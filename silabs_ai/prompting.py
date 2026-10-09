from __future__ import annotations

from collections.abc import Iterable

from .schemas import Message


def build_chat_messages(
    message: str,
    history: Iterable[Message] | None = None,
    *,
    system_prompt: str | None = None,
    retrieved_context: Iterable[str] | None = None,
) -> list[dict[str, str]]:
    """Build normalized chat messages for the tokenizer chat template."""
    messages: list[dict[str, str]] = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt.strip()})

    for item in history or []:
        messages.append({"role": item.role, "content": item.content.strip()})

    context = [chunk.strip() for chunk in (retrieved_context or []) if chunk.strip()]
    user_text = message.strip()
    if context:
        context_block = "\n\n".join(
            f"[Context {i + 1}]\n{chunk}" for i, chunk in enumerate(context)
        )
        user_text = (
            "Use the following retrieved context when relevant. Do not invent facts that "
            "are not present in it.\n\n"
            f"{context_block}\n\n[User]\n{user_text}"
        )

    messages.append({"role": "user", "content": user_text})
    return messages


def ensure_system_message(
    messages: list[dict[str, str]],
    system_prompt: str | None,
) -> list[dict[str, str]]:
    """Ensure the engine's base system contract cannot be replaced by clients."""
    if not system_prompt:
        return messages

    base = system_prompt.strip()
    if messages and messages[0].get("role") == "system":
        existing = messages[0].get("content", "").strip()
        if not existing or existing == base:
            return [{"role": "system", "content": base}, *messages[1:]]

        prefix = base + "\n\nAdditional application instructions:\n"
        if existing.startswith(prefix):
            return messages

        combined = prefix + existing
        return [{"role": "system", "content": combined}, *messages[1:]]

    return [{"role": "system", "content": base}, *messages]
