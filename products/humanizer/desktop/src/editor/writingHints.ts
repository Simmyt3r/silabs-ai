/** Instant, entirely local writing hints. Conservative by design:
 * no cloud service, no model load and no claim to diagnose every grammar error.
 */
export type WritingHint = {
  id: string;
  type: "correctness" | "clarity";
  title: string;
  explanation: string;
  start: number;
  end: number;
  replacement: string;
};

export function inspectWriting(text: string): WritingHint[] {
  const hints: WritingHint[] = [];
  const add = (
    type: WritingHint["type"], title: string, explanation: string,
    start: number, end: number, replacement: string,
  ) => {
    if (hints.some(h => Math.max(start, h.start) < Math.min(end, h.end))) return;
    hints.push({ id: String(start) + ":" + String(end) + ":" + title,
      type, title, explanation, start, end, replacement });
  };

  for (const match of text.matchAll(/\b([\p{L}]+)\s+(\1)\b/giu)) {
    const start = match.index!;
    add("correctness", "Repeated word",
      "The same word appears twice. Consider removing the repetition.",
      start, start + match[0].length, match[1]);
  }

  for (const match of text.matchAll(/[ \t]+[,.!?;:]/g)) {
    const start = match.index!;
    add("correctness", "Spacing before punctuation",
      "Punctuation normally follows the word without a preceding space.",
      start, start + match[0].length, match[0].trimStart());
  }

  for (const match of text.matchAll(/ {2,}/g)) {
    const start = match.index!;
    add("correctness", "Extra spaces",
      "Use one space between words.",
      start, start + match[0].length, " ");
  }

  for (const match of text.matchAll(/[!?]{2,}/g)) {
    const start = match.index!;
    add("clarity", "Repeated punctuation",
      "A single question mark or exclamation point is usually easier to read.",
      start, start + match[0].length, match[0][0]);
  }

  // Do not auto-correct complex or uncertain grammar using simplistic regexes.
  const sentences = text.matchAll(/[^.!?\n]+[.!?]?/g);
  for (const match of sentences) {
    const words = (match[0].match(/\S+/g) ?? []).length;
    if (words > 38) {
      add("clarity", "Long sentence",
        "Consider splitting this sentence. This suggestion requires your judgment.",
        match.index!, match.index! + match[0].length, match[0]);
    }
  }
  return hints.sort((a, b) => a.start - b.start);
}

export function applyWritingHint(text: string, hint: WritingHint): string {
  if (hint.start < 0 || hint.end > text.length || hint.end < hint.start) return text;
  return text.slice(0, hint.start) + hint.replacement + text.slice(hint.end);
}
