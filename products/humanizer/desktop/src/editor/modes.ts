import type { RewriteMode } from "../ipc";

export const MODES: ReadonlyArray<{
  id: RewriteMode;
  label: string;
  detail: string;
}> = [
  { id: "natural", label: "Humanize", detail: "More natural wording and sentence flow." },
  { id: "academic", label: "Academic", detail: "Clear academic tone without unnecessary jargon." },
  { id: "grammar", label: "Grammar", detail: "Correct grammar and spelling; keep your voice." },
  { id: "professional", label: "Professional", detail: "Polished writing for formal documents." },
  { id: "simplify", label: "Simplify", detail: "Make complex wording easier to understand." },
  { id: "shorten", label: "Shorten", detail: "Remove filler while keeping key details." },
  { id: "expand", label: "Expand", detail: "Improve explanations without inventing facts." },
];
