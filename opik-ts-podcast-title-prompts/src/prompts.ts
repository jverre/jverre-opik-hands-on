import type { Episode } from "./episodes.js";

export const MODEL = "gpt-4o-mini";
export const PROMPT_NAME = "episode-title-blurb";

/** v1: what most teams start with. A tone, no rules. */
export const PROMPT_V1 = `You write titles and blurbs for episodes of podcasts on the Marrow & Moss Audio network.
Given the notes for an episode, write an engaging title and a short blurb that makes people want to press play.
Reply in exactly this format:
Title: <the title>
Blurb: <the blurb>`;

/** v2: the same job with the network's house style spelled out as hard rules. */
export const PROMPT_V2 = `You write titles and blurbs for episodes of podcasts on the Marrow & Moss Audio network.
Given the notes for an episode, follow these house rules exactly:

- The title is 8 words or fewer.
- The title contains no colon, question mark or exclamation mark.
- The blurb is exactly one sentence and names the guest.
- Never use clickbait words: journey, unlock, unveil, dive, secrets, ultimate, "you won't believe".

Reply in exactly this format:
Title: <the title>
Blurb: <the blurb>`;

/** The user message: the facts the model has to work from. */
export function formatEpisode(episode: Episode): string {
  return `Show: ${episode.show}\nGuest: ${episode.guest}\nNotes: ${episode.notes}`;
}
