import { beforeEach, describe, expect, it } from "vitest";
import { freshLibrary, type LibraryState } from "../src/data/catalogue.ts";
import { accountSummary, addDays, daysOverdue, payFine, placeHold, renewLoan, searchBooks } from "../src/library/rules.ts";

let lib: LibraryState;
beforeEach(() => {
  lib = freshLibrary();
});

describe("dates", () => {
  it("adds days across month ends and counts overdue days", () => {
    expect(addDays("2026-11-28", 14)).toBe("2026-12-12");
    expect(daysOverdue("2026-11-10")).toBe(15);
    expect(daysOverdue("2026-12-01")).toBe(0);
  });
});

describe("renewals", () => {
  it("renews a clean loan by 14 days", () => {
    expect(renewLoan(lib, "P-3001", "L-501")).toMatchObject({ ok: true, new_due: "2026-12-12", renewals_used: 1 });
  });
  it("refuses when another patron has a hold", () => {
    expect(renewLoan(lib, "P-3001", "L-502")).toMatchObject({ ok: false });
  });
  it("refuses when fines are at the limit", () => {
    const r = renewLoan(lib, "P-3002", "L-601");
    expect(r.ok).toBe(false);
    expect(r.error).toMatch(/fines/);
  });
});

describe("holds and fines", () => {
  it("queues a hold on an unavailable title and refuses shelf copies", () => {
    expect(placeHold(lib, "P-3001", "B-100")).toMatchObject({ ok: true, queue_position: 1 });
    expect(placeHold(lib, "P-3001", "B-101").ok).toBe(false);
  });
  it("blocks holds for patrons over the fines limit", () => {
    expect(placeHold(lib, "P-3002", "B-100").ok).toBe(false);
  });
  it("pays down a fine but not past the balance", () => {
    expect(payFine(lib, "P-3002", 5)).toMatchObject({ ok: true, remaining_usd: 7 });
    expect(payFine(lib, "P-3002", 50).ok).toBe(false);
  });
  it("searches and summarises accounts", () => {
    expect(searchBooks(lib, "fog")).toHaveLength(1);
    expect(accountSummary(lib, "p-3001")).toMatchObject({ name: "Imogen Hale" });
    expect(accountSummary(lib, "P-0000")).toHaveProperty("error");
  });
});
