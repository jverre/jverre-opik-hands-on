import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

/** Load the nearest .env, walking up from the project folder. Real env vars win. */
export function loadNearestEnv(start = process.cwd()): void {
  let dir = resolve(start);
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
