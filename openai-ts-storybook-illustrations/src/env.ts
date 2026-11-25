import path from "node:path";
import process from "node:process";

// Load .env files without a dependency: this folder's .env first, then the
// parent folder's. Variables already in the environment win.
export function loadEnv(): void {
  // Some shells export a proxy base URL; this example talks to the public API.
  delete process.env.OPENAI_BASE_URL;
  for (const file of [".env", "../.env"]) {
    try {
      process.loadEnvFile(path.resolve(file));
    } catch {
      // not there: keys may come from the environment
    }
  }
}
