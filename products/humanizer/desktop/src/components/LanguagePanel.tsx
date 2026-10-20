import { AlertTriangle, BookCheck, Check, ShieldCheck, SpellCheck2 } from "lucide-react";
import type { OfflineAnalysis, OfflineIssue } from "../ipc";

type Props = {
  text: string;
  analysis: OfflineAnalysis | null;
  pending: boolean;
  error: string | null;
  editable: boolean;
  busy: boolean;
  onEdit: (text: string) => void;
};

export default function LanguagePanel({
  text, analysis, pending, error, editable, busy, onEdit,
}: Props) {
  const issues = analysis?.text_length === text.length ? analysis.issues : [];
  const grammar = issues.filter(x => x.category === "grammar").length;
  const spelling = issues.filter(x => x.category === "spelling").length;
  function apply(issue: OfflineIssue, replacement: string) {
    if (issue.start < 0 || issue.end > text.length ||
      text.slice(issue.start, issue.end) !== issue.original) return;
    onEdit(text.slice(0, issue.start) + replacement + text.slice(issue.end));
  }

  return (
    <section className="assistant-section" aria-label="Offline grammar and spelling">
      <div className="assistant-section-heading">
        <strong><SpellCheck2 size={16} /> Grammar & spelling</strong>
        <span>English · offline</span>
      </div>
      {pending && <p className="language-pending" role="status">Checking the selected passage locally…</p>}
      {error && <div className="assistant-warning" role="alert"><AlertTriangle size={16} /> {error}</div>}
      {analysis && (
        <>
          <div className="language-counts">
            <span><BookCheck size={15} /> {grammar} grammar</span>
            <span><SpellCheck2 size={15} /> {spelling} spelling</span>
          </div>
          {issues.length === 0 && (
            <div className="writing-clean"><Check size={20} />
              <strong>No issues found by the installed local checker.</strong>
              <p>This is not proof that the passage is error-free. Technical names and uncommon words may require manual review.</p>
            </div>
          )}
          {issues.map(issue => (
            <article className="hint-card" key={issue.rule_id + ":" + issue.start + ":" + issue.end}>
              <div className="hint-type">{issue.category} · {issue.confidence} confidence</div>
              <strong>{issue.title}</strong>
              <p>{issue.message}</p>
              <div className="language-original">In text: <strong>{issue.original}</strong></div>
              <div className="language-options" aria-label={"Suggestions for " + issue.original}>
                {issue.replacements.map(suggestion =>
                  <button key={suggestion} type="button" className="hint-apply"
                    disabled={busy || !editable}
                    onClick={() => apply(issue, suggestion)}>
                    <Check size={14} /> {suggestion}
                  </button>
                )}
              </div>
            </article>
          ))}
          <div className="language-disclaimer"><ShieldCheck size={15} />
            {analysis.limitations} Suggestions change nothing until you select one.
          </div>
        </>
      )}
    </section>
  );
}
