/** Word-aware, capped diff for readable side-by-side paragraphs.
 *
 * Large documents use a conservative whole-paragraph fallback instead of
 * allocating unbounded quadratic edit matrices on low-memory laptops.
 */
export type DiffPart = { text: string; changed: boolean };
export type Comparison = { before: DiffPart[]; after: DiffPart[] };

function joinParts(parts: DiffPart[]): DiffPart[] {
  const combined: DiffPart[] = [];
  for (const part of parts) {
    if (!part.text) continue;
    const previous = combined[combined.length - 1];
    if (previous && previous.changed === part.changed) previous.text += part.text;
    else combined.push({ ...part });
  }
  return combined;
}

export function compareText(before: string, after: string): Comparison {
  if (before === after) return {
    before: [{ text: before, changed: false }],
    after: [{ text: after, changed: false }],
  };

  const left = before.match(/\s+|[^\s]+/gu) || [];
  const right = after.match(/\s+|[^\s]+/gu) || [];
  const rows = left.length + 1;
  const cols = right.length + 1;
  if (left.length * right.length > 36000) {
    return {
      before: [{ text: before, changed: true }],
      after: [{ text: after, changed: true }],
    };
  }

  const matrix = new Uint16Array(rows * cols);
  for (let i = left.length - 1; i >= 0; i--) {
    for (let j = right.length - 1; j >= 0; j--) {
      matrix[i * cols + j] = left[i] === right[j]
        ? matrix[(i + 1) * cols + j + 1] + 1
        : Math.max(matrix[(i + 1) * cols + j], matrix[i * cols + j + 1]);
    }
  }

  const a: DiffPart[] = [];
  const b: DiffPart[] = [];
  let i = 0;
  let j = 0;
  while (i < left.length || j < right.length) {
    if (i < left.length && j < right.length && left[i] === right[j]) {
      a.push({ text: left[i], changed: false });
      b.push({ text: right[j], changed: false });
      i++; j++;
    } else if (j < right.length && (i === left.length ||
      matrix[i * cols + j + 1] >= matrix[(i + 1) * cols + j])) {
      b.push({ text: right[j], changed: true });
      j++;
    } else {
      a.push({ text: left[i], changed: true });
      i++;
    }
  }
  return { before: joinParts(a), after: joinParts(b) };
}
