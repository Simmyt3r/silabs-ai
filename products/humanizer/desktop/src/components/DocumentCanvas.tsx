import { useEffect, useRef, useState } from "react";
import { FileText, PencilLine, ShieldCheck } from "lucide-react";
import type { Block, OpenedDocument } from "../ipc";

type Props = {
  doc: OpenedDocument;
  selected: number | null;
  accepted: Record<number, string>;
  busy: boolean;
  onSelect: (index: number) => void;
  onEdit: (text: string) => void;
  onSelection: (start: number, end: number) => void;
};

const CHUNK = 150;

export default function DocumentCanvas({
  doc, selected, accepted, busy, onSelect, onEdit, onSelection,
}: Props) {
  const [limit, setLimit] = useState(CHUNK);
  const focusRef = useRef<HTMLTextAreaElement | null>(null);
  const scrollRoot = useRef<HTMLDivElement | null>(null);
  useEffect(() => { setLimit(CHUNK); }, [doc.path, doc.fingerprint]);
  useEffect(() => {
    const idx = doc.blocks.findIndex(block => block.index === selected);
    if (idx >= limit) setLimit(Math.min(doc.blocks.length, idx + 25));
  }, [selected, doc, limit]);
  useEffect(() => {
    if (selected === null) return;
    const active = scrollRoot.current?.querySelector('[data-block-index="' + selected + '"]');
    active?.scrollIntoView({ block: "nearest", behavior: "auto" });
  }, [selected, limit]);

  return (
    <section className="document-stage" aria-label="Document editor">
      <header className="document-stage-header">
        <div className="document-stage-title"><FileText size={18} />
          <div><strong>{doc.name}</strong><small>Editable working copy · original preserved</small></div>
        </div>
        <span className="document-stage-count">{doc.blocks.length} blocks</span>
      </header>
      <div className="document-scroll" ref={scrollRoot}>
        <div className="document-paper">
          <div className="document-paper-label"><PencilLine size={14} /> Your document</div>
          {doc.blocks.slice(0, limit).map(block => {
            const current = accepted[block.index] ?? block.text;
            const active = selected === block.index;
            const editable = block.editable;
            const heading = block.kind === "heading" || /^Heading/.test(block.style ?? "");
            return (
              <div className={"editor-block " + (active ? "editor-block-active " : "") +
                (heading ? "editor-block-heading " : "")}
                data-block-index={block.index} key={block.index}>
                <span className="editor-block-marker" aria-hidden="true">
                  {block.index in accepted ? "●" : ""}
                </span>
                {active && editable ? (
                  <div className="editor-input-wrap">
                    <label className="sr-only" htmlFor="paragraph-editor">Edit selected passage</label>
                    <textarea id="paragraph-editor" ref={focusRef}
                      aria-label="Edit selected passage"
                      className={"editor-textarea " + (heading ? "editor-textarea-heading" : "")}
                      spellCheck
                      disabled={busy}
                      rows={Math.max(3, Math.min(20, Math.ceil(current.length / 80) + 1))}
                      value={current}
                      onChange={e => onEdit(e.target.value)}
                      onSelect={e => {
                        const el = e.currentTarget;
                        onSelection(el.selectionStart, el.selectionEnd);
                      }}
                    />
                    <span className="editor-active-tip">
                      {block.index in accepted ? "Edited in working copy" : "Editing this passage"}
                      · Select text to improve only that selection
                    </span>
                  </div>
                ) : (
                  <button type="button" className="editor-paragraph" onClick={() => onSelect(block.index)}
                    disabled={busy} aria-label={"Select " + (heading ? "heading" : "paragraph") + " " + (block.index + 1)}
                    title={editable ? "Click to edit this passage" : (block.reason ?? "Structured content is preserved")}>
                    <span className={heading ? "paper-heading-text" : "paper-body-text"}>{current || " "}</span>
                  </button>
                )}
                {active && !editable && (
                  <div className="protected-block-note"><ShieldCheck size={15} />
                    This structure is preview-only for now. Its original content and formatting will be preserved.
                  </div>
                )}
              </div>
            );
          })}
          {doc.blocks.length > limit && (
            <button type="button" className="document-load-more"
              onClick={() => setLimit(n => Math.min(doc.blocks.length, n + CHUNK))}>
              Show more of the document ({doc.blocks.length - limit} remaining)
            </button>
          )}
        </div>
      </div>
      <footer className="document-stage-footer">
        <ShieldCheck size={15} /> Edits remain in this working copy until you export a new file.
      </footer>
    </section>
  );
}
