import { useEffect, useMemo, useState } from "react";
import { Check, FileText, LockKeyhole, Search, X } from "lucide-react";
import type { OpenedDocument } from "../ipc";
import { canEditBlock } from "../editor/review";

type Props = {
  doc: OpenedDocument | null;
  selected: number | null;
  accepted: Record<number, string>;
  busy: boolean;
  onSelect: (index: number) => void;
};

export default function DocumentSidebar({ doc, selected, accepted, busy, onSelect }: Props) {
  const [query, setQuery] = useState("");
  useEffect(() => { setQuery(""); }, [doc?.path, doc?.fingerprint]);
  const blocks = useMemo(() => {
    if (!doc) return [];
    const term = query.trim().toLocaleLowerCase();
    return term
      ? doc.blocks.filter(block => block.text.toLocaleLowerCase().includes(term) ||
          block.style?.toLocaleLowerCase().includes(term))
      : doc.blocks;
  }, [doc, query]);

  return (
    <aside className="outline" aria-label="Document outline">
      <div className="outline-heading">
        <span className="overline">DOCUMENT</span>
        <h2>Outline</h2>
        <p>Choose a paragraph to review or rewrite.</p>
      </div>
      {doc ? (
        <>
          <div className="open-document" title={doc.path}>
            <span className="document-icon"><FileText size={20} /></span>
            <div className="document-details">
              <strong>{doc.name}</strong>
              <span>{doc.format.toUpperCase()} · {doc.blocks.length} blocks</span>
            </div>
          </div>
          <label className="outline-search">
            <Search size={16} aria-hidden="true" />
            <span className="sr-only">Find in document outline</span>
            <input value={query} onChange={e => setQuery(e.target.value)}
              placeholder="Find paragraph or heading..." autoComplete="off" />
            {query && <button type="button" aria-label="Clear search" onClick={() => setQuery("")}><X size={15} /></button>}
          </label>
          <div className="outline-meta">
            <span>{blocks.length} shown</span>
            <span>{Object.keys(accepted).length} accepted</span>
          </div>
          <nav className="outline-list" aria-label="Paragraphs and headings">
            {blocks.length ? blocks.map(block => {
              const readOnly = !canEditBlock(block);
              const heading = block.kind === "heading";
              return (
                <button key={block.index} type="button" disabled={busy}
                  aria-current={selected === block.index ? "true" : undefined}
                  onClick={() => onSelect(block.index)}
                  title={readOnly && !heading ? (block.reason || "Read-only structure") : block.text}
                  className={[
                    "outline-block", selected === block.index ? "is-active" : "",
                    heading ? "is-heading" : "", readOnly ? "is-readonly" : "",
                  ].filter(Boolean).join(" ")}>
                  <span className="outline-block-icon">
                    {block.index in accepted ? <Check size={15} /> :
                      readOnly && !heading ? <LockKeyhole size={14} /> : <FileText size={15} />}
                  </span>
                  <span className="outline-block-content">
                    <span className="outline-block-title">
                      {heading ? block.text || "Untitled heading" :
                        block.kind === "table_cell" ? "Table cell" : "Paragraph " + (block.index + 1)}
                    </span>
                    {!heading && <span className="outline-block-preview">{block.text.trim() || "Empty paragraph"}</span>}
                  </span>
                  {block.index in accepted && <span className="outline-accepted">Reviewed</span>}
                </button>
              );
            }) : (
              <div className="outline-no-match">No matching paragraphs. Try a shorter search.</div>
            )}
          </nav>
          <div className="outline-legend"><LockKeyhole size={14} /> Some formatted blocks are read-only to protect document structure.</div>
        </>
      ) : (
        <div className="outline-empty">
          <FileText size={32} strokeWidth={1.5} />
          <strong>No document open</strong>
          <p>Your document outline will appear here.</p>
        </div>
      )}
      <div className="outline-foot"><span className="local-dot" /> Private, on-device processing</div>
    </aside>
  );
}
