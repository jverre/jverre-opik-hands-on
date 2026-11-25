"""Score the raw and the compiled claim checker on the same held-out claims."""

import opik

import factcheck


def score(program) -> int:
    hits = 0
    for row in factcheck.load_testset():
        out = program(facts=factcheck.FACT_SHEET, claim=row["claim"]).verdict
        expected = (row["label"], row["cites"])
        hits += factcheck.parse_verdict(out) == expected
        print(f"  {row['claim'][:50]:<50} -> {out[:60]!r}")
    return hits


def main() -> None:
    factcheck.configure_lm()
    raw = factcheck.build_program()
    total = len(factcheck.load_testset())
    print("Uncompiled program:")
    before = score(raw)
    print("\nCompiling with BootstrapFewShot...")
    compiled = factcheck.compile_program(raw)
    print("Compiled program:")
    after = score(compiled)
    # Traces are sent from a background thread; flush so none are lost on exit.
    opik.flush_tracker()
    print(f"\nuncompiled {before}/{total}   compiled {after}/{total}")


if __name__ == "__main__":
    main()
