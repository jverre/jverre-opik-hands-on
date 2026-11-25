"""An Opik dataset of visitor questions and an experiment that scores the graph."""

from typing import Any

import opik
from opik.evaluation import evaluate
from opik.evaluation.metrics import ContextPrecision, Hallucination

DATASET_NAME = "museum-guide-questions"
JUDGE_MODEL = "gpt-4o-mini"

# Several questions need two sections at once (hours + step-free access, free entry
# + carers, ...). That is what makes the number of retrieved chunks matter.
DATASET_ITEMS = [
    {"question": "When does the Orrery Room close, and can I get there without stairs?",
     "expected_output": "It closes at 17:00, thirty minutes before the rest of the museum, "
                        "and the East Wing lift reaches it, so no stairs are needed."},
    {"question": "Can wheelchair users see the Lantern Cellar, and is there an alternative?",
     "expected_output": "No: the cellar is reached only by a spiral stair with no lift. A "
                        "filmed tour plays on a screen in the Tidal Hall."},
    {"question": "Which days is entry free, and does a carer have to pay?",
     "expected_output": "Entry is free for everyone on the first Sunday of each month, and "
                        "registered carers accompanying a visitor with a disability always "
                        "enter free."},
    {"question": "What time is the Whitby Orrery wound, and which room is it in?",
     "expected_output": "It is wound by hand every morning at 10:15 in the Orrery Room."},
    {"question": "How much is an adult ticket bought online, and do under-12s pay?",
     "expected_output": "13 pounds online (14 at the desk); children under 12 are free with "
                        "a paying adult."},
    {"question": "When is the quiet morning, and what sensory equipment can I borrow?",
     "expected_output": "The second Saturday of each month from 10:00 to 12:00; ear defenders "
                        "and sensory backpacks can be borrowed from the cloakroom."},
    {"question": "Is there a watchmaker I can talk to, and on which days?",
     "expected_output": "Yes, a watchmaker is on duty at the Chronometer Gallery workbench "
                        "from Wednesday to Saturday."},
    {"question": "Until what time is hot food served, and may I bring a picnic?",
     "expected_output": "Hot food is served until 15:30. Picnics are not allowed in the "
                        "galleries but may be eaten in the courtyard."},
    {"question": "Is there a planetarium show at the museum?",
     "expected_output": "The guide does not mention a planetarium, so the assistant should "
                        "say it doesn't know."},
]


def make_task(app: Any):
    """Wrap the graph as an evaluate() task returning what the judges need."""

    def task(item: dict) -> dict:
        result = app.invoke({"question": item["question"]})
        return {"output": result["answer"], "context": result["context"]}

    return task


def run_experiment(app: Any, experiment_name: str, k: int):
    """Score the graph on the dataset and return the Opik evaluation result."""
    # get_or_create + insert: the dataset appears once in Opik and re-runs add no duplicates.
    dataset = opik.Opik().get_or_create_dataset(name=DATASET_NAME)
    dataset.insert(DATASET_ITEMS)

    # evaluate() runs the task per item and logs an experiment linked to the dataset.
    # Hallucination: is the answer supported by the retrieved context (0 grounded,
    # 1 hallucinated)? ContextPrecision: was the retrieved context the right context
    # for the question and reference answer (1 precise)? Both are LLM judges.
    return evaluate(
        dataset=dataset,
        task=make_task(app),
        scoring_metrics=[
            Hallucination(model=JUDGE_MODEL),
            ContextPrecision(model=JUDGE_MODEL),
        ],
        # The dataset calls it "question"; the metrics expect "input".
        scoring_key_mapping={"input": "question"},
        experiment_name=experiment_name,
        # experiment_config shows up as columns in the experiments table, so runs
        # that differ only in k can be told apart and compared.
        experiment_config={"k": k, "model": "gpt-4o-mini", "judge": JUDGE_MODEL},
        task_threads=4,
    )


def summarize(evaluation) -> dict[str, float]:
    """Mean of each judge score over the dataset."""
    stats = evaluation.aggregate_evaluation_scores().aggregated_scores
    return {name: s.mean for name, s in stats.items()}
