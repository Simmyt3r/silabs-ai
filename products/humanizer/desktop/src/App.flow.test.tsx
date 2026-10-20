// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

const mocks = vi.hoisted(() => ({
  invoke: vi.fn(),
  openDialog: vi.fn(),
  saveDialog: vi.fn(),
  confirmDialog: vi.fn(),
  onCloseRequested: vi.fn(),
  localOpen: vi.fn(),
  localRewrite: vi.fn(),
  localExport: vi.fn(),
  localDiagnostics: vi.fn(),
  localAnalyse: vi.fn(),
  localCompare: vi.fn(),
}));

vi.mock("@tauri-apps/api/core", () => ({ invoke: mocks.invoke }));
vi.mock("@tauri-apps/api/window", () => ({
  getCurrentWindow: () => ({
    onCloseRequested: mocks.onCloseRequested,
    close: vi.fn(),
  }),
}));
vi.mock("@tauri-apps/plugin-dialog", () => ({
  open: mocks.openDialog,
  save: mocks.saveDialog,
  confirm: mocks.confirmDialog,
}));
vi.mock("./ipc", () => ({
  localApi: {
    open: mocks.localOpen,
    rewrite: mocks.localRewrite,
    export: mocks.localExport,
    diagnostics: mocks.localDiagnostics,
    analyseWriting: mocks.localAnalyse,
    compareSources: mocks.localCompare,
  },
}));

const sample = {
  path: "C:\\tests\\paper.docx",
  name: "paper.docx",
  fingerprint: "sample-sha",
  format: "docx",
  blocks: [
    { index: 0, kind: "heading", text: "Chapter One", style: "Heading 1", editable: false, reason: "Protected heading" },
    { index: 1, kind: "paragraph", text: "This sentences is unclear.", style: "Normal", editable: true, reason: null },
    { index: 2, kind: "paragraph", text: "Smith (2024) reported 67.4% adoption.", style: "Normal", editable: true, reason: null },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
  mocks.invoke.mockResolvedValue({ packaged: true, model_path: "C:\\Program Files\\Silabs\\model\\qwen3-1.7b.gguf" });
  mocks.openDialog.mockResolvedValue(sample.path);
  mocks.saveDialog.mockResolvedValue("C:\\tests\\paper-revised.docx");
  mocks.confirmDialog.mockResolvedValue(true);
  mocks.onCloseRequested.mockResolvedValue(() => {});
  mocks.localOpen.mockResolvedValue(sample);
  mocks.localRewrite.mockResolvedValue({
    index: 1, proposal: "This sentence is clearer.", passed: true, issues: [], elapsed_seconds: 4.2,
  });
  mocks.localExport.mockResolvedValue({ destination: "C:\\tests\\paper-revised.docx", revised_count: 1 });
  mocks.localAnalyse.mockResolvedValue({
    language: "en", engine: "offline-rules-and-word-frequency",
    issues: [], text_length: 26, limitations: "English-only, suggestive not exhaustive.",
  });
  mocks.localCompare.mockResolvedValue({
    scope: "selected-local-files-only", status: "compared",
    source_count: 1, draft_words: 40, coverage_percent: 20,
    explanation: "Only user-selected files searched", sources: [{
      name: "reference.docx", matched_words: 8, draft_coverage_percent: 20,
      match_excerpts: [{ draft_excerpt: "an example phrase", source_excerpt: "an example phrase" }],
    }],
  });
  mocks.localDiagnostics.mockResolvedValue({
    components_present: true,
    model_file_found: true,
    gguf_header_valid: true,
    model_bytes: 1282439264,
    inference_installed: true,
    word_support_installed: true,
    issues: [],
    note: "File and component checks only; model load and rewrite quality are not tested.",
  });
});
afterEach(cleanup);

async function openDocument() {
  fireEvent.click(screen.getByRole("button", { name: "Choose document" }));
  await screen.findByRole("heading", { name: /Refine your writing|Edit your document/i });
}

