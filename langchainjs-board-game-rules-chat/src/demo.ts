/**
 * Autonomous demo: start the server, play scripted table conversations
 * against POST /chat, print the answers, shut down.
 */
import { startServer } from "./server.js";

const PORT = Number(process.env.PORT ?? 4171);

const CONVERSATIONS: Record<string, string[]> = {
  "table-4-lantern-heist": [
    "How many actions do I get on my turn in Lantern Heist?",
    "Can I grab two lanterns in one turn?",
    "What happens if the Watchman catches me?",
  ],
  "table-9-tidewalkers": [
    "We're playing Tidewalkers. What does Brace do?",
    "And what happens to someone standing on a flooded space?",
    "Can we play it with a dragon expansion?",
  ],
};

async function chat(sessionId: string, message: string): Promise<string> {
  const response = await fetch(`http://localhost:${PORT}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sessionId, message }),
  });
  if (!response.ok) throw new Error(`POST /chat failed: ${response.status} ${await response.text()}`);
  return ((await response.json()) as { reply: string }).reply;
}

async function main() {
  const server = await startServer(PORT);
  for (const [sessionId, turns] of Object.entries(CONVERSATIONS)) {
    console.log(`\n=== ${sessionId} ===`);
    for (const message of turns) {
      console.log(`\nGuest:  ${message}`);
      console.log(`Helper: ${await chat(sessionId, message)}`);
    }
  }
  server.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
