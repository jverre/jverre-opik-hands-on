// Next.js calls register() once at server start. The OpenTelemetry setup needs
// Node APIs, so it only loads in the Node.js runtime, not the Edge one.
export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    await import("./instrumentation.node");
  }
}
