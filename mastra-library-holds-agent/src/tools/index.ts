// The patron desk's five tools. Each one is a thin, schema-checked wrapper
// over a rule in src/library/rules.ts, so the model supplies arguments and the
// library code decides the outcome.
import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import { accountSummary, payFine, placeHold, renewLoan, searchBooks } from "../library/rules.ts";
import { getLibrary } from "../library/state.ts";

const cardId = z.string().describe("Library card number, like P-3001");

export const searchCatalogue = createTool({
  id: "search_catalogue",
  description: "Search the catalogue by title or author. Returns book ids with copies on the shelf.",
  inputSchema: z.object({ query: z.string().describe("Part of a title or author name") }),
  execute: async ({ query }) => ({ results: searchBooks(getLibrary(), query) }),
});

export const getAccount = createTool({
  id: "get_account",
  description: "Get a patron's account: fines owed, current loans (with due dates, renewals used, days overdue) and holds.",
  inputSchema: z.object({ patron_id: cardId }),
  execute: async ({ patron_id }) => accountSummary(getLibrary(), patron_id),
});

export const placeHoldTool = createTool({
  id: "place_hold",
  description: "Place a hold for a patron on a book that has no copies on the shelf.",
  inputSchema: z.object({ patron_id: cardId, book_id: z.string().describe("Book id, like B-100") }),
  execute: async ({ patron_id, book_id }) => placeHold(getLibrary(), patron_id, book_id),
});

export const renewLoanTool = createTool({
  id: "renew_loan",
  description: "Renew one loan by 14 days. Refuses when the patron owes $10 or more, the loan has hit its renewal limit, or someone else is waiting.",
  inputSchema: z.object({ patron_id: cardId, loan_id: z.string().describe("Loan id, like L-501") }),
  execute: async ({ patron_id, loan_id }) => renewLoan(getLibrary(), patron_id, loan_id),
});

export const payFineTool = createTool({
  id: "pay_fine",
  description: "Record a fine payment in US dollars against a patron's balance.",
  inputSchema: z.object({ patron_id: cardId, amount_usd: z.number().describe("Amount to pay, in dollars") }),
  execute: async ({ patron_id, amount_usd }) => payFine(getLibrary(), patron_id, amount_usd),
});

export const libraryTools = {
  searchCatalogue,
  getAccount,
  placeHold: placeHoldTool,
  renewLoan: renewLoanTool,
  payFine: payFineTool,
};