describe("complete offline editing flow", () => {
  it("opens a document, rewrites, reviews, accepts and exports safely", async () => {
    render(<App />);
    await waitFor(() => expect(mocks.invoke).toHaveBeenCalledWith("runtime_info"));
    await openDocument();
    expect(screen.getAllByText("Chapter One").length).toBeGreaterThan(0);
    expect(screen.getByText("0 accepted · 2 editable")).toBeTruthy();
    fireEvent.click(screen.getByRole("tab", { name: /Rewrite/i }));
    const generate = screen.getByRole("button", { name: /generate suggestion/i });
    expect(generate.hasAttribute("disabled")).toBe(false);
    fireEvent.click(generate);
    await waitFor(() => expect(mocks.localRewrite).toHaveBeenCalledWith(
      sample, 1, "natural", "C:\\Program Files\\Silabs\\model\\qwen3-1.7b.gguf", "This sentences is unclear.",
    ));
    await screen.findByRole("button", { name: "Accept" });
    expect(screen.getByRole("article", { name: "Revised passage" }).textContent).toContain("This sentence is clearer.");
    fireEvent.click(screen.getByRole("button", { name: "Accept" }));
    expect(screen.getByText("1 accepted · 2 editable")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Export revised file/i }));
    await waitFor(() => expect(mocks.localExport).toHaveBeenCalledWith(
      sample, "C:\\tests\\paper-revised.docx", { 1: "This sentence is clearer." },
    ));
    expect(await screen.findByText("Exported")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Export revised file/i }).hasAttribute("disabled")).toBe(true);
  });

  it("rejects failed protection checks without allowing acceptance", async () => {
    mocks.localRewrite.mockResolvedValue({
      index: 1, proposal: "67% of participants?", passed: false,
      issues: ["Protected number changed"], elapsed_seconds: 1,
    });
    render(<App />);
    await openDocument();
    fireEvent.click(screen.getByRole("tab", { name: /Rewrite/i }));
    fireEvent.click(screen.getByRole("button", { name: /Generate suggestion/i }));
    const rejected = await screen.findByText("Suggestion needs attention");
    expect(rejected).toBeTruthy();
    expect(screen.getByRole("button", { name: "Accept" }).hasAttribute("disabled")).toBe(true);
    expect(screen.getByRole("button", { name: /Export revised file/i }).hasAttribute("disabled")).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: /Reject/i }));
    expect(screen.queryByText("Suggestion needs attention")).toBeNull();
  });

  it("runs a fully local, informative first-run setup check", async () => {
    render(<App />);
    await waitFor(() => expect(mocks.invoke).toHaveBeenCalledWith("runtime_info"));
    fireEvent.click(screen.getByRole("button", { name: /Model settings/i }));
    fireEvent.click(screen.getByRole("button", { name: /Check local setup/i }));
    await waitFor(() => expect(mocks.localDiagnostics).toHaveBeenCalledWith(
      "C:\\Program Files\\Silabs\\model\\qwen3-1.7b.gguf",
    ));
    expect(await screen.findByText("Core offline files and libraries found")).toBeTruthy();
    expect(screen.getByText(/model load and rewrite quality are not tested/i)).toBeTruthy();
  });

  it("explains failed local dependencies without claiming the model is ready", async () => {
    mocks.localDiagnostics.mockResolvedValueOnce({
      components_present: false, model_file_found: false, gguf_header_valid: false,
      model_bytes: 0, inference_installed: true, word_support_installed: true,
      issues: ["Local GGUF weights not found or invalid. Check Model settings."],
      note: "File and component checks only; model load and rewrite quality are not tested.",
    });
    render(<App />);
    await waitFor(() => expect(mocks.invoke).toHaveBeenCalledWith("runtime_info"));
    fireEvent.click(screen.getByRole("button", { name: /Model settings/i }));
    fireEvent.click(screen.getByRole("button", { name: /Check local setup/i }));
    expect(await screen.findByText("Offline setup requires attention")).toBeTruthy();
    expect(screen.getByText(/Local GGUF weights not found or invalid/i)).toBeTruthy();
  });

  it("allows typing directly into the document and fixing local grammar hints", async () => {
    render(<App />);
    await openDocument();
    const editor = screen.getByRole("textbox", { name: "Edit selected passage" });
    fireEvent.change(editor, { target: { value: "This this sentence is unclear." } });
    expect(await screen.findByText("Repeated word")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Apply correction/i }));
    expect((editor as HTMLTextAreaElement).value).toBe("This sentence is unclear.");
    expect(screen.getByText("1 accepted · 2 editable")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Export revised file/i }));
    await waitFor(() => expect(mocks.localExport).toHaveBeenCalledWith(
      sample, "C:\\tests\\paper-revised.docx", { 1: "This sentence is unclear." },
    ));
  });

  it("rewrites only selected words and preserves the rest of a paragraph", async () => {
    mocks.localRewrite.mockResolvedValue({
      index: 1, proposal: "These sentences", passed: true,
      issues: [], elapsed_seconds: 2,
    });
    render(<App />);
    await openDocument();
    const editor = screen.getByRole("textbox", { name: "Edit selected passage" }) as HTMLTextAreaElement;
    editor.setSelectionRange(0, 14);
    fireEvent.select(editor);
    fireEvent.click(screen.getByRole("tab", { name: /Rewrite/i }));
    fireEvent.click(screen.getByRole("button", { name: /Generate suggestion/i }));
    await waitFor(() => expect(mocks.localRewrite).toHaveBeenCalledWith(
      sample, 1, "natural",
      "C:\\Program Files\\Silabs\\model\\qwen3-1.7b.gguf", "This sentences",
    ));
    fireEvent.click(await screen.findByRole("button", { name: "Accept" }));
    expect(editor.value).toBe("These sentences is unclear.");
  });

  it("applies approved local grammar suggestion without any cloud call", async () => {
    mocks.localAnalyse.mockResolvedValue({
      language: "en", engine: "offline-rules-and-word-frequency", text_length: 26,
      limitations: "English-only, suggestive not exhaustive.",
      issues: [{
        category: "grammar", rule_id: "demonstrative-plural",
        title: "Grammar agreement", message: "Plural noun",
        start: 0, end: 14, original: "This sentences",
        replacements: ["These sentences"], confidence: "high",
      }],
    });
    render(<App />);
    await openDocument();
    fireEvent.click(screen.getByRole("tab", { name: "Grammar" }));
    expect(await screen.findByText("Grammar agreement")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /These sentences/i }));
    expect((screen.getByRole("textbox", { name: "Edit selected passage" }) as HTMLTextAreaElement).value)
      .toBe("These sentences is unclear.");
  });

  it("compares only explicitly selected local references and shows matched excerpt", async () => {
    render(<App />);
    await openDocument();
    mocks.openDialog.mockResolvedValueOnce(["C:\\tests\\reference.docx"]);
    fireEvent.click(screen.getByRole("tab", { name: "Sources" }));
    fireEvent.click(screen.getByRole("button", { name: /Select reference documents/i }));
    await waitFor(() => expect(mocks.localCompare).toHaveBeenCalledWith(
      sample, {}, ["C:\\tests\\reference.docx"],
    ));
    expect(await screen.findByText("reference.docx")).toBeTruthy();
    expect(screen.getByText(/Only user-selected files searched/i)).toBeTruthy();
  });

  it("keeps accepted changes when reopening is cancelled", async () => {
    render(<App />);
    await openDocument();
    fireEvent.click(screen.getByRole("tab", { name: /Rewrite/i }));
    fireEvent.click(screen.getByRole("button", { name: /Generate suggestion/i }));
    await screen.findByRole("button", { name: "Accept" });
    fireEvent.click(screen.getByRole("button", { name: "Accept" }));
    mocks.confirmDialog.mockResolvedValueOnce(false);
    fireEvent.click(screen.getByRole("button", { name: "Open another file" }));
    await waitFor(() => expect(mocks.confirmDialog).toHaveBeenCalled());
    expect(mocks.localOpen).toHaveBeenCalledTimes(1);
    expect(screen.getByText("1 accepted · 2 editable")).toBeTruthy();
  });
});
