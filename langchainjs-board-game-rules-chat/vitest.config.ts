import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["tests/**/*.test.ts"],
    // The Opik SDK's documented switch to turn tracking off: nothing is sent.
    env: { OPIK_TRACK_DISABLE: "true" },
  },
});
