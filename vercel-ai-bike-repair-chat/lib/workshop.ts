// Fictional data for the Cobblestone Cycle Co-op, a volunteer-run community
// bike workshop. Everything here is invented for the example.

export interface Service {
  id: string;
  name: string;
  keywords: string[];
  labourGbp: number; // suggested donation for labour, parts extra
  minutes: number;
  note: string;
}

export const SERVICES: Service[] = [
  { id: "puncture", name: "Puncture repair", keywords: ["puncture", "flat", "tube", "tyre", "tire"], labourGbp: 4, minutes: 20, note: "New inner tube is GBP 6 on top." },
  { id: "brake-pads", name: "Brake pad swap", keywords: ["brake", "pads", "squeal", "rubbing"], labourGbp: 8, minutes: 30, note: "Pads from GBP 7 a pair; rim and disc pads in stock." },
  { id: "gear-tune", name: "Gear tune-up", keywords: ["gear", "shifting", "derailleur", "indexing", "skipping"], labourGbp: 10, minutes: 40, note: "Includes cable tension and limit screws." },
  { id: "chain", name: "Chain replacement", keywords: ["chain", "drivetrain", "squeak", "creak", "lube"], labourGbp: 6, minutes: 25, note: "Chains from GBP 14. We check cassette wear for free." },
  { id: "safety-check", name: "Full safety check", keywords: ["check", "service", "safety", "mot"], labourGbp: 15, minutes: 60, note: "Brakes, tyres, headset, wheels, bolts, report card." },
];

export const OPENING_HOURS =
  "Tuesday and Thursday 17:00-20:00, Saturday 10:00-15:00. Walk-ins only, no bookings.";

/** Case-insensitive keyword match; returns the best-scoring service or undefined. */
export function findService(query: string): Service | undefined {
  const words = query.toLowerCase().split(/[^a-z]+/).filter(Boolean);
  let best: { service: Service; score: number } | undefined;
  for (const service of SERVICES) {
    const matches = (k: string, w: string) => w.length >= 4 && (w.startsWith(k) || k.startsWith(w));
    const score = service.keywords.filter((k) => words.some((w) => matches(k, w))).length;
    if (score > 0 && (!best || score > best.score)) best = { service, score };
  }
  return best?.service;
}

export function describeService(service: Service): string {
  return `${service.name}: suggested labour donation GBP ${service.labourGbp}, about ${service.minutes} minutes. ${service.note}`;
}
