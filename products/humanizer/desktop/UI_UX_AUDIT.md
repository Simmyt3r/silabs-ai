# Silabs Humanizer desktop: UI/UX and structural audit

Status: **UI foundation refactored; real-device usability review still open.**
Scope: improve existing product. No feature expansion or installer work.

## One clear workflow

~~~text
Open local document
  |
  v
Find and select paragraph in the outline
  |
  v
Choose ONE rewrite style
  |
  v
Generate a local suggestion
  |
  v
Compare word-level changes
  |
  +--> Reject -> no change
  |
  +--> Accept -> working copy (not yet saved)
                    |
                    v
              Export NEW file
~~~

No account screens, cloud integrations, extra dashboards, redundant navigation
bars, or confusing parallel editor modes.

## Information architecture

~~~text
src/
  App.tsx                     # consistent shell, toolbar, status, welcome
  ipc.ts                     # typed bridge; no business state
  components/
    DocumentSidebar.tsx      # search, heading hierarchy, selection
    ReviewWorkspace.tsx      # style controls and before/after review
  editor/
    useDocumentWorkspace.ts  # one owner of app state, dialogs, document actions
    review.ts                 # revision snapshot, editable guard, word count
    diff.ts                   # capped word-level comparison
    outline.ts                # bounded list and full-document search
    hotkeys.ts                # keyboard shortcut guards
    modes.ts                  # one source for the seven rewriting labels
  styles.css                 # tokens, layout, typography and accessibility
~~~

### UX improvements actually implemented

- Consistent header, outline, and paper-like editorial workspace.
- Single, numbered Select > Refine > Review journey.
- Searchable outline, headings and clearly labelled read-only paragraphs.
- Bounded outline rendering (80 entries at a time) to keep long-document navigation responsive.
- Complete-document search remains available even for paragraphs not yet rendered.
- Keyboard shortcuts: Ctrl+O open, Ctrl+Enter rewrite, Ctrl+Shift+S export, Escape reject.
- Keyboard shortcuts do not intercept text-input typing or repeat events.
- Selected paragraph details and word count.
- One set of seven modes with user-facing explanations.
- Disabled Generate when no local model or when selected block is read-only.
- One operation lock to prevent duplicate rewrite/export actions.
- Real before/after word-level comparison with input reconstruction checks.
- Explicit proposal Accept/Reject; restore an accepted paragraph to original.
- Accepted revisions kept separate from exported revisions.
- Export state confirms actual completed export; no false "saved" message.
- Safeguard on switching documents or closing with unexported revisions.
- Reset outline search when document changes.
- Notice/error states and visible progress labels.
- Contrast-focused writing view, responsive comparison, keyboard focus rings,
  accessible control labels and reduced-motion preference.

### Functional boundaries

- The editor operates on **whole paragraphs**, not arbitrary text selections.
- Complex Word formatting is read-only to prevent accidental damage.
- Automatic checks protect some citations and numeric values, **not all facts**.
- The word diff is a visual review aid, not a grammar or truthfulness score.
- The app is an offline engineering preview; real-model tests and clean-PC
  interactive UX acceptance are still required.

## Manual UX acceptance checklist

Test on Windows x64 with local GGUF and DOCX/TXT/MD samples.

- [ ] Welcome screen, open-file dialog and local model setup are obvious.
- [ ] Keyboard Tab and Shift+Tab reach controls in a logical order.
- [ ] Verify Ctrl+O, Ctrl+Enter, Ctrl+Shift+S and Escape on Windows without interfering with native dialogs.
- [ ] Focus indicators stay visible and buttons have adequate contrast.
- [ ] Large document outline scrolls, paging remains discoverable, and search finds a heading and paragraph.
- [ ] Opening a different document clears old search, proposal and selections.
- [ ] Heading and richly formatted blocks show an accurate read-only reason.
- [ ] Generate is blocked without a model or while another operation runs.
- [ ] No simultaneous requests or missing-response crashes under repeated clicks.
- [ ] A short paragraph produces a complete, readable original/revision comparison.
- [ ] Reject changes nothing; Accept updates only the working copy.
- [ ] Restore original works after acceptance.
- [ ] Export button activates only for unexported accepted revisions.
- [ ] Saved/exported state appears only after the filesystem operation succeeds.
- [ ] Switching files with pending revisions asks for confirmation.
- [ ] Closing the app with pending revisions asks for confirmation.
- [ ] The original file is unchanged after rewrite, reject, accept and export.
- [ ] Test 1024x768, 1366x768, 1920x1080, 125% and 150% DPI.
- [ ] Test longer text, complex DOCX, table cells and unavailable model paths.
- [ ] Verify offline operation and no outbound document transfer.
- [ ] Review output accuracy and factual preservation manually.

These checks are intentionally not marked complete without real desktop QA.

## Rules for subsequent work

1. Do not add features until this UX checklist passes.
2. Do not change working service/model logic to make the UI appear functional.
3. Refactor shared state in the single controller; do not recreate state in cards.
4. Keep prompts, mode labels and backend mode identifiers consistent.
5. Keep destructive actions explicit and original files non-destructive.
6. Run UI tests, TypeScript build, Python regression and Windows-native CI.
7. Fix defects before adding new design components.

## UI testing added in this iteration

- Pure tests for multi-term outline search and capped pagination.
- Pure tests for guarded keyboard shortcuts and text-input exclusions.
- DOM interaction tests for 230-paragraph outlines, Show more, and searching beyond the initial page.
- GitHub Actions runs UI tests, React/TypeScript build, Python regression and native Windows checks.

These are automation gates, not a substitute for manual usability or accessibility testing on the actual desktop build.

## Clean installation automation (2026-10-19)

The separately downloaded full-model installer passed fresh-runner NSIS installation, installed-file and Qwen checksum checks, actual offline CPU inference, DOCX export and TXT export. Original files remained unchanged. The graphical WebView, accessibility, scaling, file dialogs and completely disconnected machine must still be tested interactively.

Evidence: https://github.com/Simmyt3r/silabs-ai/actions/runs/39268760789

## v0.1.1 workflow polish

- [x] Test realistic UI flow: open document > run rewrite > review > accept >
  export, including unsaved document switching.
- [x] Add first-run offline component diagnostics in Model settings.
- [x] Warn that file checks do not certify real inference or text quality.
- [x] Show a visible first-rewrite CPU wait explanation.
- [ ] Run manual interactive GUI checks on a physical Windows computer.
- [ ] Rebuild v0.1.1 installer and verify its installed resources and real
  bundled Qwen inference.
