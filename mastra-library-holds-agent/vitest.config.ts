import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // Tests never need Opik or a model. The exporter in src/observability.ts is only
    // built when src/mastra.ts is imported, which the tests avoid.
    env: { OPENAI_API_KEY: "", OPIK_URL_OVERRIDE: "http://127.0.0.1:9/api" },
  },
});
