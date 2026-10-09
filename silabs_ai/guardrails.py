from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class GuardrailDecision:
    category: str
    response: str


class BasicGuardrail:
    """Small deterministic policy layer for high-risk request classes.

    This layer is intentionally narrow. It blocks or redirects cases where a
    360M language model should not be trusted to improvise a safe answer. It is
    not a substitute for model evaluation, retrieval, or broader policy work.
    """

    _credential = re.compile(
        r"(?i)\b(password|passcode|one[- ]?time password|otp|2fa code|api key|secret key)\b"
    )
    _credential_intent = re.compile(
        r"(?i)\b(tell|give|show|reveal|find|obtain|steal|extract|recover)\b"
    )

    _private_pii = re.compile(
        r"(?i)\b(exact home address|private (?:phone|mobile) number|personal "
        r"(?:phone|mobile) number)\b"
    )

    _cyber_object = re.compile(
        r"(?i)\b(phishing|ransomware|malware|keylogger|credential stealer|"
        r"password stealer|infostealer)\b"
    )
    _cyber_harm_intent = re.compile(
        r"(?i)\b(create|build|write|deploy|send|spread|steal|encrypt|infect|"
        r"step[- ]?by[- ]?step|instructions?|designed to)\b"
    )

    _medical_emergency = re.compile(
        r"(?i)(severe chest pain.*(?:trouble|difficulty).*breath|"
        r"(?:trouble|difficulty).*breath.*severe chest pain|"
        r"unconscious|severe bleeding|cannot breathe|can't breathe)"
    )
    _diagnosis_certainty = re.compile(
        r"(?i)(diagnos(?:e|is).*(?:with certainty|for certain|definitely)|"
        r"(?:tell me|say) exactly what illness)"
    )

    _financial_guarantee = re.compile(
        r"(?i)(guarantee.*(?:investment|return|profit)|"
        r"(?:definitely|guaranteed).*double.*money|risk[- ]?free.*return)"
    )
    _legal_certainty = re.compile(
        r"(?i)((?:with certainty|guarantee|definitely).*(?:legally safe|legal outcome)|"
        r"(?:legally safe|legal outcome).*(?:with certainty|guarantee|definitely))"
    )

    _future_certainty = re.compile(
        r"(?i)((?:exactly|definitely|for certain).*(?:will happen|will occur).*"
        r"(?:tomorrow|next week|next month|in the future)|"
        r"(?:what|which).*(?:will happen|will occur) tomorrow.*(?:exactly|for certain))"
    )

    _forced_false_claim = re.compile(
        r"(?i)(present .* as (?:a )?verified .*fact|state .* as (?:a )?verified .*fact|"
        r"pretend .* is (?:a )?verified .*fact)"
    )
    _unverified_award_study = re.compile(
        r"(?i)\b(?:Nobel[- ]winning|award[- ]winning) study by\b"
    )

    def evaluate(self, text: str) -> GuardrailDecision | None:
        prompt = " ".join(text.split())

        if self._cyber_object.search(prompt) and self._cyber_harm_intent.search(prompt):
            return GuardrailDecision(
                "malicious_cyber",
                "I cannot provide instructions or content for phishing, credential "
                "theft, malware, ransomware, or attacks on other people’s systems. "
                "I can help with detection, prevention, secure testing, incident "
                "response, or recovery.",
            )

        if self._credential.search(prompt) and self._credential_intent.search(prompt):
            return GuardrailDecision(
                "credentials",
                "I cannot access, reveal, or help steal passwords or other account "
                "credentials. Use the service’s official account-recovery or support "
                "process if you need to regain access.",
            )

        if self._private_pii.search(prompt):
            return GuardrailDecision(
                "private_information",
                "I cannot provide or help obtain a private person’s home address or "
                "private contact details. I can help with legitimate public contact "
                "channels instead.",
            )

        if self._medical_emergency.search(prompt):
            return GuardrailDecision(
                "medical_emergency",
                "Severe chest pain, major breathing difficulty, unconsciousness, or "
                "severe bleeding can be a medical emergency. Seek urgent professional "
                "medical help now or contact your local emergency service.",
            )

        if self._diagnosis_certainty.search(prompt):
            return GuardrailDecision(
                "medical_uncertainty",
                "I cannot diagnose an illness with certainty from a short description. "
                "Symptoms such as fever and headache have many possible causes. A "
                "qualified medical professional should assess you, especially if "
                "symptoms are severe, persistent, or worsening.",
            )

        if self._financial_guarantee.search(prompt):
            return GuardrailDecision(
                "financial_guarantee",
                "I cannot guarantee an investment return or promise that money will "
                "double. Investments involve risk, and claims of guaranteed rapid "
                "returns should be treated cautiously.",
            )

        if self._legal_certainty.search(prompt):
            return GuardrailDecision(
                "legal_certainty",
                "I cannot guarantee that a legal decision is safe without reviewing "
                "the relevant facts and documents. For a consequential contract or "
                "legal decision, have a qualified legal professional review it.",
            )

        if self._future_certainty.search(prompt):
            return GuardrailDecision(
                "future_certainty",
                "I cannot know or guarantee exactly what future news event will happen. "
                "I can discuss scheduled events, forecasts, or scenarios when reliable "
                "current sources are available.",
            )

        if self._forced_false_claim.search(prompt):
            return GuardrailDecision(
                "unverified_claim",
                "I cannot present an unverified claim as a verified fact. I can help "
                "check the evidence and distinguish established facts from myths or "
                "unsupported claims.",
            )

        if self._unverified_award_study.search(prompt):
            return GuardrailDecision(
                "source_verification",
                "I cannot verify that specific award-winning study from the information "
                "provided. Please provide a citation or use a retrieval-enabled source "
                "check before treating the claim as factual.",
            )

        return None
