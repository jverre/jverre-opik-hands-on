// All of the Opik wiring lives here. Nothing in agents/, tools/ or library/
// knows tracing exists.
import { Observability } from "@mastra/observability";
import { OtelExporter } from "@mastra/otel-exporter";

export const PROJECT_NAME = "mastra-library-holds-agent";

// Local Opik by default; for Opik Cloud set OPIK_URL_OVERRIDE to
// https://www.comet.com/opik/api and provide OPIK_API_KEY.
const opikBase = (process.env.OPIK_URL_OVERRIDE ?? "http://localhost:5173/api").replace(/\/+$/, "");

// Opik's OTLP route takes the workspace and target project as headers. The
// projectName header decides which Opik project the traces land in; without it
// they go to "Default Project". Authorization is only sent for Opik Cloud.
const headers: Record<string, string> = {
  "Comet-Workspace": process.env.OPIK_WORKSPACE ?? "default",
  projectName: process.env.OPIK_PROJECT_NAME ?? PROJECT_NAME,
};
if (process.env.OPIK_API_KEY) headers.Authorization = process.env.OPIK_API_KEY;

// Mastra's observability layer emits one span per agent run, model step, LLM
// call and tool execution; OtelExporter converts them to OTLP and posts them
// to Opik (as protobuf: JSON export produced nothing), which rebuilds the tree (invoke_agent > agent_step > chat / execute_tool).
export const observability = new Observability({
  configs: {
    default: {
      serviceName: PROJECT_NAME,
      exporters: [
        new OtelExporter({
          provider: {
            custom: { endpoint: `${opikBase}/v1/private/otel/v1/traces`, protocol: "http/protobuf", headers },
          },
        }),
      ],
    },
  },
});
