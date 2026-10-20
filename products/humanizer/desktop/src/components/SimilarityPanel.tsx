import { AlertTriangle, FileSearch, FolderOpen, LockKeyhole, ShieldCheck } from "lucide-react";
import type { LocalSimilarityReport } from "../ipc";

type Props = {
  report: LocalSimilarityReport | null;
  busy: boolean;
  onCompare: () => void;
};

export default function SimilarityPanel({ report, busy, onCompare }: Props) {
  return (
    <section className="assistant-section" aria-label="Local source similarity">
      <div className="assistant-section-heading">
        <strong><FileSearch size={16} /> Source similarity</strong><span>Selected files only</span>
      </div>
      <p className="assistant-hint-text">
        Check whether your document shares passages with DOCX, TXT or Markdown
        files that you explicitly select on this computer.
      </p>
      <button className="button button-primary generate-action" type="button"
        disabled={busy} onClick={onCompare}>
        <FolderOpen size={16} />
        {busy ? "Comparing…" : "Select reference documents"}
      </button>
      <div className="similarity-privacy"><LockKeyhole size={15} />
        No cloud service, uploads, internet search, or automatic folder scanning.
      </div>
      {report && (
        <div className="similarity-results" role="status">
          {report.status === "too-short" ? (
            <div className="assistant-warning">{report.explanation}</div>
          ) : (
            <>
              <div className="similarity-score">
                <strong>{report.coverage_percent}%</strong>
                <span>Exact-sequence coverage across {report.source_count} selected local files</span>
              </div>
              <p className="similarity-explainer">{report.explanation}</p>
              {report.sources.length === 0 ? (
                <div className="writing-clean"><ShieldCheck size={18} />
                  <strong>No 8-word exact matches found in the selected files.</strong>
                  <p>This does not establish originality or rule out paraphrasing.</p>
                </div>
              ) : report.sources.map((source, idx) => (
                <article className="hint-card" key={source.name + idx}>
                  <div className="hint-type">Reference document</div>
                  <strong>{source.name}</strong>
                  <p>{source.matched_words} matched words · {source.draft_coverage_percent}% of draft</p>
                  {source.match_excerpts.map((match, i) => (
                    <div key={i} className="source-match">
                      <span>Your text</span><p>{match.draft_excerpt}</p>
                      <span>Reference text</span><p>{match.source_excerpt}</p>
                    </div>
                  ))}
                </article>
              ))}
            </>
          )}
          <p className="similarity-warning"><AlertTriangle size={14} />
            Matching text is not proof of plagiarism. Review legitimate quotes,
            citations and commonly used phrases yourself.</p>
        </div>
      )}
    </section>
  );
}
