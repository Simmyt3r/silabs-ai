"""Document-level style controls."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StyleProfile:
    mode: str = "natural"
    english_variant: str = "British"
    person: str = "third_person"
    citation_style: str | None = None
    preferred_terms: tuple[str, ...] = ()
    avoided_terms: tuple[str, ...] = ()

    def instruction(self) -> str:
        parts = [
            f"Rewrite mode: {self.mode}.",
            f"Use {self.english_variant} English.",
            f"Preferred grammatical person: {self.person}.",
        ]
        if self.citation_style:
            parts.append(f"Preserve {self.citation_style} citation conventions.")
        if self.preferred_terms:
            parts.append("Prefer these terms: " + ", ".join(self.preferred_terms) + ".")
        if self.avoided_terms:
            parts.append("Avoid these terms where possible: " + ", ".join(self.avoided_terms) + ".")
        return " ".join(parts)
