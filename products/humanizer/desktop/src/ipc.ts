import { invoke } from "@tauri-apps/api/core";

export type Block = {
  index: number;
  kind: "heading" | "paragraph" | "table_cell";
  text: string;
  style: string | null;
  editable: boolean;
  reason: string | null;
};
export type OpenedDocument = {
  path: string;
  fingerprint: string;
  name: string;
  format: "docx" | "md" | "txt";
  blocks: Block[];
};
export type RewriteMode = "natural" | "academic" | "professional" | "simplify" | "grammar" | "shorten" | "expand";
export type RewriteProposal = {
  index: number;
  proposal: string;
  passed: boolean;
  issues: string[];
  elapsed_seconds: number;
};
export type ExportResult = { destination: string; revised_count: number };

async function command<T>(payload: Record<string, unknown>): Promise<T> {
  return invoke<T>("bridge", { payload });
}

export const localApi = {
  open: (path: string) => command<OpenedDocument>({ action: "open", path }),
  rewrite: (doc: OpenedDocument, index: number, mode: RewriteMode, modelPath: string) =>
    command<RewriteProposal>({
      action: "rewrite", path: doc.path, fingerprint: doc.fingerprint, index, mode,
      backend: "gguf", model_path: modelPath,
    }),
  export: (doc: OpenedDocument, destination: string, revisions: Record<number, string>) =>
    command<ExportResult>({ action: "export", path: doc.path, fingerprint: doc.fingerprint, destination, revisions }),
};
