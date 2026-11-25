// Minimal reader for the AI SDK UI-message stream (server-sent events).

/** Returns the text-delta payload of one SSE line, or "" for anything else. */
export function textDeltaFromLine(line: string): string {
  if (!line.startsWith("data: ") || line === "data: [DONE]") return "";
  try {
    const event = JSON.parse(line.slice(6));
    return event.type === "text-delta" && typeof event.delta === "string" ? event.delta : "";
  } catch {
    return "";
  }
}

/** Reads a fetch body to the end, calling onDelta for every text chunk; returns the full text. */
export async function readReply(body: ReadableStream<Uint8Array>, onDelta: (text: string) => void): Promise<string> {
  const decoder = new TextDecoder();
  const reader = body.getReader();
  let buffer = "";
  let text = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      const delta = textDeltaFromLine(line);
      if (delta) {
        text += delta;
        onDelta(delta);
      }
    }
  }
  return text;
}
