import { describe, expect, it } from "vitest";
import { buildCallbackList, describeCallback, formatPhone, parseTriage } from "../src/triage.js";

const reply = (over: Record<string, unknown> = {}) =>
  JSON.stringify({
    urgency: "Emergency",
    reason: "Ate chocolate and is shaking.",
    callback: { caller: "Marisol Okafor", phone: "555-0142", pet: "Biscuit", issue: "chocolate" },
    ...over,
  });

describe("parseTriage", () => {
  it("normalises level and keeps phone digits only", () => {
    const t = parseTriage(reply());
    expect(t.urgency).toBe("emergency");
    expect(t.callback.phone).toBe("5550142");
  });

  it("turns missing or 'null' fields into null instead of the string", () => {
    const t = parseTriage(reply({ callback: { caller: "null", phone: "", pet: null, issue: "refill" } }));
    expect(t.callback).toEqual({ caller: null, phone: null, pet: null, issue: "refill" });
  });

  it("rejects an unknown level rather than defaulting to routine", () => {
    expect(() => parseTriage(reply({ urgency: "whenever" }))).toThrow(/unknown urgency/);
    expect(() => parseTriage("not json")).toThrow(/not JSON/);
  });
});

describe("callback list", () => {
  it("puts emergencies first and keeps arrival order within a level", () => {
    const mk = (id: string, urgency: string) => ({ id, triage: parseTriage(reply({ urgency })) });
    const ordered = buildCallbackList([mk("a", "routine"), mk("b", "urgent"), mk("c", "emergency"), mk("d", "urgent")]);
    expect(ordered.map((i) => i.id)).toEqual(["c", "b", "d", "a"]);
  });

  it("formats phones and lines", () => {
    expect(formatPhone("5550142")).toBe("555-0142");
    expect(formatPhone(null)).toBe("(no number left)");
    expect(describeCallback(parseTriage(reply()))).toContain("EMERGENCY Marisol Okafor re Biscuit, 555-0142");
  });
});
