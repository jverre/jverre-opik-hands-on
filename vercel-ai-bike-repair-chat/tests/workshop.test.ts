import { describe, expect, it } from "vitest";
import { describeService, findService } from "../lib/workshop";
import { getServicePrice } from "../lib/tools";
import { SYSTEM_PROMPT } from "../lib/prompt";

describe("workshop price list", () => {
  it("matches a service from rider wording", () => {
    expect(findService("my brake pads are squealing")?.id).toBe("brake-pads");
    expect(findService("I got a flat tyre")?.id).toBe("puncture");
  });

  it("returns undefined for things the workshop does not do", () => {
    expect(findService("bleed the brakes on my Honda Civic engine")?.id).not.toBe("gear-tune");
    expect(findService("xyz")).toBeUndefined();
  });

  it("formats a service with price and time", () => {
    const text = describeService(findService("chain")!);
    expect(text).toContain("GBP 6");
    expect(text).toContain("25 minutes");
  });

  it("exposes the lookup as an AI SDK tool", async () => {
    const result = await getServicePrice.execute!({ service: "gear shifting" }, { toolCallId: "t1", messages: [] } as never);
    expect(result).toContain("Gear tune-up");
  });

  it("tells the model to use the tool for prices and to stay on bicycles", () => {
    expect(SYSTEM_PROMPT).toContain("getServicePrice");
    expect(SYSTEM_PROMPT).toContain("only help with bicycles");
  });
});
