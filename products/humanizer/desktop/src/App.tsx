import { useEffect } from "react";
import { getWorkspaceShortcut } from "./editor/hotkeys";
import {
  AlertCircle, CheckCircle2, FileDown, FileText, FolderOpen, HardDrive,
  LoaderCircle, LockKeyhole, Settings2, ShieldCheck, Sparkles, WandSparkles, X,
} from "lucide-react";
import DocumentSidebar from "./components/DocumentSidebar";
import DocumentCanvas from "./components/DocumentCanvas";
import WritingAssistant from "./components/WritingAssistant";
import { useDocumentWorkspace } from "./editor/useDocumentWorkspace";

export default function App() {
  const workspace = useDocumentWorkspace();
  const {
    doc, selected, activeBlock, mode, modelPath, bundledModel, settingsOpen, diagnostics,
    analysis, analysisError, analysisPending, sourceReport,
    accepted, acceptedCount, proposal, previewText, workingText, selection, busy, status, editables,
    hasUnexportedChanges, canRewrite, canExport,
    setSettingsOpen, selectBlock, updateDraft, updateSelection, changeMode, dismissStatus,
    openDocument, chooseModel, checkLocalSetup, compareSources, rewrite, acceptProposal, rejectProposal,
    restoreOriginal, exportDocument,
  } = workspace;

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const command = getWorkspaceShortcut(event);
      if (!command || busy) return;
      switch (command) {
        case "open":
          event.preventDefault();
          void openDocument();
          break;
        case "export":
          event.preventDefault();
          if (canExport) void exportDocument();
          break;
        case "rewrite":
          event.preventDefault();
          if (canRewrite) void rewrite();
          break;
        case "reject":
          if (proposal) {
            event.preventDefault();
            rejectProposal();
          }
          break;
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [busy, canExport, canRewrite, proposal, openDocument, exportDocument, rewrite, rejectProposal]);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="identity">
          <span className="identity-icon" aria-hidden="true"><WandSparkles size={24} /></span>
          <div className="identity-copy">
            <strong>Silabs <span>Humanizer</span></strong>
            <small>Offline document studio <span className="preview-label">PREVIEW</span></small>
          </div>
        </div>
        <div className="header-actions">
          <div className="privacy-indicator" title="Documents are processed on your computer.">
            <span className="local-dot" /> On-device
          </div>
          <button type="button" className="button button-quiet"
            aria-expanded={settingsOpen} aria-controls="model-settings"
            onClick={() => setSettingsOpen(!settingsOpen)} disabled={!!busy}>
            <Settings2 size={17} /> Model settings
          </button>
          <button type="button" className="button button-primary"
            disabled={!!busy} onClick={openDocument} title="Open document (Ctrl+O)">
            {busy === "open" ? <LoaderCircle size={17} className="spinning" /> : <FolderOpen size={17} />}
            {busy === "open" ? "Opening…" : doc ? "Open another file" : "Open document"}
          </button>
        </div>
      </header>

      <div className="app-body">
        <DocumentSidebar
          doc={doc} selected={selected} accepted={accepted} busy={!!busy}
          onSelect={selectBlock}
        />

        <main className="main-content">
          {settingsOpen && (
            <section className="settings-panel" id="model-settings" aria-labelledby="settings-title">
              <div className="settings-copy">
                <span className="overline">OFFLINE MODEL</span>
                <h2 id="settings-title">Local inference</h2>
                <p>{bundledModel ?
                  "The bundled model file was found. Run the local check to verify the required components, or choose another GGUF." :
                  "Choose a compatible GGUF model already saved on your computer. There are no server connections."}</p>
                <span className="model-location" title={modelPath}>{bundledModel ?
                  "Included Qwen model" : modelPath || "No model selected"}</span>
              </div>
              <div className="settings-controls">
                <button type="button" className="button button-secondary" disabled={!!busy} onClick={chooseModel}>
                  <HardDrive size={17} /> Choose GGUF
                </button>
                <button type="button" className="button button-primary"
                  onClick={checkLocalSetup} disabled={!!busy || !modelPath}>
                  {busy === "diagnostics" ? <LoaderCircle size={16} className="spinning" /> : <ShieldCheck size={16} />}
                  {busy === "diagnostics" ? "Checking…" : "Check local setup"}
                </button>
                {diagnostics && (
                  <div className="local-check-result" role="status">
                    <strong>{diagnostics.components_present
                      ? "Core offline files and libraries found"
                      : "Offline setup requires attention"}</strong>
                    <span>GGUF weights: {diagnostics.gguf_header_valid ? "Found" : "Missing/invalid"} · Inference engine: {diagnostics.inference_installed ? "Found" : "Missing"} · Word support: {diagnostics.word_support_installed ? "Found" : "Missing"} · English dictionary: {diagnostics.english_dictionary_installed ? "Found" : "Missing"}</span>
                    {diagnostics.issues.map((issue, i) => <span key={i} className="diagnostic-issue">{issue}</span>)}
                    <small>{diagnostics.note}</small>
                  </div>
                )}
              </div>
            </section>
          )}

          <div className="page-heading">
            <div>
              <span className="overline">{doc ? "DOCUMENT WORKSPACE" : "WELCOME"}</span>
              <h1>{doc ? "Refine your writing" : "Write clearly. Stay in control."}</h1>
              <p>{doc ? "Edit your document directly, review writing suggestions, and export only approved changes." :
                "Open your document, improve its wording, and decide what gets saved."}</p>
            </div>
            {doc && (
              <div className="export-controls">
                <span className="export-count">{acceptedCount} accepted · {editables} editable</span>
                <button type="button" className="button button-export"
                  onClick={exportDocument} disabled={!canExport} title="Export revised file (Ctrl+Shift+S)">
                  {busy === "export" ? <LoaderCircle size={17} className="spinning" /> : <FileDown size={17} />}
                  {busy === "export" ? "Exporting…" : "Export revised file"}
                </button>
                {acceptedCount > 0 && !hasUnexportedChanges &&
                  <span className="save-state"><CheckCircle2 size={15} /> Exported</span>}
              </div>
            )}
          </div>

          {status && (
            <div className={"status-banner status-" + status.kind} role={status.kind === "error" ? "alert" : "status"}>
              {status.kind === "error" ? <AlertCircle size={18} /> : <CheckCircle2 size={18} />}
              <p>{status.message}</p>
              <button type="button" onClick={dismissStatus} aria-label="Dismiss message"><X size={17} /></button>
            </div>
          )}

          {!doc ? (
            <section className="empty-workspace" aria-labelledby="welcome-heading">
              <div className="empty-icon"><FileText size={33} /></div>
              <h2 id="welcome-heading">Your document comes first.</h2>
              <p>Open a DOCX, TXT or Markdown file. Select a paragraph, choose a writing style, then compare the result before accepting it.</p>
              <button className="button button-primary button-large" type="button"
                disabled={!!busy} onClick={openDocument}>
                <FolderOpen size={19} /> Choose document
              </button>
              <div className="empty-assurance">
                <span><LockKeyhole size={16} /> Offline processing</span>
                <span><ShieldCheck size={16} /> Original file preserved</span>
                <span><Sparkles size={16} /> Your approval required</span>
              </div>
            </section>
          ) : (
            <div className="writing-workspace">
              <DocumentCanvas doc={doc} selected={selected} accepted={accepted}
                busy={!!busy} onSelect={selectBlock} onEdit={updateDraft}
                onSelection={updateSelection} />
              <WritingAssistant activeBlock={activeBlock} workingText={workingText}
                previewText={previewText} selection={selection}
                mode={mode} proposal={proposal} accepted={accepted}
                modelReady={!!modelPath} busy={busy === "rewrite"} compareBusy={busy === "compare"}
                analysis={analysis} analysisError={analysisError}
                analysisPending={analysisPending} sourceReport={sourceReport}
                canRewrite={canRewrite}
                onMode={changeMode} onRewrite={rewrite} onEdit={updateDraft}
                onAccept={acceptProposal} onReject={rejectProposal}
                onRestore={restoreOriginal}
                onCompareSources={compareSources}
                onShowSettings={() => setSettingsOpen(true)} />
            </div>
          )}
        </main>
      </div>
      <footer className="app-footer">
        <span><span className="local-dot" /> Files remain on this device</span>
        <span>{doc ? doc.name : "Silabs Humanizer"} · Engineering preview</span>
      </footer>
    </div>
  );
}
