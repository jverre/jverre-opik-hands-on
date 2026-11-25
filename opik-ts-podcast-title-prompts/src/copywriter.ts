import OpenAI from "openai";
import type { Episode } from "./episodes.js";
import { MODEL, formatEpisode } from "./prompts.js";

export interface EpisodeCopy {
  title: string;
  blurb: string;
}

/** The slice of the OpenAI client the copywriter needs (easy to stub in tests). */
export interface ChatClient {
  chat: { completions: { create: OpenAI["chat"]["completions"]["create"] } };
}

/** Parse the "Title: ... / Blurb: ..." reply. Throws if either line is missing. */
export function parseCopy(raw: string): EpisodeCopy {
  const title = /^\s*Title:\s*(.+)$/im.exec(raw)?.[1]?.trim();
  const blurb = /^\s*Blurb:\s*([\s\S]+)$/im.exec(raw)?.[1]?.trim();
  if (!title || !blurb) throw new Error(`Reply is missing a Title or Blurb line: ${JSON.stringify(raw)}`);
  return { title, blurb };
}

/** Write the title and blurb for one episode with the given system prompt. */
export async function writeEpisodeCopy(
  client: ChatClient,
  systemPrompt: string,
  episode: Episode,
): Promise<EpisodeCopy> {
  const response = await client.chat.completions.create({
    model: MODEL,
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: formatEpisode(episode) },
    ],
  });
  return parseCopy(response.choices[0]?.message.content ?? "");
}
