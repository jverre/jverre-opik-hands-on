import { registerOTel } from "@vercel/otel";
import { registerTelemetry } from "ai";
import { OpenTelemetry } from "@ai-sdk/otel";
import { OpikExporter } from "opik-vercel";
import { Opik } from "opik";
import { config } from "dotenv";
import path from "path";
import { PROJECT_NAME, spanAttributes } from "./lib/telemetry";

// Secrets live in one repo-level .env; Next.js already loads this folder's
// .env. Neither file overrides variables that are already set.
config({ path: path.resolve(process.cwd(), "../.env"), quiet: true });

// OpikExporter is the OpenTelemetry exporter that rebuilds each AI SDK call
// as an Opik trace with llm and tool spans. Pinning projectName here sends
// every trace to one project; URL, workspace and key come from OPIK_* env vars.
registerOTel({
  serviceName: PROJECT_NAME,
  traceExporter: new OpikExporter({
    client: new Opik({ projectName: PROJECT_NAME }),
    tags: ["workshop", "streaming"],
  }),
});

// Registers the AI SDK v7 OpenTelemetry integration, which is what emits the spans
// the exporter above turns into Opik traces.
registerTelemetry(
  new OpenTelemetry({
    usage: true, // token counts on llm spans, which Opik turns into cost
    enrichSpan: ({ runtimeContext }) => spanAttributes(runtimeContext),
  }),
);
