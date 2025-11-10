"""
InterruptHandler Module
-----------------------
Enhances LiveKit agents to intelligently handle user voice interruptions.
It ignores filler words ("uh", "umm", "hmm", "haan") while the agent speaks,
but recognizes real commands ("wait", "stop", etc.) instantly.
"""

import asyncio
import re
import time
from enum import Enum
from typing import List, Dict, Optional

# Define decision types for clarity
class Decision(Enum):
    IGNORED = "ignored"
    INTERRUPT = "interrupt"
    FORWARDED = "forwarded"

# Helper: simple word tokenizer
def tokenize(text: str) -> List[str]:
    return re.findall(r"\w+", (text or "").lower())

# --- Multilingual filler normalization ---
def normalize_text(text: str) -> str:
    """
    Normalize text to handle multilingual fillers (Hindi + English mix).
    Example: 'acha', 'achha', 'haan', 'haanji', 'ummm', 'hmmm', etc.
    """
    text = text.lower().strip()

    # Replace common Hindi/English filler variants with canonical forms
    replacements = {
        r"ach+?a+": "acha",
        r"ha+?n+": "haan",
        r"arre+": "arre",
        r"umm+": "umm",
        r"uh+": "uh",
        r"hmm+": "hmm",
        r"em+": "em",
        r"ok+?ay*": "ok",
        r"th(e)?ek\s*hai": "theek hai",
        r"cha?lo+": "chalo",
    }

    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)

    return text


# Default configuration
DEFAULT_IGNORED = ["uh", "um", "umm", "hmm", "haan", "acha", "em", "arre", "chalo", "theek", "theek hai"]


DEFAULT_STOP_WORDS = ["stop", "wait", "hold on", "pause", "no not that one"]

class AgentState:
    """Keeps track of whether the agent is currently speaking."""
    def __init__(self):
        self._lock = asyncio.Lock()
        self._speaking = False

    async def set_speaking(self, value: bool):
        async with self._lock:
            self._speaking = value

    async def is_speaking(self) -> bool:
        async with self._lock:
            return self._speaking


class InterruptHandler:
    """
    Handles real-time voice transcripts from ASR (Automatic Speech Recognition)
    to decide whether the agent should ignore, interrupt, or forward the speech.
    """

    def __init__(
        self,
        ignored_words: Optional[List[str]] = None,
        stop_words: Optional[List[str]] = None,
        confidence_threshold: float = 0.5,
        low_confidence_threshold: float = 0.35,
    ):
        self.ignored_words = set((ignored_words or DEFAULT_IGNORED))
        self.stop_words = set((stop_words or DEFAULT_STOP_WORDS))
        self.confidence_threshold = confidence_threshold
        self.low_confidence_threshold = low_confidence_threshold
        self.agent_state = AgentState()
        self._logs: List[Dict] = []

    def update_ignored_words(self, new_words: List[str]):
            """
            Dynamically update the ignored filler words at runtime.
            """
            before = self.ignored_words.copy()
            self.ignored_words = set(new_words)
            print(f"[CONFIG] Ignored words updated from {before} -> {self.ignored_words}")


    async def handle_transcript(
        self, text: str, confidence: float, is_final: bool = True, metadata: Optional[Dict] = None
    ) -> Decision:
        """Main logic to decide whether to IGNORE, INTERRUPT, or FORWARD."""
        metadata = metadata or {}
        text = normalize_text(text)
        tokens = tokenize(text)
        tokens = [t for t in tokens if len(t) > 1]  # new: ignore 1-letter tokens

        speaking = await self.agent_state.is_speaking()

        

        # Case 1: agent is speaking and user sound is low-confidence (background murmur)
        if speaking and confidence <= self.low_confidence_threshold:
            self._log("IGNORED_LOW_CONF", text, confidence, metadata)
            return Decision.IGNORED
        
        def is_filler(word, ignored):
            for ig in ignored:
                # matches um, umm, ummm, uhhh, etc. safely
                if re.fullmatch(fr"{ig}+", word):
                    return True
            return False



        # Case 2: agent is speaking — check if it's filler or real interruption
        if speaking:
            # Remove filler tokens
            # Replace this
            for sw in self.stop_words:
                if sw and sw in text.lower():
                    self._log("INTERRUPT_STOP_WORD", text, confidence, metadata, {"matched": sw})
                    return Decision.INTERRUPT
#above part if a phrase like "umm okay stop" or "hmm wait" appears — the agent instantly stops before doing other checks.
            DISCOURSE = {"so", "anyway", "yeah", "well", "right", "like", "sure","ok"}

            # Keep "okay" special-cased
            def is_soft_acknowledgment(text: str) -> bool:
                cleaned = text.strip().lower()
                # "ok" or "okay" alone -> ignore
                if re.fullmatch(r"(ok(?:ay)?|haan|hmm|yeah)[.! ]*$", cleaned):
                    return True
                # "ok stop", "ok fine" etc. -> meaningful (not soft ack)
                return False

            if is_soft_acknowledgment(text):
                self._log("IGNORED_ACK", text, confidence, metadata)
                return Decision.IGNORED
            tokens = [t for t in tokens if t not in DISCOURSE]
#These are “flow” words — they don’t mean interruption but are often picked up as text.
#This ensures sentences like "uh so anyway yeah" don’t cause interruption.
            # Ignore incomplete short fragments like 'wa', 'st', 'wai' if confidence is low
            if speaking and all(len(t) <= 3 for t in tokens) and confidence < 0.7:
                self._log("IGNORED_PARTIAL_TOKENS", text, confidence, metadata, {"tokens": tokens})
                return Decision.IGNORED


            meaningful = [t for t in tokens if not is_filler(t, self.ignored_words)]
            if not meaningful:
                self._log("IGNORED_FILLER_OR_DISCOURSE", text, confidence, metadata)

                return Decision.IGNORED

            # If any stop/command word is present, interrupt immediately
            full_text = text.lower()
            for sw in self.stop_words:
                if sw in full_text:
                    self._log("INTERRUPT_STOP_WORD", text, confidence, metadata, {"matched": sw})
                    return Decision.INTERRUPT

            # Otherwise, treat as real interruption
            self._log("INTERRUPT_MEANINGFUL", text, confidence, metadata, {"tokens": meaningful})
            return Decision.INTERRUPT

        # Case 3: agent is NOT speaking — normal user speech
        if confidence < (self.confidence_threshold * 0.5):
            self._log("FORWARDED_LOW_CONF", text, confidence, metadata)
            return Decision.FORWARDED

        self._log("FORWARDED", text, confidence, metadata)
        return Decision.FORWARDED

    def _log(self, tag: str, text: str, conf: float, meta: Dict, extra: Dict = None):
        """Internal structured logging."""
        entry = {
            "event": tag,
            "text": text,
            "confidence": conf,
            "metadata": meta,
            "extra": extra or {},
            "timestamp": time.time(),
        }
        self._logs.append(entry)
        print(f"[{tag}] text='{text}' conf={conf:.2f} extra={extra or {}}")

    def get_logs(self) -> List[Dict]:
        """Returns logs for debugging."""
        return self._logs

