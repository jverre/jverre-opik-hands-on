import path from "node:path";
import { fileURLToPath } from "node:url";
import { FakeListChatModel } from "@langchain/core/utils/testing";
import { OpikCallbackHandler } from "opik-langchain";
import { describe, expect, it } from "vitest";

import { buildChain, buildObjectRootChain, lastQuestion, remember } from "../src/chat.js";
import type { Session } from "../src/chat.js";
import { loadCorpus } from "../src/rules.js";

const corpus = loadCorpus(path.join(path.dirname(fileURLToPath(import.meta.url)), "../data/rules"));

function setup(responses: string[]) {
  const sessions = new Map<string, Session>([["t1", { history: [] }]]);
  const llm = new FakeListChatModel({ responses });
  return { sessions, deps: { llm, corpus, sessions } };
}

describe("rules-helper chain", () => {
  it("takes a string and returns a string", async () => {
    const { deps } = setup(["3 actions."]);
    const answer = await buildChain(deps).invoke("How many actions?", { configurable: { sessionId: "t1" } });
    expect(answer).toBe("3 actions.");
  });

  it("fails clearly for an unknown session", async () => {
    const { deps } = setup(["x"]);
    await expect(buildChain(deps).invoke("hi", { configurable: { sessionId: "nope" } })).rejects.toThrow(
      /Unknown session/
    );
  });

  it("remembers the last question for follow-ups", () => {
    const session: Session = { history: [] };
    remember(session, "What does Brace do?", "Skips movement.");
    expect(lastQuestion(session.history)).toBe("What does Brace do?");
  });

  it("wraps the answer in an object for the object-root variant", async () => {
    const { deps } = setup(["ok"]);
    const out = await buildObjectRootChain(deps).invoke({ question: "q" }, { configurable: { sessionId: "t1" } });
    expect(out).toEqual({ answer: "ok" });
  });

  it("runs with the Opik callback handler while tracking is disabled", async () => {
    const { deps } = setup(["fine"]);
    const handler = new OpikCallbackHandler({ threadId: "t1" });
    const answer = await buildChain(deps).invoke("Can I trade a jar?", {
      callbacks: [handler],
      configurable: { sessionId: "t1" },
    });
    expect(answer).toBe("fine");
  });
});
