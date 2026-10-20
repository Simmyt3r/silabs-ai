import { useMemo, useState } from "react";
import {
  AlertCircle, BookOpenCheck, Check, CheckCircle2, ChevronDown,
  Clock3, Lightbulb, RotateCcw, ShieldCheck, Sparkles, WandSparkles, X,
} from "lucide-react";
import type { RewriteMode, RewriteProposal, Block, OfflineAnalysis, LocalSimilarityReport } from "../ipc";
import LanguagePanel from "./LanguagePanel";
import SimilarityPanel from "./SimilarityPanel";
import { MODES } from "../editor/modes";
import { inspectWriting, applyWritingHint } from "../editor/writingHints";
import { compareText } from "../editor/diff";

type Props = {
  activeBlock: Block | null;
  workingText: string;
  previewText: string | null;
  selection: { start: number; end: number } | null;
  proposal: RewriteProposal | null;
  mode: RewriteMode;
  accepted: Record<number, string>;
  modelReady: boolean;
  analysis: OfflineAnalysis | null;
  analysisError: string | null;
  analysisPending: boolean;
  sourceReport: LocalSimilarityReport | null;
  busy: boolean;
  compareBusy: boolean;
  canRewrite: boolean;
  onMode: (mode: RewriteMode) => void;
  onRewrite: () => void;
  onAccept: () => void;
  onReject: () => void;
  onRestore: () => void;
  onEdit: (text: string) => void;
  onShowSettings: () => void;
  onCompareSources: () => void;
};

