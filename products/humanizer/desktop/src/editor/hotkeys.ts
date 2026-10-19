export type WorkspaceShortcut = "open" | "export" | "rewrite" | "reject";

type KeyInput = Pick<KeyboardEvent, "key" | "ctrlKey" | "metaKey" | "shiftKey" | "altKey" | "repeat"> & {
  target: EventTarget | null;
};

export function getWorkspaceShortcut(event: KeyInput): WorkspaceShortcut | null {
  if (event.repeat || event.altKey) return null;
  const target = event.target as (EventTarget & {
    tagName?: string; isContentEditable?: boolean;
  }) | null;
  const tag = target?.tagName?.toLowerCase();
  if (target?.isContentEditable || tag === "input" || tag === "textarea" || tag === "select") {
    return null;
  }

  const command = event.ctrlKey || event.metaKey;
  const key = event.key.toLowerCase();
  if (command && !event.shiftKey && key === "o") return "open";
  if (command && event.shiftKey && key === "s") return "export";
  if (command && !event.shiftKey && key === "enter") return "rewrite";
  if (!command && !event.shiftKey && event.key === "Escape") return "reject";
  return null;
}
