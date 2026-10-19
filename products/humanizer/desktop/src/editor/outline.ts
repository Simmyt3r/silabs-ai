import type { Block } from "../ipc";

export const OUTLINE_PAGE_SIZE = 80;

export function filterOutline(blocks: readonly Block[], query: string): Block[] {
  const words = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  if (!words.length) return [...blocks];
  return blocks.filter(block => {
    const haystack = (block.text + " " + (block.style ?? "")).toLocaleLowerCase();
    return words.every(word => haystack.includes(word));
  });
}

export function nextOutlineLimit(current: number, total: number): number {
  return Math.min(total, current + OUTLINE_PAGE_SIZE);
}
