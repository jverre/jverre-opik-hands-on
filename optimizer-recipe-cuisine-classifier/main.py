"""Optimize the cuisine classifier's prompt with the Opik Agent Optimizer.

The baseline prompt (see classifier.py) names the five cuisines but never says
how to answer, so gpt-4o-mini replies in sentences and exact-match accuracy
sits near 0.3. MetaPromptOptimizer scores it on 20 labeled dishes, asks
gpt-4o-mini to propose rewrites, and keeps the best within a six-trial budget.
The score curve, the winning prompt and a held-out check all end up in Opik.
"""

from classifier import (
    BASELINE_SYSTEM,
    MODEL,
    PROJECT_NAME,
    accuracy,
    is_correct,
)
from data import HELD_OUT, TRAIN

DATASET_NAME = "recipe-cuisines-train"
LIBRARY_PROMPT_NAME = "cuisine-classifier"
MAX_TRIALS = 6  # candidate prompts the optimizer may score: the budget cap
LITELLM_MODEL = f"openai/{MODEL}"  # the optimizer talks to models through LiteLLM


def trial_scores(history: list[dict]) -> list[float]:
    """Flatten the optimizer's per-round history into one score per trial."""
    return [
        trial["score"]
        for round_state in history
        for trial in round_state.get("trials", [])
        if trial.get("score") is not None
    ]


def to_mustache(messages: list[dict]) -> list[dict]:
    """The optimizer fills {dish}; the prompt library uses {{dish}}."""
    return [
        {**m, "content": m["content"].replace("{dish}", "{{dish}}")}
        for m in messages
    ]


def cuisine_exact_match(dataset_item: dict, llm_output: str) -> float:
    """Reply must be exactly one cuisine label, such as 'sichuan', with no extra words.

    The optimizer never sees the dataset's labels or the model's answers. It
    reads only this function's name and the first line of this docstring, so
    that line is where the output format has to be spelled out.
    """
    return 1.0 if is_correct(llm_output, dataset_item["label"]) else 0.0


def main() -> None:
    import opik
    from opik_optimizer import ChatPrompt, MetaPromptOptimizer

    # Opik client: creates the dataset and prompt-library entries below.
    opik_client = opik.Opik()

    # The dataset is the ground truth the optimizer climbs against. It is stored
    # in Opik (Datasets tab), and every trial below is an experiment on it. The
    # item keys must not be called "description": the SDK drops that key on insert.
    dataset = opik_client.get_or_create_dataset(
        name=DATASET_NAME,
        description="20 invented recipe blurbs labeled with one of five cuisines",
    )
    dataset.insert([{"dish": t, "label": label} for t, label in TRAIN])

    prompt = ChatPrompt(
        name=LIBRARY_PROMPT_NAME,
        system=BASELINE_SYSTEM,
        user="{dish}",  # filled from the dataset's "dish" column
        model=LITELLM_MODEL,
    )

    # Prompt library v1 = the baseline, saved before optimizing so the library
    # tells the whole story (v1 loose, v2 optimized), under this project.
    opik_client.create_chat_prompt(
        name=LIBRARY_PROMPT_NAME,
        messages=to_mustache(prompt.get_messages()),
        change_description="Baseline hand-written prompt (pre-optimization)",
        metadata={"stage": "baseline"},
        tags=["cuisine"],
        project_name=PROJECT_NAME,
    )

    # MetaPromptOptimizer scores the baseline, then asks the model for rewrites
    # (it sees the prompt, past scores, sample dishes and the metric's name and
    # docstring, never the labels). Each trial becomes an experiment on the
    # dataset, grouped under one optimization run in Opik.
    optimizer = MetaPromptOptimizer(
        model=LITELLM_MODEL,  # the model that writes the candidate prompts
        prompts_per_round=3,
        seed=42,
        skip_perfect_score=False,  # by default the run stops at the first score >= 0.95
        verbose=1,
    )
    result = optimizer.optimize_prompt(
        prompt=prompt,
        dataset=dataset,
        metric=cuisine_exact_match,
        n_samples=len(TRAIN),  # score every dish on every trial
        max_trials=MAX_TRIALS,
        project_name=PROJECT_NAME,  # optimizer traces land in the same project
    )

    initial = result.initial_score or 0.0
    best = result.score
    winner_system = result.prompt.get_messages()[0]["content"]

    # Held-out check: dishes the optimizer never saw. Each pass is one traced
    # score_prompt call in the project, so both runs can be opened side by side.
    held_before = accuracy(HELD_OUT, BASELINE_SYSTEM)
    held_after = accuracy(HELD_OUT, winner_system)

    print()
    print("=" * 64)
    curve = [round(s, 2) for s in [initial, *trial_scores(result.history)]]
    print(f"baseline accuracy (train) : {initial:.3f}")
    print(f"best accuracy (train)     : {best:.3f}  ({best - initial:+.3f})")
    print(f"score curve (base, trials): {curve}")
    print(f"held-out accuracy         : {held_before:.3f} -> {held_after:.3f}")
    print(f"optimizer llm calls       : {result.llm_calls}")

    # result.get_run_link() is a session redirect that lands in whichever project
    # the UI last showed, so the run can look empty. Build a project-pinned link.
    info = opik_client.rest_client.optimizations.get_optimization_by_id(
        result.optimization_id
    )
    ui_base = opik_client.config.url_override.rstrip("/").removesuffix("/api")
    print(
        "optimization run          : "
        f"{ui_base}/{opik_client.config.workspace}/projects/{info.project_id}"
        f"/optimizations/{result.optimization_id}"
    )
    print("=" * 64)

    # Only a real improvement earns version 2 of the library prompt.
    if best > initial:
        opik_client.create_chat_prompt(
            name=LIBRARY_PROMPT_NAME,
            messages=to_mustache(result.prompt.get_messages()),
            change_description=(
                f"MetaPromptOptimizer winner: accuracy {initial:.3f} -> {best:.3f} "
                f"on {DATASET_NAME}; held-out {held_before:.3f} -> {held_after:.3f}"
            ),
            # Metadata and tags show up on the prompt's page in the library.
            metadata={
                "stage": "optimized",
                "train_accuracy": best,
                "held_out_accuracy": held_after,
            },
            tags=["cuisine"],
            project_name=PROJECT_NAME,
        )
        print(f"\nSaved the winner as a new version of '{LIBRARY_PROMPT_NAME}'.")
        print(f"\nWinning system prompt:\n\n{winner_system}")
    else:
        print("\nNo improvement over the baseline; the library keeps only v1.")

    opik.flush_tracker()  # send any buffered traces before the process exits


if __name__ == "__main__":
    main()
