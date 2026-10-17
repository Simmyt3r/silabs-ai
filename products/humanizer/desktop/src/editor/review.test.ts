import { describe, expect, it } from "vitest";
import { compareText } from "./diff";
import { canEditBlock, snapshotOf, wordCount } from "./review";

describe("word comparison", () => {
  it("preserves original and revised wording without dropping whitespace", () => {
    const before = "This research  seeks to examine responses.";
    const after = "This study examines responses.";
    const diff = compareText(before, after);
    expect(diff.before.map(item => item.text).join("")).toBe(before);
    expect(diff.after.map(item => item.text).join("")).toBe(after);
    expect(diff.before.some(item => item.changed)).toBe(true);
    expect(diff.after.some(item => item.changed)).toBe(true);
  });

  it("keeps identical text unmarked", () => {
    const diff = compareText("No revision.", "No revision.");
    expect(diff.before).toEqual([{ text: "No revision.", changed: false }]);
    expect(diff.after).toEqual([{ text: "No revision.", changed: false }]);
  });

  it("falls back safely on very long text", () => {
    const before = ("alpha ".repeat(3000)).trim();
    const after = ("beta ".repeat(3000)).trim();
    const diff = compareText(before, after);
    expect(diff.before[0].text).toBe(before);
    expect(diff.after[0].text).toBe(after);
  });
});

describe("review state", () => {
  it("is stable regardless of revision acceptance order", () => {
    expect(snapshotOf({ 14: "two", 2: "one" })).toBe(snapshotOf({ 2: "one", 14: "two" }));
  });

  it("disallows protected and heading paragraphs", () => {
    expect(canEditBlock({ editable: true, kind: "paragraph" })).toBe(true);
    expect(canEditBlock({ editable: true, kind: "heading" })).toBe(false);
    expect(canEditBlock({ editable: false, kind: "table_cell" })).toBe(false);
    expect(canEditBlock(null)).toBe(false);
  });

  it("counts words without treating repeated whitespace as words", () => {
    expect(wordCount("  A   useful\nsentence. ")).toBe(3);
    expect(wordCount("")).toBe(0);
  });
});
