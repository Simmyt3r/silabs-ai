export type ReviewStatus = { kind: "info" | "error" | "success"; message: string } | null;

export function snapshotOf(revisions: Record<number, string>): string {
  // The key order does not depend on the order in which the editor accepted edits.
  return JSON.stringify(
    Object.entries(revisions)
      .sort(([a], [b]) => Number(a) - Number(b)),
  );
}

export function canEditBlock(block: { editable: boolean; kind: string } | null): boolean {
  return !!block && block.editable;
}

export function wordCount(text: string): number {
  return (text.trim().match(/\S+/g) || []).length;
}
