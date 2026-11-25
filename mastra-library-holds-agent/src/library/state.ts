// The one shared, mutable library the tools act on. resetLibrary() gives the
// demo and the tests a clean slate.
import { freshLibrary, type LibraryState } from "../data/catalogue.ts";

let state: LibraryState = freshLibrary();

export const getLibrary = (): LibraryState => state;
export const resetLibrary = (): void => {
  state = freshLibrary();
};
