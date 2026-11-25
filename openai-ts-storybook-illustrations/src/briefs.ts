// Two versions of the illustration brief. Templates use {{variable}} slots.
//   v1: just the scene.
//   v2: adds the rules an art director would write after seeing v1 results:
//       a fixed character description, a style, no lettering, and room for text.

export const BRIEF_NAME = "storybook-page-brief";

export const BRIEF_V1 =
  "A children's picture-book illustration. {{scene}} " +
  "The main character is {{hero}}. Mood: {{mood}}.";

export const BRIEF_V2 =
  "A children's picture-book illustration in soft watercolor with warm, " +
  "muted colors and gentle ink outlines. {{scene}} " +
  "The main character, drawn identically on every page, is {{hero}}. " +
  "Mood: {{mood}}. " +
  "Compose a square page with the character fully visible and the top third " +
  "left calm and uncluttered, so the story text can sit there. " +
  "Do not draw any letters, words, captions or signs.";

export const V2_CHANGE_DESCRIPTION =
  "Add watercolor style, fixed hero description, text-free calm top third";

export const BRIEF_TEMPLATES: Record<string, string> = {
  v1: BRIEF_V1,
  v2: BRIEF_V2,
};

export function renderBrief(template: string, vars: Record<string, string>): string {
  return template.replace(/\{\{\s*(\w+)\s*\}\}/g, (_match, key: string) => {
    const value = vars[key];
    if (value === undefined) throw new Error(`Brief needs a "${key}" value`);
    return value;
  });
}
