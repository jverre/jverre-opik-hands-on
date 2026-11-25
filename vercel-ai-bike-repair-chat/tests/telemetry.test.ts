import { describe, expect, it } from "vitest";
import { runtimeContextFor, spanAttributes, telemetrySettings, trackingDisabled, TRACE_NAME } from "../lib/telemetry";

describe("telemetry helpers", () => {
  it("maps runtimeContext to the span attributes opik-vercel reads", () => {
    expect(spanAttributes(runtimeContextFor("chat-1"))).toEqual({
      "ai.telemetry.metadata.threadId": "chat-1",
      "ai.telemetry.metadata.traceName": TRACE_NAME,
    });
    expect(spanAttributes(undefined)).toEqual({});
  });

  it("emits spans by default and honours OPIK_TRACK_DISABLE=true", () => {
    expect(telemetrySettings({}).isEnabled).toBe(true);
    expect(trackingDisabled({ OPIK_TRACK_DISABLE: "true" })).toBe(true);
    expect(telemetrySettings({ OPIK_TRACK_DISABLE: "true" }).isEnabled).toBe(false);
  });

  it("lets runtimeContext keys through to the spans", () => {
    expect(telemetrySettings({}).includeRuntimeContext).toEqual({ threadId: true, traceName: true });
  });
});
