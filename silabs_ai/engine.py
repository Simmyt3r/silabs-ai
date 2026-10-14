from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass, field

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

from .config import Settings, get_settings
from .guardrails import BasicGuardrail
from .model_source import resolve_model_source
from .prompting import build_chat_messages, ensure_system_message
from .retrieval import JsonlKnowledgeRetriever, NullRetriever, RetrievedChunk, Retriever
from .response_contracts import contract_for_prompt, enforce_contract
from .schemas import Message

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    text: str
    input_tokens: int
    output_tokens: int
    finish_reason: str = "stop"
    guardrail_category: str | None = None
    sources: list[RetrievedChunk] = field(default_factory=list)
    citation_repaired: bool = False


_CITATION_RE = re.compile(r"\[(S\d+)\]")


def enforce_source_citations(
    text: str,
    sources: list[RetrievedChunk] | None,
) -> tuple[str, bool]:
    source_list = list(sources or [])
    valid_labels = {
        item.citation
        for item in source_list
        if item.citation
    }
    if not valid_labels:
        return text, False

    repaired = False

    def replace_unknown(match: re.Match[str]) -> str:
        nonlocal repaired
        label = match.group(1)
        if label in valid_labels:
            return match.group(0)
        repaired = True
        return ""

    cleaned = _CITATION_RE.sub(replace_unknown, text).strip()
    cited = set(_CITATION_RE.findall(cleaned))

    if not cited:
        preferred = source_list[0].citation
        if preferred:
            cleaned = cleaned.rstrip()
            if cleaned:
                cleaned += f" [{preferred}]"
            else:
                cleaned = f"[{preferred}]"
            repaired = True

    return cleaned, repaired


