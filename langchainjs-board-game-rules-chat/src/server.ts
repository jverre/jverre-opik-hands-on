/**
 * Moss & Meeple rules helper: the Express backend behind the tablet widget.
 * POST /chat { message, sessionId } -> { reply }.
 */
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Server } from "node:http";

import dotenv from "dotenv";
import express from "express";
import { ChatOpenAI } from "@langchain/openai";
import type { BaseLanguageModel } from "@langchain/core/language_models/base";

import { buildChain, remember } from "./chat.js";
import type { Session } from "./chat.js";
import { loadCorpus } from "./rules.js";

const here = path.dirname(fileURLToPath(import.meta.url));

// Load the example's .env, then the repo-root .env (existing values win).
dotenv.config({ path: path.join(here, "../.env"), quiet: true });
dotenv.config({ path: path.join(here, "../../.env"), quiet: true });

export const PROJECT_NAME = "langchainjs-board-game-rules-chat";

const corpus = loadCorpus(path.join(here, "../data/rules"));
const sessions = new Map<string, Session>();

export function createApp(llm: BaseLanguageModel) {
  const chain = buildChain({ llm, corpus, sessions });
  const app = express();
  app.use(express.json());
  app.use(express.static(path.join(here, "../public")));

  app.post("/chat", async (req, res) => {
    const { message, sessionId } = req.body ?? {};
    if (typeof message !== "string" || !message.trim() || typeof sessionId !== "string" || !sessionId) {
      res.status(400).json({ error: "Body must be { message: string, sessionId: string }" });
      return;
    }
    try {
      let session = sessions.get(sessionId);
      if (!session) {
        session = { history: [] };
        sessions.set(sessionId, session);
      }
      const reply = await chain.invoke(message, {
        runName: "rules-helper-turn",
        configurable: { sessionId },
      });
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
  });
}
