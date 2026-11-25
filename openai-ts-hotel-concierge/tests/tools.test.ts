import { describe, expect, it } from "vitest";
import { executeTool } from "../src/tools.js";

describe("tools", () => {
  it("lists only available spa slots", () => {
    const slots = JSON.parse(executeTool("check_spa_slots", '{"day":"today"}')) as { time: string }[];
    expect(slots.map((s) => s.time)).toEqual(["15:30", "17:00"]);
  });

  it("logs a housekeeping ticket and rejects unknown items", () => {
    const ok = JSON.parse(executeTool("log_housekeeping_request", '{"room":"208","item":"towels","quantity":2}'));
    expect(ok).toMatchObject({ room: "208", item: "towels", quantity: 2, status: "queued" });
    expect(ok.ticket).toMatch(/^HK-\d+$/);
    expect(JSON.parse(executeTool("log_housekeeping_request", '{"room":"208","item":"flight"}'))).toHaveProperty("error");
  });

  it("survives bad arguments and unknown tools", () => {
    expect(JSON.parse(executeTool("check_spa_slots", "not json"))).toHaveProperty("error");
    expect(JSON.parse(executeTool("book_flight", "{}"))).toHaveProperty("error");
  });
});
