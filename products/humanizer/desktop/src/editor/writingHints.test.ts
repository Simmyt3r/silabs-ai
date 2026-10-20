import { describe, expect, it } from "vitest";
import { inspectWriting, applyWritingHint } from "./writingHints";

describe("instant on-device writing assistance", () => {
  it("finds repeat words and permits one-click correction without model calls", () => {
    const text = "This is is a draft.";
    const hint = inspectWriting(text).find(x => x.title === "Repeated word");
    expect(hint).toBeDefined();
    expect(applyWritingHint(text, hint!)).toBe("This is a draft.");
  });

  it("handles punctuation spacing and excessive whitespace", () => {
    const source = "Consider this  option ,please.";
    const hints = inspectWriting(source);
    expect(hints.some(h => h.title === "Extra spaces")).toBe(true);
    expect(hints.some(h => h.title === "Spacing before punctuation")).toBe(true);
  });

  it("never auto-rewrites a long sentence based on an uncertain style heuristic", () => {
    const text = "The study " + "examined participants ".repeat(42) + "in detail.";
    const hint = inspectWriting(text).find(h => h.title === "Long sentence");
    expect(hint).toBeDefined();
    expect(hint!.replacement).toBe(text);
  });
});
