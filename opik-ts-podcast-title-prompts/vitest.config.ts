import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // The Opik SDK's documented switch to turn tracking off: nothing is sent.
    env: { OPIK_TRACK_DISABLE: "true" },
  },
});
