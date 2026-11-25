// Fictional Larkspur Public Library data. Pure data, no behaviour: the rules
// that act on it live in src/library/rules.ts.

// The library's "today" is fixed so fines and due dates are the same on every run.
export const TODAY = "2026-11-25";

export interface Book {
  book_id: string;
  title: string;
  author: string;
  copies_total: number;
  copies_on_shelf: number;
}

export interface Loan {
  loan_id: string;
  book_id: string;
  due: string; // YYYY-MM-DD
  renewals_used: number;
}

export interface Hold {
  hold_id: string;
  book_id: string;
  patron_id: string;
}

export interface Patron {
  patron_id: string;
  name: string;
  fines_usd: number;
}

export interface LibraryState {
  books: Book[];
  patrons: Patron[];
  loans: Record<string, Loan[]>; // by patron_id
  holds: Hold[];
}

// A fresh copy every call, so each demo run (and each test) starts identical.
export function freshLibrary(): LibraryState {
  return {
    books: [
      { book_id: "B-100", title: "The Salt Road", author: "Marit Oyelaran", copies_total: 2, copies_on_shelf: 0 },
      { book_id: "B-101", title: "Kelp and Lanterns", author: "Dev Rautenbach", copies_total: 1, copies_on_shelf: 1 },
      { book_id: "B-102", title: "A Field Guide to Fog", author: "Wilhelmina Tross", copies_total: 3, copies_on_shelf: 2 },
      { book_id: "B-103", title: "Orchard Arithmetic", author: "Ines Calloway", copies_total: 1, copies_on_shelf: 0 },
    ],
    patrons: [
      { patron_id: "P-3001", name: "Imogen Hale", fines_usd: 3.5 },
      { patron_id: "P-3002", name: "Tobias Wren", fines_usd: 12.0 },
    ],
    loans: {
      "P-3001": [
        // Due soon, nobody waiting: renewable.
        { loan_id: "L-501", book_id: "B-102", due: "2026-11-28", renewals_used: 0 },
        // Another patron is waiting for this one: renewal must be refused.
        { loan_id: "L-502", book_id: "B-103", due: "2026-11-27", renewals_used: 1 },
      ],
      "P-3002": [
        // Overdue, and the account is over the fines limit.
        { loan_id: "L-601", book_id: "B-100", due: "2026-11-10", renewals_used: 2 },
      ],
    },
    holds: [{ hold_id: "H-900", book_id: "B-103", patron_id: "P-3002" }],
  };
}
