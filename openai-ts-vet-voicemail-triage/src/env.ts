import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

/** Load the nearest .env, walking up from this folder (so a repo-root .env works too). */
export function loadNearestEnv(): void {
  let dir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
  for (;;) {
    const candidate = join(dir, ".env");
    if (existsSync(candidate)) {
      process.loadEnvFile(candidate);
      return;
    }
    const parent = dirname(dir);
    if (parent === dir) return;
    dir = parent;
  }
}
