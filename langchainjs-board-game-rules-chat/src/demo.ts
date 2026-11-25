/**
 * Autonomous demo: start the server, play scripted table conversations
 * against POST /chat, print the answers, shut down.
 */
import { flushOpik, startServer } from "./server.js";

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

// A third table goes through the object-shaped root chain, so the Threads
// view can show the same kind of conversation rendered as JSON.
const OBJECT_ROOT_SESSION = "table-12-object-root";
const OBJECT_ROOT_TURNS = [
  "How many actions do I get on my turn in Lantern Heist?",
  "Can I grab two lanterns in one turn?",
];

async function chat(sessionId: string, message: string, rootShape?: "object"): Promise<string> {
  const response = await fetch(`http://localhost:${PORT}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sessionId, message, rootShape }),
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
  console.log(`\n=== ${OBJECT_ROOT_SESSION} (object-shaped root) ===`);
  for (const message of OBJECT_ROOT_TURNS) {
    console.log(`\nGuest:  ${message}`);
    console.log(`Helper: ${await chat(OBJECT_ROOT_SESSION, message, "object")}`);
  }
  await flushOpik(); // sends the buffered traces; without it the demo can exit before they upload
  server.close();
  console.log('\nDone. Open the "langchainjs-board-game-rules-chat" project in Opik, Threads tab.');
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
