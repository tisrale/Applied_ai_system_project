"""
Gemini client wrapper, plus a FakeGemini for tests.

Both expose the same method:
    generate(prompt, json_mode=False) -> str

The rest of the system only talks to that method, so tests can swap in FakeGemini
and run with no API key and no network.

The API key is read from GEMINI_API_KEY (in .env). It is never printed or logged.
"""

import logging
import os
import re
import time
from typing import Callable, List, Optional

logger = logging.getLogger("vibejudge")

# Override with GEMINI_MODEL in .env if this model is ever retired.
# ("gemini-flash-lite-latest" from earlier projects now returns 404.)
DEFAULT_MODEL = "gemini-3.5-flash-lite"

# Free tier allows 15 requests/minute. On 429 (quota) or 503 (overloaded) we wait and retry,
# but never longer than this, so the app doesn't hang.
MAX_RETRY_WAIT = 20.0


def _retry_wait(exc: Exception) -> Optional[float]:
    """Seconds to wait before retrying, or None if the error isn't worth retrying."""
    code = getattr(exc, "code", None)
    if code == 503:
        return 2.0
    if code == 429:
        match = re.search(r"retryDelay'?:\s*'(\d+(?:\.\d+)?)s", str(exc))
        return min(float(match.group(1)) + 1 if match else 10.0, MAX_RETRY_WAIT)
    return None


class LLMError(RuntimeError):
    """Raised when the model can't be reached or returns nothing usable."""


class GeminiClient:
    """Thin wrapper around google-genai's generate_content."""

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None, max_retries: int = 1):
        from dotenv import load_dotenv
        from google import genai

        load_dotenv()
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise LLMError("GEMINI_API_KEY is not set. Copy .env.example to .env and add your key.")
        self._client = genai.Client(api_key=key)
        self.model = model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
        self.name = f"gemini:{self.model}"
        self.max_retries = max_retries

    def generate(self, prompt: str, json_mode: bool = False, temperature: float = 0.2) -> str:
        """Send one prompt and return the reply text. json_mode asks Gemini for pure JSON."""
        from google.genai import types

        config = types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json" if json_mode else None,
        )
        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.models.generate_content(model=self.model, contents=prompt, config=config)
                break
            except Exception as exc:  # network, quota, bad model name, ...
                wait = _retry_wait(exc)
                if wait is None or attempt == self.max_retries:
                    raise LLMError(f"Gemini call failed ({type(exc).__name__}): {exc}") from exc
                logger.warning("Gemini busy (%s), retrying in %.0fs", getattr(exc, "code", "?"), wait)
                time.sleep(wait)
        text = (response.text or "").strip()
        if not text:
            raise LLMError("Gemini returned an empty response")
        return text


class FakeGemini:
    """Stand-in for GeminiClient in tests: no key, no network, fully predictable.

    Give it either a list of canned replies (returned in order) or a handler
    function that builds a reply from the prompt. fail=True simulates an outage.
    Every prompt it receives is kept in .prompts so tests can inspect them.
    """

    def __init__(self, responses: Optional[List[str]] = None,
                 handler: Optional[Callable[[str], str]] = None, fail: bool = False):
        self.responses = list(responses or [])
        self.handler = handler
        self.fail = fail
        self.prompts: List[str] = []
        self.name = "fake"

    def generate(self, prompt: str, json_mode: bool = False, temperature: float = 0.2) -> str:
        self.prompts.append(prompt)
        if self.fail:
            raise LLMError("FakeGemini simulated outage")
        if self.handler:
            return self.handler(prompt)
        if not self.responses:
            raise LLMError("FakeGemini ran out of canned responses")
        return self.responses.pop(0)


def get_llm(offline: bool = False):
    """Return a GeminiClient, or None for offline mode (keyword parser + template explanations)."""
    if offline:
        return None
    return GeminiClient()
