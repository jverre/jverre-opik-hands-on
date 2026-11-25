import { describe, expect, it } from "vitest";
import { BRIEF_TEMPLATES, renderBrief } from "../src/briefs.js";
import { pageVars } from "../src/illustrate.js";
import { HERO, PAGES } from "../src/story.js";

describe("briefs", () => {
  it("fills every slot from a page", () => {
    const out = renderBrief(BRIEF_TEMPLATES.v2, pageVars(PAGES[0]));
    expect(out).not.toContain("{{");
    expect(out).toContain(HERO);
    expect(out).toContain(PAGES[0].scene);
  });

  it("v2 adds the style, hero and no-lettering rules that v1 lacks", () => {
    const v1 = renderBrief(BRIEF_TEMPLATES.v1, pageVars(PAGES[1]));
    const v2 = renderBrief(BRIEF_TEMPLATES.v2, pageVars(PAGES[1]));
    expect(v1).not.toMatch(/watercolor|letters/);
    expect(v2).toMatch(/watercolor/);
    expect(v2).toMatch(/Do not draw any letters/);
    expect(v2.length).toBeGreaterThan(v1.length);
  });

  it("fails loudly when a variable is missing", () => {
    expect(() => renderBrief("Hello {{who}}", {})).toThrow(/who/);
  });
});
