import { useMemo } from "react";
import {
  AlertCircle, ArrowRight, Check, ChevronRight, Clock3, FileCheck2,
  FileText, LockKeyhole, RotateCcw, ShieldCheck, Sparkles, WandSparkles, X,
} from "lucide-react";
import type { RewriteMode, RewriteProposal, Block } from "../ipc";
import { MODES } from "../editor/modes";
import { compareText, type DiffPart } from "../editor/diff";
import { canEditBlock, wordCount } from "../editor/review";

type Props = {
  activeBlock: Block | null;
  mode: RewriteMode;
  proposal: RewriteProposal | null;
  accepted: Record<number, string>;
  modelReady: boolean;
  busy: boolean;
  rewriting: boolean;
  canRewrite: boolean;
  onMode: (mode: RewriteMode) => void;
  onRewrite: () => void;
  onAccept: () => void;
  onReject: () => void;
  onRestore: () => void;
  onShowSettings: () => void;
};

function DiffText({ parts, direction }: { parts: DiffPart[]; direction: "before" | "after" }) {
  return (
    <p className="comparison-text">
      {parts.map((piece, index) => piece.changed ? (
        <mark key={index} className={direction === "before" ? "diff-removed" : "diff-added"}>{piece.text}</mark>
      ) : <span key={index}>{piece.text}</span>)}
    </p>
  );
}

