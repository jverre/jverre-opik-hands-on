import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { Opik } from "opik";
import { BRIEF_TEMPLATES } from "../src/briefs.js";
import { illustratePage } from "../src/illustrate.js";
import { PAGES } from "../src/story.js";

const PIXEL =
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==";

// A stub OpenAI client: records the request and returns a 1x1 PNG.
function stubOpenAI(calls: any[]) {
  return {
    images: {
      generate: async (req: unknown) => {
        calls.push(req);
        return { data: [{ b64_json: PIXEL }] };
      },
    },
  } as any;
}

const dirs: string[] = [];
afterEach(() => dirs.splice(0).forEach((d) => fs.rmSync(d, { recursive: true, force: true })));

describe("illustratePage", () => {
  it("renders the brief, calls the image model and saves the PNG (tracking disabled)", async () => {
    const outDir = fs.mkdtempSync(path.join(os.tmpdir(), "storybook-"));
    dirs.push(outDir);
    const calls: any[] = [];
    // OPIK_TRACK_DISABLE=true (vitest.config.ts) makes the traced path a no-op.
    const opik = new Opik({ projectName: "unit-tests" });

    const result = await illustratePage({
      openai: stubOpenAI(calls),
      opik,
      page: PAGES[0],
      version: "v2",
      template: BRIEF_TEMPLATES.v2,
      outDir,
    });

    expect(calls).toHaveLength(1);
    expect(calls[0].model).toBe("gpt-image-1-mini");
    expect(calls[0].quality).toBe("low");
    expect(calls[0].prompt).toBe(result.prompt);
    expect(path.basename(result.file)).toBe("v2-page-1-dusk.png");
    expect(fs.readFileSync(result.file).subarray(1, 4).toString()).toBe("PNG");
  });

  it("rethrows when the model returns no image", async () => {
    const outDir = fs.mkdtempSync(path.join(os.tmpdir(), "storybook-"));
    dirs.push(outDir);
    const openai = { images: { generate: async () => ({ data: [] }) } } as any;
    await expect(
      illustratePage({
        openai,
        opik: new Opik({ projectName: "unit-tests" }),
        page: PAGES[0],
        version: "v1",
        template: BRIEF_TEMPLATES.v1,
        outDir,
      }),
    ).rejects.toThrow(/no image/);
  });
});
