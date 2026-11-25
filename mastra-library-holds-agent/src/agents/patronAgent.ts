import { Agent } from "@mastra/core/agent";
import { openai } from "@ai-sdk/openai";
import { libraryTools } from "../tools/index.ts";

export const patronAgent = new Agent({
  id: "patron-agent",
  name: "larkspur-patron-agent",
  instructions:
    "You are the patron-desk assistant for Larkspur Public Library. " +
    "Never guess account details: call get_account before discussing loans, holds or fines, " +
    "and search_catalogue before talking about a book. Only call place_hold, renew_loan or " +
    "pay_fine when the patron clearly asked for it. If a tool refuses, explain the reason " +
    "plainly and offer the next step (for example paying a fine first). " +
    "Be warm and brief: 2-4 sentences, no bullet lists.",
  model: openai("gpt-4o-mini"),
  tools: libraryTools,
});
