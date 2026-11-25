"""Run one Opik test suite against the raw and the compiled claim checker."""

import opik

import factcheck

# Plain-language quality bar; an LLM judge checks every assertion per item.
# The judge only sees the claim and the answer, never the fact sheet, so the
# per-item assertion below spells out the label and fact id it should find.
GLOBAL_ASSERTIONS = [
    "The answer has exactly the form '<LABEL> | cites: <FACT-ID>' where LABEL "
    "is SUPPORTED, REFUTED or NOT ENOUGH INFO and FACT-ID looks like F03, "
    "or the word none",
    "The answer contains nothing besides the label and the cites tag: no "
    "explanation, no extra sentences",
]


def item_assertion(row: dict) -> str:
    return f'The answer\'s label is {row["label"]} and it cites {row["cites"]}'


def run_suite(suite, program, name: str, compiled: bool):
    # run_tests runs the task over every suite item, has a judge score the
    # assertions, and records the whole thing as an experiment named `name`.
    return opik.run_tests(
        test_suite=suite,
        task=factcheck.make_task(program),
        experiment_name=name,
        experiment_config={"program": "ChainOfThought(CheckClaim)",
                           "compiled": compiled, "model": factcheck.MODEL},
        worker_threads=4,
        generate_report=False,
    )


def main() -> None:
    factcheck.configure_lm()
    client = opik.Opik()

    # The suite is the fixed yardstick. get_or_create + insert dedup means
    # re-runs reuse the same suite instead of piling up copies.
    suite = client.get_or_create_test_suite(
        name="astronomy-claims",
        project_name=factcheck.PROJECT_NAME,
        global_assertions=GLOBAL_ASSERTIONS,
    )
    suite.insert([
        {"data": {"claim": row["claim"], "why": row["why"]},
         "assertions": [item_assertion(row)]}
        for row in factcheck.load_testset()
    ])

    raw = factcheck.build_program()
    print("Suite run on the uncompiled program...")
    before = run_suite(suite, raw, "uncompiled", compiled=False)

    print("\nCompiling with BootstrapFewShot...")
    compiled = factcheck.compile_program(raw)

    print("\nSuite run on the compiled program...")
    after = run_suite(suite, compiled, "compiled", compiled=True)

    # Traces and experiment items upload in the background; flush before exit.
    opik.flush_tracker()
    client.flush()

    print("\n=== Same suite, two programs ===")
    for name, result in (("uncompiled", before), ("compiled  ", after)):
        print(f"{name}: {result.pass_rate:.0%} pass "
              f"({result.items_passed}/{result.items_total} items)")
    if after.experiment_url:
        print(f"\nCompare the runs: {after.experiment_url}")


if __name__ == "__main__":
    main()
