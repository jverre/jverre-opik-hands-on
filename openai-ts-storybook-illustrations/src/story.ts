// The fictional story: "Pip and the Lantern Moss". Two pages are enough to
// see how a brief behaves; each page fills the variables of a brief template.

export interface StoryPage {
  id: string;
  title: string;
  scene: string;
  mood: string;
}

export const STORY_TITLE = "Pip and the Lantern Moss";

export const PAGES: StoryPage[] = [
  {
    id: "page-1-dusk",
    title: "Pip sets out at dusk",
    scene:
      "Pip leaves a hollow log on a mossy riverbank just after sunset, " +
      "her glowing shell lighting a small circle of ground around her.",
    mood: "quiet, brave, a little sleepy",
  },
  {
    id: "page-2-leaf-bridge",
    title: "The leaf bridge",
    scene:
      "Pip inches across a bridge made of floating leaves over a slow stream " +
      "while a curious green frog watches from a lily pad.",
    mood: "wobbly suspense that turns to wonder",
  },
];

// The character description a good brief repeats on every page.
export const HERO =
  "Pip, a small pale-green snail with a round spiral shell that glows warm " +
  "amber like a lantern, and a tiny red scarf";
