// Scripted patron-desk requests. `npm run demo` needs no input.
import { config } from "dotenv";
import { fileURLToPath } from "node:url";

// Load this folder's .env first, then fall back to the repo-root .env.
config({
  path: [fileURLToPath(new URL("../.env", import.meta.url)), fileURLToPath(new URL("../../.env", import.meta.url))],
  quiet: true,
});

if (!process.env.OPENAI_API_KEY) {
  console.error("Missing OPENAI_API_KEY. Copy .env.example to .env and fill it in.");
  process.exit(1);
}

// Import Mastra only after the env vars are loaded: the Opik exporter reads them at import time.
const { mastra } = await import("./mastra.ts");
const { resetLibrary } = await import("./library/state.ts");

const REQUESTS = [
  // 1. Happy path: get_account, then renew_loan succeeds.
  "Hi, I'm card P-3001. Can you renew my loan L-501 for me?",
  // 2. A refusal the agent must explain: the book has a hold queue.
  "I'm P-3001. Please also renew my loan L-502.",
  // 3. A long chain: search, place a hold, check the account.
  "Card P-3001 again. Do you have 'The Salt Road'? If there are no copies on the shelf, put me on its waiting list, then tell me where I stand on my account.",
  // 4. Blocked by fines: the agent should explain and offer to take payment.
  "This is P-3002. I want to renew L-601 please.",
];

resetLibrary();
const agent = mastra.getAgent("patronAgent");

for (const [i, request] of REQUESTS.entries()) {
  console.log(`\n=== Request ${i + 1} ===`);
  console.log(`Patron: ${request}`);
  const result = await agent.generate(request, { maxSteps: 8 });
  console.log(`Agent:  ${result.text}`);
}

// shutdown() flushes the OTel exporter; without it the last spans may never reach Opik.
await mastra.shutdown();
console.log('\nDone. Open the "mastra-library-holds-agent" project in Opik.');
