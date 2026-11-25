import { parseChatRequest, streamRepairReply } from "../../../lib/chat";

export const maxDuration = 30;

// Thin on purpose: parse, delegate to lib/chat.ts, stream back.
export async function POST(req: Request) {
  let request;
  try {
    request = parseChatRequest(await req.json());
  } catch (error) {
    return Response.json({ error: (error as Error).message }, { status: 400 });
  }
  const result = await streamRepairReply(request);
  return result.toUIMessageStreamResponse();
}
