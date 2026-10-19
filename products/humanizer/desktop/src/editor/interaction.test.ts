import { describe, expect, it } from "vitest";
import { filterOutline, nextOutlineLimit, OUTLINE_PAGE_SIZE } from "./outline";
import { getWorkspaceShortcut } from "./hotkeys";
import type { Block } from "../ipc";

const makeBlock = (index: number, text: string, style: string | null = null): Block => ({
  index, text, style, kind: "paragraph", editable: true, reason: null,
});

function keyEvent(key: string, args: Record<string, unknown> = {}) {
  return {
    key, ctrlKey: false, metaKey: false, shiftKey: false,
    altKey: false, repeat: false, target: null, ...args,
  } as Parameters<typeof getWorkspaceShortcut>[0];
}

describe("document outline navigation", () => {
  it("finds paragraphs using multiple case-insensitive terms and styles", () => {
    const blocks = [makeBlock(1, "Sentinel vegetation data", "Normal"),
      makeBlock(2, "Field observations", "Heading 2")];
    expect(filterOutline(blocks, "VEGETATION sentinel").map(block => block.index)).toEqual([1]);
    expect(filterOutline(blocks, "heading 2").map(block => block.index)).toEqual([2]);
  });

  it("progresses in bounded increments without skipping the final page", () => {
    expect(nextOutlineLimit(OUTLINE_PAGE_SIZE, 205)).toBe(160);
    expect(nextOutlineLimit(160, 205)).toBe(205);
    expect(nextOutlineLimit(205, 205)).toBe(205);
  });
});

describe("safe desktop hotkeys", () => {
  it("maps open, export, generate and reject", () => {
    expect(getWorkspaceShortcut(keyEvent("o", { ctrlKey: true }))).toBe("open");
    expect(getWorkspaceShortcut(keyEvent("S", { ctrlKey: true, shiftKey: true }))).toBe("export");
    expect(getWorkspaceShortcut(keyEvent("Enter", { ctrlKey: true }))).toBe("rewrite");
    expect(getWorkspaceShortcut(keyEvent("Escape"))).toBe("reject");
  });

  it("does not hijack typing or repeated shortcuts", () => {
    expect(getWorkspaceShortcut(keyEvent("o", { ctrlKey: true, target: { tagName: "INPUT" } }))).toBe(null);
    expect(getWorkspaceShortcut(keyEvent("Escape", { target: { isContentEditable: true } }))).toBe(null);
    expect(getWorkspaceShortcut(keyEvent("Enter", { ctrlKey: true, repeat: true }))).toBe(null);
    expect(getWorkspaceShortcut(keyEvent("s", { ctrlKey: true }))).toBe(null);
  });
});
