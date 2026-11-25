import { HOUSEKEEPING_ITEMS, SPA_SLOTS } from "./hotel.js";

// Tool schemas the model sees (OpenAI function-calling format).
export const TOOL_DEFINITIONS = [
  {
    type: "function" as const,
    function: {
      name: "check_spa_slots",
      description: "List spa treatment slots for 'today' or 'tomorrow'.",
      parameters: {
        type: "object",
        properties: { day: { type: "string", enum: ["today", "tomorrow"] } },
        required: ["day"],
      },
    },
  },
  {
    type: "function" as const,
    function: {
      name: "log_housekeeping_request",
      description: "Log a housekeeping request for the guest's room.",
      parameters: {
        type: "object",
        properties: {
          room: { type: "string", description: "Room number, e.g. 412" },
          item: { type: "string", enum: [...HOUSEKEEPING_ITEMS] },
          quantity: { type: "integer", minimum: 1, maximum: 6 },
        },
        required: ["room", "item"],
      },
    },
  },
];

export function checkSpaSlots(day: string): string {
  const slots = SPA_SLOTS[day];
  if (!slots) return JSON.stringify({ error: `unknown day '${day}'` });
  return JSON.stringify(slots.filter((s) => s.available));
}

let ticket = 100;
export function logHousekeepingRequest(room: string, item: string, quantity = 1): string {
  if (!(HOUSEKEEPING_ITEMS as readonly string[]).includes(item)) {
    return JSON.stringify({ error: `cannot arrange '${item}'` });
  }
  ticket += 1;
  return JSON.stringify({ ticket: `HK-${ticket}`, room, item, quantity, status: "queued" });
}

/** Run one tool call by name. Arguments arrive as the model's raw JSON string. */
export function executeTool(name: string, rawArgs: string): string {
  let args: Record<string, unknown>;
  try {
    args = JSON.parse(rawArgs || "{}") as Record<string, unknown>;
  } catch {
    return JSON.stringify({ error: "invalid JSON arguments" });
  }
  if (name === "check_spa_slots") return checkSpaSlots(String(args.day ?? ""));
  if (name === "log_housekeeping_request") {
    return logHousekeepingRequest(
      String(args.room ?? ""),
      String(args.item ?? ""),
      typeof args.quantity === "number" ? args.quantity : 1,
    );
  }
  return JSON.stringify({ error: `unknown tool '${name}'` });
}
