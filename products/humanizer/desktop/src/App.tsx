import { useEffect, useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import {
  AlertCircle, ArrowRight, BookOpen, Check, CheckCheck,
  ChevronRight, CircleCheck, Clock3, FileDown, FileText,
  FolderOpen, HardDrive, LockKeyhole, LoaderCircle,
  RotateCcw, Settings2, ShieldCheck, Sparkles, WandSparkles, X,
} from "lucide-react";
import { confirm, open, save } from "@tauri-apps/plugin-dialog";
import { Block, localApi, OpenedDocument, RewriteMode, RewriteProposal } from "./ipc";

const MODES: Array<{ id: RewriteMode; label: string; helper: string }> = [
  { id: "natural", label: "Humanize", helper: "Improve natural flow and rhythm" },
  { id: "academic", label: "Academic", helper: "Clear, credible academic writing" },
  { id: "grammar", label: "Grammar", helper: "Correct errors without changing voice" },
  { id: "professional", label: "Professional", helper: "Polished and business-ready" },
  { id: "simplify", label: "Simplify", helper: "Make difficult ideas easy to follow" },
  { id: "shorten", label: "Shorten", helper: "Remove filler, preserve substance" },
  { id: "expand", label: "Expand", helper: "Improve explanations without new facts" },
];

function TextDiff({ before, after, variant }: { before: string; after: string; variant: "before" | "after" }) {
  let start = 0;
  while (start < before.length && start < after.length && before[start] === after[start]) start++;
  let suffix = 0;
  while (suffix < before.length - start && suffix < after.length - start &&
    before[before.length - suffix - 1] === after[after.length - suffix - 1]) suffix++;
  const value = variant === "before" ? before : after;
  return (
    <p className="comparison-text">{value.slice(0, start)}
      <mark className={variant}>{value.slice(start, value.length - suffix)}</mark>
      {value.slice(value.length - suffix)}
    </p>
  );
}

function BlockListItem({ block, active, accepted, onClick }: {
  block: Block; active: boolean; accepted: boolean; onClick: () => void;
}) {
  return (
    <button type="button" onClick={onClick}
      className={"document-block " + (active ? "active " : "") + (!block.editable ? "protected" : "")}
      title={block.reason ?? (block.editable ? "Select paragraph" : "Protected content")}>
      <span className="block-icon">
        {accepted ? <Check size={16} /> : block.kind === "heading" ? <BookOpen size={16} /> : <FileText size={16} />}
      </span>
      <span className="block-description">
        <span className="block-topline">{block.kind === "heading" ? "Heading" :
          block.kind === "table_cell" ? "Table cell" : "Paragraph " + (block.index + 1)}</span>
        <span className="block-snippet">{block.text.trim() || "Empty paragraph"}</span>
      </span>
      {active && <ChevronRight className="active-arrow" size={16} />}
    </button>
  );
}

export default function App() {
  const [doc, setDoc] = useState<OpenedDocument | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [mode, setMode] = useState<RewriteMode>("natural");
  const [modelPath, setModelPath] = useState("");
  const [bundledModel, setBundledModel] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [accepted, setAccepted] = useState<Record<number, string>>({});
  const [proposal, setProposal] = useState<RewriteProposal | null>(null);
  const [busy, setBusy] = useState<"open" | "rewrite" | "export" | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let active = true;
    invoke<{ packaged: boolean; model_path: string | null }>("runtime_info")
      .then(info => {
        if (!active) return;
        setBundledModel(info.packaged && Boolean(info.model_path));
        if (info.model_path) setModelPath(info.model_path);
        if (info.packaged && !info.model_path) {
          setError("The offline AI model is missing from this installation. Reinstall the full offline edition.");
        }
      })
      .catch(err => { if (active) setError("Cannot inspect offline runtime: " + String(err)); });
    return () => { active = false; };
  }, []);

  const activeBlock = useMemo(() => doc?.blocks.find(block => block.index === selected) ?? null, [doc, selected]);
  const currentMode = MODES.find(entry => entry.id === mode)!;
  const acceptedCount = Object.keys(accepted).length;
  const usableBlocks = doc?.blocks.filter(b => b.editable && b.kind !== "heading").length ?? 0;
  const canRewrite = Boolean(doc && activeBlock?.editable && activeBlock.kind !== "heading" && modelPath.trim() && !busy);
  const shownText = activeBlock ? (accepted[activeBlock.index] ?? activeBlock.text) : "";

  async function openDocument() {
    if (acceptedCount > 0) {
      const discard = await confirm("You have accepted revisions that have not been exported. Opening another document will discard them.", { title: "Unsaved revisions", kind: "warning" });
      if (!discard) return;
    }
    setError(""); setNotice("");
    try {
      const path = await open({ multiple: false, directory: false, filters: [
        { name: "Document", extensions: ["docx", "txt", "md"] },
      ] });
      if (typeof path !== "string") return;
      setBusy("open");
      const result = await localApi.open(path);
      setDoc(result);
      setSelected(result.blocks.find(b => b.editable && b.kind !== "heading")?.index ?? result.blocks[0]?.index ?? null);
      setAccepted({});
      setProposal(null);
      setNotice("Opened " + result.name + ". " + result.blocks.length + " blocks found.");
    } catch (err) { setError(String(err)); } finally { setBusy(null); }
  }

  async function chooseModel() {
    setError("");
    try {
      const path = await open({ multiple: false, directory: false, filters: [
        { name: "Local GGUF model", extensions: ["gguf"] },
      ] });
      if (typeof path === "string") {
        setModelPath(path);
        setNotice("Local model selected. No data will be uploaded.");
      }
    } catch (err) { setError(String(err)); }
  }

  async function rewrite() {
    if (!doc || selected === null || !modelPath || !canRewrite) return;
    setBusy("rewrite"); setError(""); setNotice(""); setProposal(null);
    try {
      const result = await localApi.rewrite(doc, selected, mode, modelPath);
      setProposal(result);
      if (!result.passed) {
        setError("The draft failed protection checks. Your original paragraph has not changed.");
      }
    } catch (err) { setError(String(err)); } finally { setBusy(null); }
  }

  function acceptProposal() {
    if (!proposal?.passed || !activeBlock || proposal.index !== activeBlock.index) return;
    setAccepted(prev => ({ ...prev, [activeBlock.index]: proposal.proposal }));
    setProposal(null);
    setNotice("Revision accepted locally. Export to create a new document.");
  }

  function discardAccepted() {
    if (selected === null) return;
    setAccepted(prev => {
      const next = { ...prev };
      delete next[selected];
      return next;
    });
    setProposal(null);
    setNotice("Restored original paragraph in the working copy.");
  }

  async function exportDocument() {
    if (!doc || acceptedCount === 0) return;
    setError(""); setNotice("");
    try {
      const suffix = "." + doc.format;
      const suggestion = doc.name.endsWith(suffix)
        ? doc.name.slice(0, -suffix.length) + "-humanized" + suffix : doc.name + "-humanized";
      const destination = await save({ defaultPath: suggestion,
        filters: [{ name: "Revised document", extensions: [doc.format] }] });
      if (!destination) return;
      setBusy("export");
      const result = await localApi.export(doc, destination, accepted);
      setNotice("Saved " + result.revised_count + " accepted edits to " + result.destination);
    } catch (err) { setError(String(err)); } finally { setBusy(null); }
  }

  return (
    <div className="app-shell">
      <header className="top-bar">
        <div className="brand">
          <div className="brand-mark"><WandSparkles size={23} strokeWidth={2.25} /></div>
          <div className="brand-copy"><strong>Silabs<span>Humanizer</span></strong><small>Offline writing studio</small></div>
          <span className="beta-tag">Preview</span>
        </div>
        <div className="top-actions">
          <span className="offline-status"><span className="status-dot" /> 100% local processing</span>
          <button className="subtle-button" type="button" onClick={() => setSettingsOpen(value => !value)}>
            <Settings2 size={16} /> Model settings
          </button>
          <button className="primary-button" type="button" disabled={!!busy} onClick={openDocument}>
            {busy === "open" ? <LoaderCircle size={17} className="spin" /> : <FolderOpen size={17} />} Open document
          </button>
        </div>
      </header>

      <div className="workspace">
        <aside className="sidebar">
          <div className="sidebar-heading">
            <span className="eyebrow">WORKSPACE</span>
            <h2>Document outline</h2>
            <p>Select a paragraph to edit.</p>
          </div>
          {doc ? (
            <>
              <div className="file-summary">
                <div className="file-icon"><FileText size={20} /></div>
                <div className="file-details">
                  <strong title={doc.path}>{doc.name}</strong>
                  <span>{doc.format.toUpperCase()} · {doc.blocks.length} blocks</span>
                </div>
              </div>
              <div className="sidebar-counter">
                <span>{usableBlocks} editable blocks</span>
                <span>{acceptedCount} accepted</span>
              </div>
              <nav className="block-list" aria-label="Document paragraphs">
                {doc.blocks.map(block => (
                  <BlockListItem key={block.index} block={block}
                    active={selected === block.index} accepted={block.index in accepted}
                    onClick={() => { if (busy) return; setSelected(block.index); setProposal(null); setError(""); }} />
                ))}
              </nav>
            </>
          ) : (
            <div className="sidebar-empty">
              <FileText size={32} /><strong>No document yet</strong>
              <span>Open a DOCX, Markdown or text file to begin.</span>
            </div>
          )}
          <div className="sidebar-footer"><LockKeyhole size={16} /><span>No cloud. No account. Your files stay here.</span></div>
        </aside>

        <main className="main-panel">
          {settingsOpen && (
            <section className="settings-panel" aria-label="Local model settings">
              <div><span className="eyebrow">LOCAL INFERENCE</span><h3>Qwen3 GGUF model</h3>
                <p>The full offline edition includes Qwen locally. You can also select a compatible GGUF stored on this PC.</p></div>
              <div className="settings-controls">
                <div className="model-path" title={modelPath}>{bundledModel ? "Bundled Qwen3-1.7B (offline)" : (modelPath || "No model selected")}</div>
                <button className="outline-button" type="button" onClick={chooseModel}>
                  <HardDrive size={16} /> Choose GGUF</button>
              </div>
            </section>
          )}
          <div className="heading-row">
            <div>
              <div className="eyebrow">EDITOR / {doc?.name ?? "WELCOME"}</div>
              <h1>{doc ? "Refine your writing" : "Writing, made more human."}</h1>
              <p className="intro">Thoughtful rewrites, clear comparisons, and full control over every change.</p>
            </div>
            <div className="heading-actions">
              {doc && acceptedCount > 0 &&
                <button className="export-button" type="button" onClick={exportDocument} disabled={!!busy}>
                  {busy === "export" ? <LoaderCircle size={16} className="spin" /> : <FileDown size={16} />}
                  Export {acceptedCount} {acceptedCount === 1 ? "revision" : "revisions"}
                </button>}
            </div>
          </div>
          {error && <div className="error-banner" role="alert">
            <AlertCircle size={18} /><span>{error}</span>
            <button type="button" aria-label="Dismiss error" onClick={() => setError("")}><X size={18} /></button>
          </div>}
          {notice && <div className="notice" role="status"><CircleCheck size={17} /> {notice}
            <button type="button" aria-label="Dismiss notice" onClick={() => setNotice("")}><X size={16} /></button>
          </div>}

          {!doc ? (
            <section className="welcome">
              <div className="welcome-icon"><Sparkles size={28} /></div>
              <span className="welcome-eyebrow">WELCOME TO YOUR PRIVATE WORKSPACE</span>
              <h2>Better writing starts<br />with your own words.</h2>
              <p>Open a document, choose a passage, and let your local AI propose an improvement. You decide what stays.</p>
              <button type="button" className="primary-button large" onClick={openDocument}>
                <FolderOpen size={18} /> Choose a document <ArrowRight size={18} /></button>
              <div className="welcome-features">
                <span><ShieldCheck size={16} /> Facts protected</span>
                <span><LockKeyhole size={16} /> Offline by design</span>
                <span><CheckCheck size={16} /> Review every edit</span>
              </div>
            </section>
          ) : (
            <>
              <div className="mode-section">
                <div className="section-bar"><div><Sparkles size={17} /><strong>Rewrite tools</strong></div>
                  <span>Choose how to improve this paragraph</span></div>
                <div className="mode-grid">
                  {MODES.map(item => <button key={item.id} type="button" title={item.helper}
                    className={"mode-chip " + (mode === item.id ? "selected" : "")}
                    onClick={() => { if (busy) return; setMode(item.id); setProposal(null); }}>
                    {mode === item.id ? <CircleCheck size={16} /> : <WandSparkles size={16} />}
                    {item.label}
                  </button>)}
                </div>
                <div className="mode-bottom">
                  <span>{currentMode.helper}</span>
                  <button className="run-button" type="button" disabled={!canRewrite} onClick={rewrite}>
                    {busy === "rewrite" ? <LoaderCircle size={17} className="spin" /> : <Sparkles size={17} />}
                    {busy === "rewrite" ? "Rewriting locally…" : "Run " + currentMode.label}
                    {!busy && <ArrowRight size={16} />}
                  </button>
                </div>
                {!modelPath && <button className="model-nudge" type="button" onClick={() => setSettingsOpen(true)}>
                  <AlertCircle size={15} /> Select your local GGUF model in Model settings to enable rewriting.
                </button>}
              </div>
              <div className="section-bar compare-heading">
                <div><BookOpen size={17} /><strong>Review changes</strong></div>
                <span>Paragraph {selected === null ? "—" : selected + 1} · {activeBlock?.style || "Normal"}</span>
              </div>
              <div className="comparison">
                <div className="comparison-card">
                  <div className="comparison-header"><span className="dot dark-dot" /> Original
                    <span className="small-muted">{activeBlock?.text.length ?? 0} chars</span></div>
                  {activeBlock?.text ? (
                    <div className="comparison-body">
                      {proposal?.passed && proposal.index === selected ?
                        <TextDiff before={activeBlock.text} after={proposal.proposal} variant="before" /> :
                        <p className="comparison-text">{activeBlock.text}</p>}
                    </div>
                  ) : <div className="comparison-placeholder">Select a paragraph from the left to preview it.</div>}
                </div>
                <div className="comparison-card revised">
                  <div className="comparison-header"><span className="dot green-dot" />
                    {proposal ? "Proposed revision" : selected !== null && selected in accepted ? "Accepted revision" : "Your revision"}
                    <span className="small-muted">{proposal?.elapsed_seconds ?
                      <><Clock3 size={13} /> {proposal.elapsed_seconds}s</> : "Local AI"}</span>
                  </div>
                  <div className="comparison-body">
                    {proposal && proposal.index === selected ?
                      proposal.passed ?
                        <TextDiff before={activeBlock?.text ?? ""} after={proposal.proposal} variant="after" /> :
                        <div className="review-failed"><AlertCircle size={21} /><strong>Proposal blocked</strong>
                          <p>{proposal.issues.join("; ")}</p></div> :
                      selected !== null && selected in accepted ? <p className="comparison-text">{shownText}</p> :
                      <div className="comparison-placeholder">
                        <WandSparkles size={28} /><strong>Your improved text appears here</strong>
                        <span>Select a rewriting mode and run it to compare.</span>
                      </div>}
                  </div>
                </div>
              </div>
              <div className="review-actions">
                <span className="review-hint">
                  {activeBlock && !activeBlock.editable ?
                    <><LockKeyhole size={16} /> Protected formatting: this block cannot be edited safely yet.</> :
                    <><ShieldCheck size={16} /> Changes are suggestions. Check meaning, sources and quotations before accepting.</>}
                </span>
                <div className="action-buttons">
                  {selected !== null && selected in accepted && !proposal &&
                    <button className="outline-button" type="button" onClick={discardAccepted}>
                      <RotateCcw size={16} /> Restore original</button>}
                  {proposal && <>
                    <button className="outline-button" type="button" onClick={() => setProposal(null)}>
                      <X size={16} /> Reject</button>
                    <button className="accept-button" type="button" disabled={!proposal.passed} onClick={acceptProposal}>
                      <Check size={16} /> Accept revision</button>
                  </>}
                </div>
              </div>
              <section className="tips">
                <div className="tip-icon"><ShieldCheck size={21} /></div>
                <div><strong>Your document stays yours.</strong>
                  <p>We propose changes paragraph by paragraph. The original file is never overwritten, and all inference happens on your device.</p>
                </div>
              </section>
            </>
          )}
        </main>
      </div>
      <footer className="bottom-bar"><span><span className="tiny-dot" /> Offline workspace</span>
        <span>Silabs Humanizer v0.1 engineering preview <span className="separator">·</span>
          <span className="footer-private">Made for careful writing.</span>
        </span>
      </footer>
    </div>
  );
}
