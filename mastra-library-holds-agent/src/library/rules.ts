// The circulation rules, as plain functions over LibraryState. The tools are
// thin wrappers around these, which is also what the offline tests exercise.
import { TODAY, type Book, type LibraryState } from "../data/catalogue.ts";

export const MAX_RENEWALS = 2;
export const RENEWAL_DAYS = 14;
export const FINES_BLOCK_USD = 10;
export const MAX_HOLDS = 3;

export function addDays(date: string, days: number): string {
  const d = new Date(`${date}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

export function daysOverdue(due: string, today = TODAY): number {
  const ms = Date.parse(`${today}T00:00:00Z`) - Date.parse(`${due}T00:00:00Z`);
  return Math.max(0, Math.round(ms / 86_400_000));
}

export function findBook(state: LibraryState, id: string): Book | undefined {
  return state.books.find((b) => b.book_id === id.toUpperCase().trim());
}

export function searchBooks(state: LibraryState, query: string): Book[] {
  const q = query.toLowerCase().trim();
  return state.books.filter((b) => b.title.toLowerCase().includes(q) || b.author.toLowerCase().includes(q));
}

export function accountSummary(state: LibraryState, patronId: string) {
  const patron = state.patrons.find((p) => p.patron_id === patronId.toUpperCase().trim());
  if (!patron) return { error: `No patron with card ${patronId}. Ask the patron to re-check the number.` };
  return {
    patron_id: patron.patron_id,
    name: patron.name,
    fines_usd: patron.fines_usd,
    loans: (state.loans[patron.patron_id] ?? []).map((l) => ({
      ...l,
      title: findBook(state, l.book_id)?.title,
      days_overdue: daysOverdue(l.due),
    })),
    holds: state.holds
      .filter((h) => h.patron_id === patron.patron_id)
      .map((h) => ({ ...h, title: findBook(state, h.book_id)?.title })),
  };
}

export function placeHold(state: LibraryState, patronId: string, bookId: string) {
  const patron = state.patrons.find((p) => p.patron_id === patronId.toUpperCase().trim());
  const book = findBook(state, bookId);
  if (!patron) return { ok: false, error: `No patron with card ${patronId}.` };
  if (!book) return { ok: false, error: `No book with id ${bookId}.` };
  if (patron.fines_usd >= FINES_BLOCK_USD)
    return { ok: false, error: `Holds are blocked: fines of $${patron.fines_usd.toFixed(2)} are at or above $${FINES_BLOCK_USD}.` };
  const mine = state.holds.filter((h) => h.patron_id === patron.patron_id);
  if (mine.length >= MAX_HOLDS) return { ok: false, error: `Patron already has the maximum of ${MAX_HOLDS} holds.` };
  if (mine.some((h) => h.book_id === book.book_id)) return { ok: false, error: "Patron already has a hold on this title." };
  if (book.copies_on_shelf > 0)
    return { ok: false, error: `"${book.title}" is on the shelf (${book.copies_on_shelf} copies); no hold needed, just borrow it.` };
  const queue = state.holds.filter((h) => h.book_id === book.book_id).length;
  const hold = { hold_id: `H-${901 + state.holds.length}`, book_id: book.book_id, patron_id: patron.patron_id };
  state.holds.push(hold);
  return { ok: true, hold_id: hold.hold_id, title: book.title, queue_position: queue + 1 };
}

export function renewLoan(state: LibraryState, patronId: string, loanId: string) {
  const patron = state.patrons.find((p) => p.patron_id === patronId.toUpperCase().trim());
  if (!patron) return { ok: false, error: `No patron with card ${patronId}.` };
  const loan = (state.loans[patron.patron_id] ?? []).find((l) => l.loan_id === loanId.toUpperCase().trim());
  if (!loan) return { ok: false, error: `Patron ${patron.patron_id} has no loan ${loanId}.` };
  const title = findBook(state, loan.book_id)?.title;
  if (patron.fines_usd >= FINES_BLOCK_USD)
    return { ok: false, error: `Renewal blocked: fines of $${patron.fines_usd.toFixed(2)} must be paid first.` };
  if (loan.renewals_used >= MAX_RENEWALS)
    return { ok: false, error: `"${title}" has already been renewed ${MAX_RENEWALS} times, the maximum.` };
  if (state.holds.some((h) => h.book_id === loan.book_id && h.patron_id !== patron.patron_id))
    return { ok: false, error: `"${title}" cannot be renewed: another patron is waiting for it.` };
  loan.due = addDays(loan.due, RENEWAL_DAYS);
  loan.renewals_used += 1;
  return { ok: true, loan_id: loan.loan_id, title, new_due: loan.due, renewals_used: loan.renewals_used };
}

export function payFine(state: LibraryState, patronId: string, amountUsd: number) {
  const patron = state.patrons.find((p) => p.patron_id === patronId.toUpperCase().trim());
  if (!patron) return { ok: false, error: `No patron with card ${patronId}.` };
  if (amountUsd <= 0) return { ok: false, error: "Payment must be more than $0." };
  if (amountUsd > patron.fines_usd)
    return { ok: false, error: `Payment of $${amountUsd.toFixed(2)} exceeds the balance of $${patron.fines_usd.toFixed(2)}.` };
  patron.fines_usd = Math.round((patron.fines_usd - amountUsd) * 100) / 100;
  return { ok: true, paid_usd: amountUsd, remaining_usd: patron.fines_usd };
}
