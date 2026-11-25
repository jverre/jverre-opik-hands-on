/**
 * Moss & Meeple rules helper: the Express backend behind the tablet widget.
 * POST /chat { message, sessionId } -> { reply }.
 *
 * Every turn runs one LangChain.js chain invocation; the OpikCallbackHandler
 * turns it into a trace in the "langchainjs-board-game-rules-chat" Opik
 * project, and the table's sessionId becomes the Opik thread id.
 */
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Server } from "node:http";

import dotenv from "dotenv";
import express from "express";
import { ChatOpenAI } from "@langchain/openai";
import type { BaseLanguageModel } from "@langchain/core/language_models/base";
import { Opik } from "opik";
import { OpikCallbackHandler } from "opik-langchain";

import { buildChain, buildObjectRootChain, remember } from "./chat.js";
import type { Session } from "./chat.js";
import { loadCorpus } from "./rules.js";

const here = path.dirname(fileURLToPath(import.meta.url));

// Load the example's .env, then the repo-root .env (existing values win).
dotenv.config({ path: path.join(here, "../.env"), quiet: true });
dotenv.config({ path: path.join(here, "../../.env"), quiet: true });

export const PROJECT_NAME = "langchainjs-board-game-rules-chat";

// One shared Opik client: every session's handler batches through it, and
// flushing it is what guarantees the last turns reach Opik before exit.
const opikClient = new Opik({ projectName: PROJECT_NAME });

interface TableSession extends Session {
  // threadId = sessionId makes Opik group this table's traces into one thread.
  opikHandler: OpikCallbackHandler;
}

const corpus = loadCorpus(path.join(here, "../data/rules"));
const sessions = new Map<string, TableSession>();

function getSession(sessionId: string): TableSession {
  let session = sessions.get(sessionId);
  if (!session) {
    session = {
      history: [],
      // The callback handler maps each chain step to a span (chain, prompt,
      // llm with token usage and cost, parser); without threadId each turn
      // would be an unrelated trace.
      opikHandler: new OpikCallbackHandler({ client: opikClient, threadId: sessionId }),
    };
    sessions.set(sessionId, session);
  }
  return session;
}

export function createApp(llm: BaseLanguageModel) {
  const deps = { llm, corpus, sessions };
  const chain = buildChain(deps);
  const objectChain = buildObjectRootChain(deps);
  const app = express();
  app.use(express.json());
  app.use(express.static(path.join(here, "../public")));

  app.post("/chat", async (req, res) => {
    const { message, sessionId, rootShape } = req.body ?? {};
    if (typeof message !== "string" || !message.trim() || typeof sessionId !== "string" || !sessionId) {
      res.status(400).json({ error: "Body must be { message: string, sessionId: string }" });
      return;
    }
    try {
      const session = getSession(sessionId);
      // runName becomes the root span's name, so each turn shows up in the
      // trace list as "rules-helper-turn".
      const config = {
        callbacks: [session.opikHandler],
        runName: "rules-helper-turn",
        configurable: { sessionId },
      };
      const reply =
        rootShape === "object"
          ? (await objectChain.invoke({ question: message }, config)).answer
          : await chain.invoke(message, config);
      remember(session, message, reply);
      res.json({ reply, sessionId });
    } catch (error) {
      console.error("Chat turn failed:", error);
      res.status(500).json({ error: "The rules helper could not answer. Try again." });
    }
  });
  return app;
}

export function defaultModel(): BaseLanguageModel {
  return new ChatOpenAI({ model: "gpt-4o-mini", temperature: 0 });
}

/** Send buffered traces to Opik. Called by the demo and on Ctrl+C. */
export async function flushOpik(): Promise<void> {
  await opikClient.flush();
}

export function startServer(port: number): Promise<Server> {
  const app = createApp(defaultModel());
  return new Promise((resolve) => {
    const server = app.listen(port, () => resolve(server));
  });
}

const isMain =
  process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);

if (isMain) {
  const port = Number(process.env.PORT ?? 4170);
  startServer(port).then(() => {
    console.log(`Rules helper widget: http://localhost:${port}`);
    console.log(`Traces land in the "${PROJECT_NAME}" Opik project.`);
  });
  for (const signal of ["SIGINT", "SIGTERM"] as const) {
    process.on(signal, async () => {
      await flushOpik(); // otherwise the last buffered turns are lost on exit
      process.exit(0);
    });
  }
}
