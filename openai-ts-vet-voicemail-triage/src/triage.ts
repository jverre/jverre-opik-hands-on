import type { Urgency } from "./voicemails.js";

export const TRIAGE_MODEL = "gpt-4o-mini";

export const TRIAGE_SYSTEM_PROMPT = `\
You are the front-desk triage assistant for a veterinary clinic. You read the
transcript of one voicemail and decide how fast someone must call the owner back.
Reply with JSON only, in exactly this shape:

{
  "urgency": "emergency" | "urgent" | "routine",
  "reason": "one sentence naming the symptom or request that decided the level",
  "callback": {
    "caller": "the caller's name as spoken, or null",
    "phone": "digits only as spoken, e.g. 5550142, or null",
    "pet": "the animal's name, or null",
    "issue": "a few words: what the call is about"
  }
}

Levels:
- emergency: possible poisoning, collapse, trouble breathing, seizures, heavy bleeding,
  or pale gums. Judge by what happened, not by how calm the caller sounds.
- urgent: a pet that stopped eating or drinking, repeated vomiting, a limp, or pain
  that should be seen today.
- routine: scheduling, refills, vaccines, and questions that can wait a day.

Only use details that are in the transcript. If the name or number is missing, use null.
`;

export interface Callback {
  caller: string | null;
  phone: string | null;
  pet: string | null;
  issue: string;
}

export interface Triage {
  urgency: Urgency;
  reason: string;
  callback: Callback;
}

const LEVELS: readonly Urgency[] = ["emergency", "urgent", "routine"];
const ORDER: Record<Urgency, number> = { emergency: 0, urgent: 1, routine: 2 };

function text(value: unknown): string | null {
  return typeof value === "string" && value.trim() !== "" && value.trim().toLowerCase() !== "null"
    ? value.trim()
    : null;
}

/** Parse the model's JSON reply. Throws on anything that is not a usable triage, so a bad reply never turns into a silent "routine". */
export function parseTriage(raw: string): Triage {
  let data: unknown;
  try {
    data = JSON.parse(raw);
  } catch {
    throw new Error(`triage reply is not JSON: ${raw.slice(0, 80)}`);
  }
  const obj = (data ?? {}) as Record<string, unknown>;
  const urgency = String(obj.urgency ?? "").toLowerCase() as Urgency;
  if (!LEVELS.includes(urgency)) throw new Error(`unknown urgency level: ${String(obj.urgency)}`);
  const cb = (obj.callback ?? {}) as Record<string, unknown>;
  const phone = text(cb.phone)?.replace(/\D/g, "") || null;
  return {
    urgency,
    reason: text(obj.reason) ?? "",
    callback: { caller: text(cb.caller), phone, pet: text(cb.pet), issue: text(cb.issue) ?? "" },
  };
}

/** Format seven or ten digits as a readable phone number; leave anything else untouched. */
export function formatPhone(digits: string | null): string {
  if (!digits) return "(no number left)";
  if (digits.length === 7) return `${digits.slice(0, 3)}-${digits.slice(3)}`;
  if (digits.length === 10) return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
  return digits;
}

/** The day's callback list: emergencies first, stable within a level. */
export function buildCallbackList(items: { id: string; triage: Triage }[]): { id: string; triage: Triage }[] {
  return items
    .map((item, index) => ({ item, index }))
    .sort((a, b) => ORDER[a.item.triage.urgency] - ORDER[b.item.triage.urgency] || a.index - b.index)
    .map(({ item }) => item);
}

export function describeCallback(triage: Triage): string {
  const who = triage.callback.caller ?? "unknown caller";
  const pet = triage.callback.pet ? ` re ${triage.callback.pet}` : "";
  return `${triage.urgency.toUpperCase().padEnd(9)} ${who}${pet}, ${formatPhone(triage.callback.phone)}: ${triage.callback.issue}`;
}
