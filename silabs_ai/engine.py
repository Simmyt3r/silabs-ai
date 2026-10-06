from __future__ import annotations

import logging
import threading
from dataclasses import dataclass

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from .config import Settings, get_settings
from .model_source import resolve_model_source
from .prompting import build_chat_messages, ensure_system_message
from .retrieval import NullRetriever, Retriever
from .schemas import Message

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    text: str
    input_tokens: int
    output_tokens: int


class SilabsAIEngine:
    """Thread-safe lazy-loading text-generation engine."""

    def __init__(
        self,
        settings: Settings | None = None,
        retriever: Retriever | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.retriever = retriever or NullRetriever()
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
                "torch_dtype": self._torch_dtype(),
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
    ) -> GenerationResult:
        self.load()
        assert self._model is not None
        assert self._tokenizer is not None

        messages = ensure_system_message(messages, self.settings.system_prompt)
        input_ids = self._tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        )

        device = next(self._model.parameters()).device
        input_ids = input_ids.to(device)

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
            output = self._model.generate(input_ids, **generation_kwargs)

        generated = output[0, input_ids.shape[-1] :]
        text = self._tokenizer.decode(generated, skip_special_tokens=True).strip()

        return GenerationResult(
            text=text,
            input_tokens=int(input_ids.shape[-1]),
            output_tokens=int(generated.shape[-1]),
        )

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
        chunks = self.retriever.retrieve(message, limit=4)
        messages = build_chat_messages(
            message,
            history,
            system_prompt=system_prompt or self.settings.system_prompt,
            retrieved_context=[chunk.text for chunk in chunks],
        )
        return self.generate(
            messages,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
        )