export default function ReviewWorkspace({
  activeBlock, mode, proposal, accepted, modelReady, busy, rewriting, canRewrite,
  onMode, onRewrite, onAccept, onReject, onRestore, onShowSettings,
}: Props) {
  const acceptedText = activeBlock ? accepted[activeBlock.index] : undefined;
  const showingProposal = !!proposal && proposal.index === activeBlock?.index;
  const revisedText = showingProposal ? (proposal?.passed ? proposal.proposal : null) : acceptedText ?? null;
  const hasRevision = revisedText !== null;
  const diff = useMemo(() => compareText(activeBlock?.text ?? "", revisedText ?? ""), [activeBlock?.text, revisedText]);
  const modeName = MODES.find(item => item.id === mode) ?? MODES[0];
  const editable = canEditBlock(activeBlock);

  return (
    <div className="editing-flow">
      <section className="selected-block" aria-labelledby="selection-title">
        <div className="step-heading">
          <div className="step-symbol">1</div>
          <div>
            <span className="overline">SELECT</span>
            <h2 id="selection-title">Current paragraph</h2>
          </div>
        </div>
        <div className="selected-summary">
          <div className="selected-info">
            <FileText size={17} />
            <span>{activeBlock ? (activeBlock.kind === "heading" ? "Heading" :
              activeBlock.kind === "table_cell" ? "Table cell" : "Paragraph " + (activeBlock.index + 1)) : "No paragraph selected"}</span>
            {activeBlock && <span className="muted-inline">· {wordCount(activeBlock.text)} words</span>}
          </div>
          <span className={"editability " + (editable ? "editable" : "readonly")}>
            {editable ? <Check size={14} /> : <LockKeyhole size={14} />}
            {editable ? "Editable" : "Read-only"}
          </span>
        </div>
        {!editable && activeBlock && (
          <p className="inline-explanation">
            {activeBlock.kind === "heading"
              ? "Headings are preserved in this preview. Select a body paragraph to rewrite."
              : (activeBlock.reason || "Complex formatting is protected to avoid altering your document.")}
          </p>
        )}
      </section>

      <section className="rewrite-card" aria-labelledby="rewrite-title">
        <div className="step-heading">
          <div className="step-symbol">2</div>
          <div>
            <span className="overline">REFINE</span>
            <h2 id="rewrite-title">Choose a writing style</h2>
          </div>
        </div>
        <div className="mode-options" role="group" aria-label="Rewrite style">
          {MODES.map(item => (
            <button type="button" key={item.id} aria-pressed={mode === item.id}
              disabled={busy} title={item.detail}
              className={"mode-option " + (mode === item.id ? "is-selected" : "")}
              onClick={() => onMode(item.id)}>
              {mode === item.id ? <Check size={15} /> : <WandSparkles size={15} />}
              {item.label}
            </button>
          ))}
        </div>
        <div className="rewrite-footer">
          <div className="mode-description">
            <span className="mode-description-title">{modeName.label}</span>
            <span>{modeName.detail}</span>
          </div>
          <button type="button" className="button button-primary rewrite-button"
            onClick={onRewrite} disabled={!canRewrite} aria-busy={rewriting}>
            <Sparkles size={16} />
            {rewriting ? "Rewriting locally…" : "Generate suggestion"}
            {!rewriting && <ArrowRight size={16} />}
          </button>
        </div>
        {!modelReady && (
          <button type="button" className="model-help" onClick={onShowSettings}>
            <AlertCircle size={15} /> Select a local model before rewriting <ChevronRight size={15} />
          </button>
        )}
        {acceptedText !== undefined && (
          <div className="mode-note">
            <ShieldCheck size={15} /> Generating again uses the original paragraph. Your accepted revision stays until replaced.
          </div>
        )}
      </section>

      <section className="review-section" aria-labelledby="review-title">
        <div className="review-titlebar">
          <div className="step-heading">
            <div className="step-symbol">3</div>
            <div>
              <span className="overline">REVIEW</span>
              <h2 id="review-title">Compare and decide</h2>
            </div>
          </div>
          <span className="review-state">
            {showingProposal && proposal?.passed ? "Suggestion needs your approval" :
              acceptedText !== undefined ? "Revision accepted" : "No change proposed yet"}
          </span>
        </div>
        <div className="compare-grid">
          <article className="paper-card" aria-label="Original passage">
            <div className="paper-heading">
              <span><span className="paper-dot original" /> Original</span>
              <span>{wordCount(activeBlock?.text ?? "")} words</span>
            </div>
            <div className="paper-content">
              {activeBlock?.text ? (
                hasRevision ? <DiffText parts={diff.before} direction="before" /> :
                  <p className="comparison-text">{activeBlock.text}</p>
              ) : <p className="empty-paper">Select a paragraph from the outline.</p>}
            </div>
          </article>
          <article className="paper-card paper-revision" aria-label="Revised passage">
            <div className="paper-heading">
              <span><span className="paper-dot proposed" />
                {showingProposal ? "Suggestion" : acceptedText !== undefined ? "Accepted wording" : "Revision"}
              </span>
              <span>{hasRevision ? wordCount(revisedText) + " words" : "Awaiting suggestion"}</span>
            </div>
            <div className="paper-content">
              {showingProposal && !proposal?.passed ? (
                <div className="blocked-proposal">
                  <AlertCircle size={22} />
                  <strong>Suggestion blocked</strong>
                  <p>{proposal?.issues.join(". ") || "The protection check failed."}</p>
                </div>
              ) : hasRevision ? <DiffText parts={diff.after} direction="after" /> :
                <div className="empty-proposal">
                  <WandSparkles size={25} />
                  <strong>Your suggested rewrite will appear here.</strong>
                  <span>Nothing changes until you explicitly accept it.</span>
                </div>}
            </div>
          </article>
        </div>
        <div className="review-toolbar">
          <div className="review-caption">
            {showingProposal && proposal?.passed ? (
              <><Clock3 size={15} /> Generated in {proposal.elapsed_seconds}s. Check accuracy before accepting.</>
            ) : (
              <><ShieldCheck size={16} /> Citations and numbers are checked; meaning still requires your review.</>
            )}
          </div>
          <div className="review-buttons">
            {acceptedText !== undefined && !showingProposal && (
              <button type="button" className="button button-secondary" disabled={busy} onClick={onRestore}>
                <RotateCcw size={15} /> Restore original
              </button>
            )}
            {showingProposal && (
              <>
                <button type="button" className="button button-secondary" disabled={busy} onClick={onReject}>
                  <X size={16} /> Reject
                </button>
                <button type="button" className="button button-accept" disabled={busy || !proposal?.passed} onClick={onAccept}>
                  <Check size={16} /> Accept revision
                </button>
              </>
            )}
          </div>
        </div>
      </section>
      <div className="editor-assurance"><FileCheck2 size={18} />
        <span>Original file preserved. Export creates a separate revised document after you accept changes.</span>
      </div>
    </div>
  );
}
