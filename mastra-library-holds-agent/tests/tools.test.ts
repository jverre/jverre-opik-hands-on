import { beforeEach, describe, expect, it } from "vitest";
import { libraryTools } from "../src/tools/index.ts";
import { getLibrary, resetLibrary } from "../src/library/state.ts";

beforeEach(() => resetLibrary());

// Tool execute() functions run with no Mastra instance, no exporter and no model,
// so tracing configuration cannot get in the way of unit tests.
describe("tools", () => {
  it("renew_loan mutates the shared library state", async () => {
    const out: any = await libraryTools.renewLoan.execute!({ patron_id: "P-3001", loan_id: "L-501" }, {} as any);
    expect(out.ok).toBe(true);
    expect(getLibrary().loans["P-3001"][0].due).toBe("2026-12-12");
  });
  it("all five tools carry the ids the trace will show as execute_tool names", () => {
    expect(Object.values(libraryTools).map((t) => t.id).sort()).toEqual(
      ["get_account", "pay_fine", "place_hold", "renew_loan", "search_catalogue"],
    );
  });
});