export default function WritingAssistant({
  activeBlock, workingText, previewText, selection, proposal, mode, accepted,
  modelReady, analysis, analysisError, analysisPending, sourceReport,
  busy, compareBusy, canRewrite, onMode, onRewrite, onAccept,
  onReject, onRestore, onEdit, onShowSettings, onCompareSources,
}: Props) {
  const [tab, setTab] = useState<"suggestions" | "language" | "rewrite" | "sources">("suggestions");
  const hints = useMemo(() => inspectWriting(workingText), [workingText]);
  const proposalActive = !!proposal && proposal.index === activeBlock?.index;
  const diff = useMemo(
    () => compareText(workingText, previewText ?? workingText),
    [workingText, previewText],
  );
  const acceptedText = activeBlock && activeBlock.index in accepted;
  const quickCount = hints.filter(h => h.type === "correctness").length;
  const clarityCount = hints.length - quickCount;

  return (
    <aside className="writing-assistant" aria-label="Writing assistant">
      <header className="assistant-header">
        <div><span className="assistant-symbol"><Sparkles size={18} /></span>
          <div><strong>Writing assistant</strong><small>Private · available offline</small></div>
        </div>
        <span className="assistant-issues">{hints.length} hints</span>
      </header>
      <div className="assistant-tabs" role="tablist" aria-label="Writing tools">
        <button type="button" role="tab" aria-selected={tab === "suggestions"}
          className={tab === "suggestions" ? "is-selected" : ""}
          onClick={() => setTab("suggestions")}>
          <Lightbulb size={15} /> Suggestions
        </button>
        <button type="button" role="tab" aria-selected={tab === "language"}
          className={tab === "language" ? "is-selected" : ""}
          onClick={() => setTab("language")}>
          Grammar
        </button>
        <button type="button" role="tab" aria-selected={tab === "rewrite"}
          className={tab === "rewrite" ? "is-selected" : ""}
          onClick={() => setTab("rewrite")}>
          <WandSparkles size={15} /> Rewrite
        </button>
        <button type="button" role="tab" aria-selected={tab === "sources"}
          className={tab === "sources" ? "is-selected" : ""}
          onClick={() => setTab("sources")}>
          Sources
        </button>
      </div>
      <div className="assistant-scroll">
        {!activeBlock ? (
          <div className="assistant-empty"><BookOpenCheck size={25} />
            Select any passage in your document to start editing.</div>
        ) : (
          <>
            <div className="writing-overview">
              <span className="writing-meta">SELECTED PASSAGE</span>
              <strong>{activeBlock.kind === "heading" ? "Heading" :
                activeBlock.kind === "table_cell" ? "Table cell" : "Paragraph " + (activeBlock.index + 1)}</strong>
              <p>{workingText.trim().split(/\s+/).filter(Boolean).length} words · {quickCount} correctness · {clarityCount} clarity</p>
              {!activeBlock.editable && (
                <div className="assistant-warning"><ShieldCheck size={15} />
                  This passage contains protected document structure.</div>
              )}
            </div>

            {tab === "suggestions" && (
              <section className="assistant-section" aria-label="Instant writing hints">
                <div className="assistant-section-heading">
                  <strong>Instant checks</strong><span>No AI wait</span>
                </div>
                {hints.length === 0 ? (
                  <div className="writing-clean"><CheckCircle2 size={22} />
                    <strong>No common mechanical issues found.</strong>
                    <p>These quick checks cover spacing, repeated words and long sentences. They do not certify grammar or factual accuracy.</p>
                  </div>
                ) : hints.map(hint => (
                  <article key={hint.id} className="hint-card">
                    <div className="hint-type">{hint.type === "correctness" ? "Correctness" : "Clarity"}</div>
                    <strong>{hint.title}</strong>
                    <p>{hint.explanation}</p>
                    {hint.replacement !== workingText.slice(hint.start, hint.end) ? (
                      <button type="button" className="hint-apply" disabled={busy || !activeBlock.editable}
                        onClick={() => onEdit(applyWritingHint(workingText, hint))}>
                        <Check size={14} /> Apply correction
                      </button>
                    ) : <small>Consider revising this sentence manually.</small>}
                  </article>
                ))}
                <button type="button" className="assistant-switch" onClick={() => setTab("rewrite")}>
                  <Sparkles size={15} /> Improve style or tone with local AI
                </button>
              </section>
            )}

            {tab === "language" && (
              <LanguagePanel text={workingText} analysis={analysis}
                pending={analysisPending} error={analysisError}
                busy={busy} editable={activeBlock.editable} onEdit={onEdit}
                onDeepGrammar={() => { onMode("grammar"); setTab("rewrite"); }} />
            )}
            {tab === "sources" && (
              <SimilarityPanel report={sourceReport}
                busy={compareBusy} onCompare={onCompareSources} />
            )}

            {tab === "rewrite" && (
              <section className="assistant-section" aria-label="AI rewriting options">
                <div className="assistant-section-heading">
                  <strong>Improve your writing</strong><span>Local Qwen</span>
                </div>
                <p className="assistant-hint-text">
                  {selection ? "Selected text only will be rewritten." :
                    "Select words in the editor to rewrite just those words, or improve the full passage."}
                </p>
                <label className="rewrite-mode-label" htmlFor="rewrite-mode">Writing goal</label>
                <div className="rewrite-mode-field">
                  <select id="rewrite-mode" value={mode} disabled={busy} onChange={e => onMode(e.target.value as RewriteMode)}>
                    {MODES.map(m => <option value={m.id} key={m.id}>{m.label}</option>)}
                  </select>
                  <ChevronDown size={16} aria-hidden="true" />
                </div>
                <p className="mode-guidance">{MODES.find(m => m.id === mode)?.detail}</p>
                <button type="button" className="button button-primary generate-action"
                  disabled={!canRewrite} onClick={onRewrite}>
                  <Sparkles size={17} /> {busy ? "Working locally…" : "Generate suggestion"}
                </button>
                {!modelReady && (
                  <button type="button" className="assistant-switch" onClick={onShowSettings}>
                    <AlertCircle size={14} /> Configure local GGUF model
                  </button>
                )}
                {busy && (
                  <p className="generation-notice" role="status"><Clock3 size={14} />
                    Running locally. The first result may take longer on older CPUs.</p>
                )}
              </section>
            )}

            {proposalActive && (
              <section className="proposal-card" aria-label="Rewriting result">
                <div className="assistant-section-heading">
                  <strong>{proposal?.passed ? "Review suggestion" : "Suggestion needs attention"}</strong>
                  <span>{proposal?.elapsed_seconds}s</span>
                </div>
                {!proposal?.passed ? (
                  <div className="assistant-warning">
                    <AlertCircle size={17} />
                    <span>{proposal?.issues.join(". ") || "Output did not pass review checks."} Try a shorter selection or another mode.</span>
                  </div>
                ) : previewText !== null ? (
                  <>
                    <p className="proposal-caption">Proposed wording compared with your current draft:</p>
                    <div className="proposal-comparison" role="article" aria-label="Revised passage">
                      {diff.after.map((part, i) => part.changed
                        ? <mark key={i}>{part.text}</mark> : <span key={i}>{part.text}</span>)}
                    </div>
                    <small>Automatic checks cannot guarantee meaning or source accuracy. Review before accepting.</small>
                  </>
                ) : null}
                <div className="proposal-actions">
                  <button type="button" className="button button-secondary" onClick={onReject} disabled={busy}><X size={15} /> Reject</button>
                  <button type="button" className="button button-accept" onClick={onAccept}
                    disabled={busy || !proposal?.passed || previewText === null}><Check size={15} /> Accept</button>
                </div>
              </section>
            )}
            {acceptedText && !proposalActive && (
              <div className="working-copy-notice">
                <CheckCircle2 size={16} /> This passage has changes in your working copy.
                <button type="button" disabled={busy} onClick={onRestore}><RotateCcw size={14} /> Restore original</button>
              </div>
            )}
          </>
        )}
      </div>
      <footer className="assistant-footer"><ShieldCheck size={15} />
        Nothing leaves your computer.</footer>
    </aside>
  );
}
