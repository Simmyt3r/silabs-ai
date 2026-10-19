import { useEffect, useMemo, useRef, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { confirm, open, save } from "@tauri-apps/plugin-dialog";
import type { LocalDiagnostics, OpenedDocument, RewriteMode, RewriteProposal } from "../ipc";
import { localApi } from "../ipc";
import { canEditBlock, snapshotOf, type ReviewStatus } from "./review";

export type BusyState = "open" | "rewrite" | "export" | "diagnostics" | null;

export function useDocumentWorkspace() {
  const [doc, setDoc] = useState<OpenedDocument | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [mode, setMode] = useState<RewriteMode>("natural");
  const [modelPath, setModelPath] = useState("");
  const [bundledModel, setBundledModel] = useState(false);
  const [diagnostics, setDiagnostics] = useState<LocalDiagnostics | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [accepted, setAccepted] = useState<Record<number, string>>({});
  const [proposal, setProposal] = useState<RewriteProposal | null>(null);
  const [exportedSnapshot, setExportedSnapshot] = useState<string | null>(null);
  const [busy, setBusy] = useState<BusyState>(null);
  const [status, setStatus] = useState<ReviewStatus>(null);
  const operationLock = useRef(false);

  useEffect(() => {
    let mounted = true;
    invoke<{ packaged: boolean; model_path: string | null }>("runtime_info")
      .then(info => {
        if (!mounted) return;
        if (info.model_path) {
          setDiagnostics(null);
          setModelPath(info.model_path);
          setBundledModel(info.packaged);
        } else if (info.packaged) {
          setStatus({
            kind: "error",
            message: "The bundled offline model is missing. Reinstall the complete edition.",
          });
        }
      })
      .catch(err => {
        if (mounted) setStatus({ kind: "error", message: "Cannot inspect the local AI runtime: " + String(err) });
      });
    return () => { mounted = false; };
  }, []);

  const activeBlock = useMemo(
    () => doc?.blocks.find(block => block.index === selected) ?? null,
    [doc, selected],
  );
  const revisionSnapshot = useMemo(() => snapshotOf(accepted), [accepted]);
  const acceptedCount = Object.keys(accepted).length;
  const hasUnexportedChanges = acceptedCount > 0 && revisionSnapshot !== exportedSnapshot;
  const canRewrite = !!doc && canEditBlock(activeBlock) && !!modelPath && busy === null;
  const canExport = !!doc && hasUnexportedChanges && busy === null;
  const editables = doc?.blocks.filter(block => canEditBlock(block)).length ?? 0;

  // Prevent silently losing accepted edits when the user closes the window.
  // The handler must prevent the close synchronously, before showing dialog.
  useEffect(() => {
    const window = getCurrentWindow();
    let disposed = false;
    let unlisten: (() => void) | null = null;
    let confirmedClose = false;
    void window.onCloseRequested(async event => {
      if (!hasUnexportedChanges || confirmedClose) return;
      event.preventDefault();
      try {
        const discard = await confirm(
          "You have accepted revisions that have not been exported. Exit without saving them?",
          { title: "Unsaved changes", kind: "warning" },
        );
        if (discard) {
          confirmedClose = true;
          try { await window.close(); }
          catch (error) {
            confirmedClose = false;
            setStatus({ kind: "error", message: "Could not close the window: " + String(error) });
          }
        }
      } catch (error) {
        setStatus({ kind: "error", message: "Close confirmation failed: " + String(error) });
      }
    }).then(stop => {
      if (disposed) stop(); else unlisten = stop;
    }).catch(error => {
      if (!disposed) setStatus({ kind: "error", message: "Cannot protect unsaved edits: " + String(error) });
    });
    return () => { disposed = true; unlisten?.(); };
  }, [hasUnexportedChanges]);

  function selectBlock(index: number) {
    if (operationLock.current) return;
    setSelected(index);
    setProposal(null);
    setStatus(null);
  }

  function changeMode(next: RewriteMode) {
    if (operationLock.current) return;
    setMode(next);
    setProposal(null);
  }

  function dismissStatus() { setStatus(null); }

  async function openDocument() {
    if (operationLock.current) return;
    operationLock.current = true;
    try {
      const path = await open({
        multiple: false,
        directory: false,
        filters: [{ name: "Documents", extensions: ["docx", "txt", "md"] }],
      });
      if (typeof path !== "string") return;
      if (hasUnexportedChanges) {
        const discard = await confirm(
          "You have accepted revisions that have not been exported. Opening another file will discard those revisions.",
          { title: "Unsaved changes", kind: "warning" },
        );
        if (!discard) return;
      }
      setBusy("open");
      setStatus(null);
      const result = await localApi.open(path);
      setDoc(result);
      setSelected(result.blocks.find(block => canEditBlock(block))?.index ?? result.blocks[0]?.index ?? null);
      setAccepted({});
      setExportedSnapshot(null);
      setProposal(null);
      setStatus({ kind: "success", message: "Opened " + result.name + ". Choose a paragraph to begin." });
    } catch (error) {
      setStatus({ kind: "error", message: String(error) });
    } finally {
      operationLock.current = false;
      setBusy(null);
    }
  }

  async function chooseModel() {
    if (operationLock.current) return;
    operationLock.current = true;
    try {
      const path = await open({
        multiple: false, directory: false,
        filters: [{ name: "Local GGUF model", extensions: ["gguf"] }],
      });
      if (typeof path === "string") {
        setModelPath(path);
        setBundledModel(false);
        setDiagnostics(null);
        setProposal(null);
        setStatus({ kind: "success", message: "Local GGUF selected. All writing remains on this computer." });
      }
    } catch (error) {
      setStatus({ kind: "error", message: String(error) });
    } finally {
      operationLock.current = false;
    }
  }

  async function checkLocalSetup() {
    if (!modelPath || operationLock.current) return;
    operationLock.current = true;
    setBusy("diagnostics");
    setDiagnostics(null);
    setStatus(null);
    try {
      const result = await localApi.diagnostics(modelPath);
      setDiagnostics(result);
      if (!result.components_present) {
        setStatus({
          kind: "error",
          message: "Some offline components need attention. Review the checks below.",
        });
      }
    } catch (error) {
      setStatus({ kind: "error", message: "Local setup check failed: " + String(error) });
    } finally {
      operationLock.current = false;
      setBusy(null);
    }
  }

  async function rewrite() {
    if (!doc || selected === null || !canRewrite || operationLock.current) return;
    operationLock.current = true;
    setBusy("rewrite");
    setProposal(null);
    setStatus(null);
    try {
      const result = await localApi.rewrite(doc, selected, mode, modelPath);
      setProposal(result);
      if (!result.passed) {
        setStatus({
          kind: "error",
          message: "This draft failed automatic protection checks. No edits were accepted.",
        });
      }
    } catch (error) {
      setStatus({ kind: "error", message: String(error) });
    } finally {
      setBusy(null);
      operationLock.current = false;
    }
  }

  function acceptProposal() {
    if (operationLock.current || !proposal?.passed || !activeBlock || proposal.index !== activeBlock.index) return;
    setAccepted(previous => ({ ...previous, [activeBlock.index]: proposal.proposal }));
    setProposal(null);
    setStatus({ kind: "success", message: "Revision accepted in your working copy. Export when ready." });
  }

  function rejectProposal() {
    if (operationLock.current) return;
    setProposal(null);
    setStatus({ kind: "info", message: "Suggestion rejected; your current draft is unchanged." });
  }

  function restoreOriginal() {
    if (operationLock.current || selected === null) return;
    setAccepted(previous => {
      const next = { ...previous };
      delete next[selected];
      return next;
    });
    setProposal(null);
    setStatus({ kind: "info", message: "This paragraph has been restored to its original wording." });
  }

  async function exportDocument() {
    if (!doc || !canExport || operationLock.current) return;
    operationLock.current = true;
    try {
      const suffix = "." + doc.format;
      const filename = doc.name.endsWith(suffix) ?
        doc.name.slice(0, -suffix.length) + "-revised" + suffix :
        doc.name + "-revised";
      const destination = await save({
        defaultPath: filename,
        filters: [{ name: "Revised document", extensions: [doc.format] }],
      });
      if (!destination) return;
      setBusy("export");
      setStatus(null);
      const currentSnapshot = snapshotOf(accepted);
      const result = await localApi.export(doc, destination, accepted);
      setExportedSnapshot(currentSnapshot);
      setStatus({
        kind: "success",
        message: "Saved " + result.revised_count + " reviewed " +
          (result.revised_count === 1 ? "revision" : "revisions") + " to " + result.destination,
      });
    } catch (error) {
      setStatus({ kind: "error", message: String(error) });
    } finally {
      operationLock.current = false;
      setBusy(null);
    }
  }

  return {
    doc, selected, activeBlock, mode, modelPath, bundledModel, settingsOpen, diagnostics,
    accepted, acceptedCount, proposal, busy, status, editables,
    hasUnexportedChanges, canRewrite, canExport,
    setSettingsOpen, selectBlock, changeMode, dismissStatus,
    openDocument, chooseModel, checkLocalSetup, rewrite, acceptProposal, rejectProposal,
    restoreOriginal, exportDocument,
  };
}
