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
export type OfflineIssue = {
  category: "grammar" | "spelling";
  rule_id: string;
  title: string;
  message: string;
  start: number;
  end: number;
  original: string;
  replacements: string[];
  confidence: "high" | "medium";
};
export type OfflineAnalysis = {
  language: string;
  engine: string;
  issues: OfflineIssue[];
  text_length: number;
  limitations: string;
};
export type LocalSimilarityReport = {
  scope: "selected-local-files-only";
  status: string;
  source_count: number;
  draft_words: number;
  coverage_percent: number;
  explanation: string;
  sources: Array<{
    name: string;
    matched_words: number;
    draft_coverage_percent: number;
    match_excerpts: Array<{ draft_excerpt: string; source_excerpt: string }>;
  }>;
};

export type LocalDiagnostics = {
  components_present: boolean;
  model_file_found: boolean;
  gguf_header_valid: boolean;
  model_bytes: number;
  inference_installed: boolean;
  word_support_installed: boolean;
  issues: string[];
  note: string;
};


async function command<T>(payload: Record<string, unknown>): Promise<T> {
  return invoke<T>("bridge", { payload });
}

export const localApi = {
  analyseWriting: (text: string) =>
    command<OfflineAnalysis>({ action: "analyse_writing", text }),
  compareSources: (doc: OpenedDocument, revisions: Record<number, string>, sources: string[]) =>
    command<LocalSimilarityReport>({
      action: "compare_local_sources", path: doc.path,
      fingerprint: doc.fingerprint, revisions, sources,
    }),
  diagnostics: (modelPath: string) => command<LocalDiagnostics>({ action: "diagnostics", model_path: modelPath }),
  open: (path: string) => command<OpenedDocument>({ action: "open", path }),
  rewrite: (doc: OpenedDocument, index: number, mode: RewriteMode, modelPath: string, text?: string) =>
    command<RewriteProposal>({
      action: "rewrite", path: doc.path, fingerprint: doc.fingerprint, index, mode,
      backend: "gguf", model_path: modelPath, text,
    }),
  export: (doc: OpenedDocument, destination: string, revisions: Record<number, string>) =>
    command<ExportResult>({ action: "export", path: doc.path, fingerprint: doc.fingerprint, destination, revisions }),
};
