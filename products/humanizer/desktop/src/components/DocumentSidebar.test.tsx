// @vitest-environment jsdom
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import DocumentSidebar from "./DocumentSidebar";
import type { OpenedDocument } from "../ipc";
import { OUTLINE_PAGE_SIZE } from "../editor/outline";

function sampleDocument(count: number): OpenedDocument {
  return {
    path: "C:\\Documents\\test.docx",
    fingerprint: "example-fingerprint",
    name: "test.docx",
    format: "docx",
    blocks: Array.from({ length: count }, (_, index) => ({
      index, text: "Section content " + index,
      kind: "paragraph", style: "Normal", editable: true, reason: null,
    })),
  };
}

describe("large document navigation", () => {
  it("renders only the first page and can reveal additional paragraphs", () => {
    render(<DocumentSidebar doc={sampleDocument(230)} selected={0}
      accepted={{}} busy={false} onSelect={vi.fn()} />);

    expect(screen.getByText(OUTLINE_PAGE_SIZE + " of 230 shown")).toBeTruthy();
    expect(screen.queryByText("Section content 180")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /show more paragraphs/i }));
    expect(screen.getByText("160 of 230 shown")).toBeTruthy();
    expect(screen.getByText("Section content 159")).toBeTruthy();
  });

  it("searches the full document even when a result is past the current page", () => {
    render(<DocumentSidebar doc={sampleDocument(230)} selected={0}
      accepted={{}} busy={false} onSelect={vi.fn()} />);

    fireEvent.change(screen.getByRole("textbox", { name: /find in document outline/i }), {
      target: { value: "Section content 180" },
    });
    expect(screen.getByText("Section content 180")).toBeTruthy();
    expect(screen.getByText("1 of 1 shown")).toBeTruthy();
    expect(screen.queryByText("Section content 159")).toBeNull();
  });
});