class SilabsAIEngine:
    """Thread-safe lazy-loading text-generation engine."""

    def __init__(
        self,
        settings: Settings | None = None,
        retriever: Retriever | None = None,
        guardrail: BasicGuardrail | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        if retriever is not None:
            self.retriever = retriever
        elif self.settings.rag_enabled and self.settings.knowledge_path:
            self.retriever = JsonlKnowledgeRetriever(
                self.settings.knowledge_path,
                min_score=self.settings.rag_min_score,
            )
        else:
            self.retriever = NullRetriever()
        self.guardrail = guardrail or BasicGuardrail()
        self._tokenizer = None
        self._model = None
        self._load_lock = threading.Lock()
        self._generate_lock = threading.Lock()

    @property
    def loaded(self) -> bool:
        return self._model is not None and self._tokenizer is not None

    def _torch_dtype(self):
        requested = self.settings.dtype
        if requested == "float32":
            return torch.float32
        if requested == "float16":
            return torch.float16
        if requested == "bfloat16":
            return torch.bfloat16
        return "auto"

    def _apply_guardrail(self, text: str) -> GenerationResult | None:
        if not self.settings.enable_guardrails:
            return None

        decision = self.guardrail.evaluate(text)
        if decision is None:
            return None

        logger.info("Guardrail intercepted request: %s", decision.category)
        return GenerationResult(
            text=decision.response,
            input_tokens=0,
            output_tokens=0,
            finish_reason="guardrail",
            guardrail_category=decision.category,
        )

    @staticmethod
    def _latest_user_content(messages: list[dict[str, str]]) -> str | None:
        for message in reversed(messages):
            if message.get("role") == "user":
                content = message.get("content", "").strip()
                if content:
                    return content
        return None

    def load(self) -> None:
        if self.loaded:
            return

        with self._load_lock:
            if self.loaded:
                return

            source = resolve_model_source(
                local_path=self.settings.model_path,
                remote_id=self.settings.model_id,
                allow_remote=self.settings.allow_remote_model_download,
            )
            logger.info(
                "Loading Silabs AI base model from %s (%s)",
                source.value,
                "local" if source.is_local else "remote",
            )

            common_kwargs = {
                "trust_remote_code": self.settings.trust_remote_code,
                "local_files_only": source.is_local,
            }
            if not source.is_local:
                common_kwargs["revision"] = self.settings.model_revision
                common_kwargs["cache_dir"] = self.settings.model_cache

            self._tokenizer = AutoTokenizer.from_pretrained(
                source.value,
                **common_kwargs,
            )

            model_kwargs = {
                **common_kwargs,
                "dtype": self._torch_dtype(),
            }
            if self.settings.device == "auto":
                model_kwargs["device_map"] = "auto"

            self._model = AutoModelForCausalLM.from_pretrained(
                source.value,
                **model_kwargs,
            )

            if self.settings.device != "auto":
                self._model.to(self.settings.device)

            if self.settings.adapter_path:
                try:
                    from peft import PeftModel
                except ImportError as exc:
                    raise RuntimeError(
                        "PEFT is required to load SILABS_ADAPTER_PATH."
                    ) from exc
                self._model = PeftModel.from_pretrained(
                    self._model,
                    self.settings.adapter_path,
                )

            self._model.eval()
            logger.info("Silabs AI model loaded")

    def generate(
        self,
        messages: list[dict[str, str]],
        *,
        max_new_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        sources: list[RetrievedChunk] | None = None,
    ) -> GenerationResult:
        user_content = self._latest_user_content(messages)
        contract = None
        if user_content:
            guarded = self._apply_guardrail(user_content)
            if guarded is not None:
                return guarded

            contract = contract_for_prompt(user_content)
            if contract and contract.direct_response is not None:
                return GenerationResult(
                    text=contract.direct_response,
                    input_tokens=0,
                    output_tokens=len(contract.direct_response.split()),
                    finish_reason="contract",
                )

        self.load()
        assert self._model is not None
        assert self._tokenizer is not None

        messages = ensure_system_message(messages, self.settings.system_prompt)
        if contract and contract.system_instruction:
            base_system = messages[0]["content"]
            messages = [
                {
                    "role": "system",
                    "content": (
                        base_system
                        + "\n\nHard response contract:\n"
                        + contract.system_instruction
                    ),
                },
                *messages[1:],
            ]
        encoded = self._tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
            enable_thinking=self.settings.enable_thinking,
        )

        device = next(self._model.parameters()).device
        input_ids = encoded["input_ids"].to(device)
        attention_mask = encoded.get("attention_mask")
        if attention_mask is None:
            attention_mask = torch.ones_like(
                input_ids, dtype=torch.long, device=device
            )
        else:
            attention_mask = attention_mask.to(device)

        temp = self.settings.temperature if temperature is None else temperature
        nucleus = self.settings.top_p if top_p is None else top_p
        do_sample = temp > 0

        generation_kwargs = {
            "max_new_tokens": max_new_tokens or self.settings.max_new_tokens,
            "do_sample": do_sample,
            "repetition_penalty": self.settings.repetition_penalty,
            "pad_token_id": self._tokenizer.eos_token_id,
        }
        if do_sample:
            generation_kwargs["temperature"] = temp
            generation_kwargs["top_p"] = nucleus

        with self._generate_lock, torch.inference_mode():
            output = self._model.generate(
                input_ids,
                attention_mask=attention_mask,
                **generation_kwargs,
            )

        generated = output[0, input_ids.shape[-1] :]
        text = self._tokenizer.decode(generated, skip_special_tokens=True).strip()
        text = enforce_contract(text, contract)
        text, citation_repaired = enforce_source_citations(text, sources)

        return GenerationResult(
            text=text,
            input_tokens=int(input_ids.shape[-1]),
            output_tokens=int(generated.shape[-1]),
            sources=list(sources or []),
            citation_repaired=citation_repaired,
        )

    def stream_chat(
        self,
        message: str,
        history: list[Message] | None = None,
        *,
        system_prompt: str | None = None,
        max_new_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
    ):
        guarded = self._apply_guardrail(message)
        if guarded is not None:
            yield {"type": "chunk", "text": guarded.text}
            yield {
                "type": "final",
                "result": guarded,
            }
            return

        chunks = self.retriever.retrieve(
            message,
            limit=self.settings.rag_limit,
        )
        retrieved_context = [
            (
                f"[{chunk.citation or f'S{index}'}] Source: {chunk.source}\n{chunk.text}"
                if chunk.source
                else f"[{chunk.citation or f'S{index}'}]\n{chunk.text}"
            )
            for index, chunk in enumerate(chunks, start=1)
        ]
        messages = build_chat_messages(
            message,
            history,
            system_prompt=system_prompt,
            retrieved_context=retrieved_context,
        )

        user_content = self._latest_user_content(messages)
        contract = contract_for_prompt(user_content) if user_content else None
        if contract and contract.direct_response is not None:
            result = GenerationResult(
                text=contract.direct_response,
                input_tokens=0,
                output_tokens=len(contract.direct_response.split()),
                finish_reason="contract",
                sources=chunks,
            )
            result.text, result.citation_repaired = enforce_source_citations(
                result.text,
                chunks,
            )
            yield {"type": "chunk", "text": result.text}
            yield {"type": "final", "result": result}
            return

        self.load()
        assert self._model is not None
        assert self._tokenizer is not None

        messages = ensure_system_message(messages, self.settings.system_prompt)
        if contract and contract.system_instruction:
            base_system = messages[0]["content"]
            messages = [
                {
                    "role": "system",
                    "content": (
                        base_system
                        + "\n\nHard response contract:\n"
                        + contract.system_instruction
                    ),
                },
                *messages[1:],
            ]

        encoded = self._tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
            enable_thinking=self.settings.enable_thinking,
        )
        device = next(self._model.parameters()).device
        input_ids = encoded["input_ids"].to(device)
        attention_mask = encoded.get("attention_mask")
        if attention_mask is None:
            attention_mask = torch.ones_like(
                input_ids, dtype=torch.long, device=device
            )
        else:
            attention_mask = attention_mask.to(device)

        temp = self.settings.temperature if temperature is None else temperature
        nucleus = self.settings.top_p if top_p is None else top_p
        do_sample = temp > 0
        streamer = TextIteratorStreamer(
            self._tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
        )
        generation_kwargs = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "streamer": streamer,
            "max_new_tokens": max_new_tokens or self.settings.max_new_tokens,
            "do_sample": do_sample,
            "repetition_penalty": self.settings.repetition_penalty,
            "pad_token_id": self._tokenizer.eos_token_id,
        }
        if do_sample:
            generation_kwargs["temperature"] = temp
            generation_kwargs["top_p"] = nucleus

        worker_error: list[BaseException] = []

        def run_generation() -> None:
            try:
                with self._generate_lock, torch.inference_mode():
                    self._model.generate(**generation_kwargs)
            except BaseException as exc:
                worker_error.append(exc)
                streamer.end()

        worker = threading.Thread(target=run_generation, daemon=True)
        worker.start()

        pieces: list[str] = []
        for piece in streamer:
            if not piece:
                continue
            pieces.append(piece)
            yield {"type": "chunk", "text": piece}

        worker.join()
        if worker_error:
            raise RuntimeError("Streaming generation failed") from worker_error[0]

        raw_text = "".join(pieces).strip()
        final_text = enforce_contract(raw_text, contract)
        final_text, citation_repaired = enforce_source_citations(
            final_text,
            chunks,
        )
        output_tokens = len(
            self._tokenizer.encode(
                raw_text,
                add_special_tokens=False,
            )
        )

        result = GenerationResult(
            text=final_text,
            input_tokens=int(input_ids.shape[-1]),
            output_tokens=output_tokens,
            sources=chunks,
            citation_repaired=citation_repaired,
        )
        yield {"type": "final", "result": result}

    def chat(
        self,
        message: str,
        history: list[Message] | None = None,
        *,
        system_prompt: str | None = None,
        max_new_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
    ) -> GenerationResult:
        guarded = self._apply_guardrail(message)
        if guarded is not None:
            return guarded

        chunks = self.retriever.retrieve(
            message,
            limit=self.settings.rag_limit,
        )
        retrieved_context = [
            (
                f"[{chunk.citation or f'S{index}'}] Source: {chunk.source}\n{chunk.text}"
                if chunk.source
                else f"[{chunk.citation or f'S{index}'}]\n{chunk.text}"
            )
            for index, chunk in enumerate(chunks, start=1)
        ]
        messages = build_chat_messages(
            message,
            history,
            system_prompt=system_prompt,
            retrieved_context=retrieved_context,
        )
        return self.generate(
            messages,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            sources=chunks,
        )
