import { tool } from "ai";
import { z } from "zod";
import { describeService, findService } from "./workshop";

// A plain AI SDK tool. When the model calls it, the Opik exporter turns the
// call into a `tool` span nested under the chat trace, with args and result.
export const getServicePrice = tool({
  description: "Look up the suggested donation and duration for a workshop service.",
  inputSchema: z.object({
    service: z.string().describe("What the rider needs, e.g. 'puncture' or 'brake pads'"),
  }),
  execute: async ({ service }) => {
    const match = findService(service);
    return match ? describeService(match) : "No such service. Offer the full safety check instead.";
  },
});

export const tools = { getServicePrice };
