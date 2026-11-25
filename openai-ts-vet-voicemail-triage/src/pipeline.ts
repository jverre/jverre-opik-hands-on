import { createReadStream } from "node:fs";
import { mkdir, stat, writeFile } from "node:fs/promises";
import { dirname } from "node:path";
import type OpenAI from "openai";
import { getTrackContext, track, type Span } from "opik";
import { TRIAGE_MODEL, TRIAGE_SYSTEM_PROMPT, parseTriage, type Triage } from "./triage.js";
import type { Voicemail } from "./voicemails.js";

export const TTS_MODEL = "tts-1";
export const TRANSCRIBE_MODEL = "gpt-4o-mini-transcribe";

/** The slice of the OpenAI client the pipeline uses, so tests can stub it. */
export interface VoicemailClient {
  audio: {
    speech: { create: (body: { model: string; voice: string; input: string; response_format: "mp3" }) => Promise<{ arrayBuffer(): Promise<ArrayBuffer> }> };
    transcriptions: { create: (body: { model: string; file: ReturnType<typeof createReadStream>; response_format: "text" }) => Promise<unknown> };
  };
  chat: { completions: { create: OpenAI["chat"]["completions"]["create"] } };
}

export interface VoicemailResult {
  id: string;
  audioPath: string;
  transcript: string;
  triage: Triage;
  /** Opik trace id of this run, so the caller can attach the audio once the trace is flushed. */
  traceId: string | undefined;
}

/** Hook that returns the chat client to use inside the "triage" span; the demo passes one that logs an llm span. */
export type ChatWrapper = (client: VoicemailClient, parent: Span | undefined) => VoicemailClient;

/**
 * Build the pipeline steps around one client. `wrapChat` decides how the chat call is traced:
 * the default runs it untraced (tests, stubs); the demo passes a trackOpenAI wrapper.
 */
export function createPipeline(client: VoicemailClient, audioDir: string, wrapChat: ChatWrapper = (c) => c) {
  // track() wraps a function in a span: arguments become the span input, the return value its
  // output, and nesting follows the call stack. type "tool" marks steps that are not a chat call.
  const synthesize = track(
    {
      name: "text-to-speech",
      type: "tool",
      enrichSpan: () => ({ metadata: { model: TTS_MODEL, provider: "openai" } }),
    },
    async (voicemail: Voicemail, audioPath: string): Promise<{ audioPath: string; bytes: number }> => {
      const speech = await client.audio.speech.create({
        model: TTS_MODEL,
        voice: voicemail.voice,
        input: voicemail.script,
        response_format: "mp3",
      });
      const audio = Buffer.from(await speech.arrayBuffer());
      await mkdir(dirname(audioPath), { recursive: true });
      await writeFile(audioPath, audio);
      return { audioPath, bytes: audio.length };
    },
  ) as (voicemail: Voicemail, audioPath: string) => Promise<{ audioPath: string; bytes: number }>;

  // The transcript is this span's output: what the pipeline believes the caller said.
  const transcribe = track(
    {
      name: "speech-to-text",
      type: "tool",
      enrichSpan: () => ({ metadata: { model: TRANSCRIBE_MODEL, provider: "openai" } }),
    },
    async (audioPath: string): Promise<string> => {
      const result = await client.audio.transcriptions.create({
        model: TRANSCRIBE_MODEL,
        file: createReadStream(audioPath),
        response_format: "text",
      });
      return String(result).trim();
    },
  ) as (audioPath: string) => Promise<string>;

  // The "triage" span is the parent handed to the chat wrapper, so the llm span with model,
  // token usage and cost nests here instead of becoming a separate trace.
  const triage = track({ name: "triage", type: "general" }, async (transcript: string): Promise<Triage> => {
    const chat = wrapChat(client, getTrackContext()?.span);
    const response = await chat.chat.completions.create({
      model: TRIAGE_MODEL,
      messages: [
        { role: "system", content: TRIAGE_SYSTEM_PROMPT },
        { role: "user", content: transcript },
      ],
      response_format: { type: "json_object" },
    });
    return parseTriage(response.choices[0]?.message?.content ?? "");
  }) as (transcript: string) => Promise<Triage>;

  // Root span: one voicemail = one trace, with synthesize, transcribe and triage nested below it.
  const processVoicemail = track(
    { name: "triage-voicemail", type: "general" },
    async (voicemail: Voicemail): Promise<VoicemailResult> => {
      // getTrackContext() hands back the trace this call created; its id is how the audio file
      // gets linked to the trace afterwards.
      const traceId = getTrackContext()?.trace.data.id;
      const audioPath = `${audioDir}/${voicemail.id}.mp3`;
      if (!(await exists(audioPath))) await synthesize(voicemail, audioPath);
      const transcript = await transcribe(audioPath);
      return { id: voicemail.id, audioPath, transcript, triage: await triage(transcript), traceId };
    },
  ) as (voicemail: Voicemail) => Promise<VoicemailResult>;

  return { synthesize, transcribe, triage, processVoicemail };
}

async function exists(path: string): Promise<boolean> {
  try {
    await stat(path);
    return true;
  } catch {
    return false;
  }
}
