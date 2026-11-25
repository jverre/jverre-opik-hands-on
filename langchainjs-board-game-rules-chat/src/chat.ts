/**
 * The rules-helper chain. The visitor's question goes in as a plain string
 * and the answer comes out as a plain string; in between: load the table's
 * history, retrieve rule passages, prompt, model, parser.
 */
import { ChatPromptTemplate, MessagesPlaceholder } from "@langchain/core/prompts";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { RunnableLambda, RunnableSequence } from "@langchain/core/runnables";
import type { RunnableConfig } from "@langchain/core/runnables";
import { AIMessage, HumanMessage } from "@langchain/core/messages";
import type { BaseMessage } from "@langchain/core/messages";
import type { BaseLanguageModel } from "@langchain/core/language_models/base";

import { formatPassages, retrieve } from "./rules.js";
import type { Passage } from "./rules.js";

export const SYSTEM_PROMPT = `You are the rules helper at the Moss & Meeple board-game cafe.
Guests ask you about the cafe's house games from a small tablet at their table.
Answer ONLY from the rule excerpts provided below, in one to three short sentences,
and name the game you are talking about. If the excerpts do not cover the question,
say the house rules don't cover it and suggest asking the host at the counter.
Never invent rules or borrow rules from other games.

Rule excerpts:
{rules}`;

/** One table's memory: what was asked and answered so far. */
export interface Session {
  history: BaseMessage[];
}

export function lastQuestion(history: BaseMessage[]): string {
  for (let i = history.length - 1; i >= 0; i--) {
    if (history[i] instanceof HumanMessage) return String(history[i].content);
  }
  return "";
}

export interface ChainDeps {
  llm: BaseLanguageModel;
  corpus: Passage[];
  sessions: Map<string, Session>;
}

/**
 * Build the chain. Pass `{ sessionId }` in the invoke config's `configurable`
 * so the first step can find this table's history.
 */
export function buildChain({ llm, corpus, sessions }: ChainDeps) {
  const loadContext = RunnableLambda.from((question: string, config?: RunnableConfig) => {
    const sessionId = (config?.configurable as { sessionId?: string } | undefined)?.sessionId;
    const session = sessionId ? sessions.get(sessionId) : undefined;
    if (!session) throw new Error(`Unknown session: ${sessionId}`);
    // Follow-ups like "and can I trade it?" only make sense with the previous
    // question, so retrieval looks at both.
    const passages = retrieve(corpus, `${question} ${lastQuestion(session.history)}`);
    return { history: session.history, question, rules: formatPassages(passages) };
  }).withConfig({ runName: "load-table-context" });

  const prompt = ChatPromptTemplate.fromMessages([
    ["system", SYSTEM_PROMPT],
    new MessagesPlaceholder("history"),
    ["human", "{question}"],
  ]);

  return RunnableSequence.from([loadContext, prompt, llm, new StringOutputParser()]);
}

/** Remember one exchange so the next turn can refer back to it. */
export function remember(session: Session, question: string, answer: string): void {
  session.history.push(new HumanMessage(question), new AIMessage(answer));
}
