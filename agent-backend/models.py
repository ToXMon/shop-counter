"""Centralized Gemini model and agent identifiers from the Builder Guide (p. 3-4).

All model strings in agent-backend MUST be imported from this module.
Do not use GEMINI_MODEL as a global selector.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv
from google import genai

# Load .env from repo root or agent-backend/ if present (without overriding existing env vars)
_MODULE_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _MODULE_DIR.parent
for _env_candidate in (_MODULE_DIR / ".env", _REPO_ROOT / ".env"):
    if _env_candidate.is_file():
        load_dotenv(_env_candidate, override=False)

MODEL_IDS: Final[dict[str, str]] = {
    # Gemini 4 reasoning and coding models (1M unified context + long decode)
    "frontier_deep": "gemini-4-carbon",
    "frontier_fast": "gemini-4-neon",
    "fast_workhorse": "gemini-4-hydrogen",
    "frontier_argon": "gemini-4-argon",
    "text_fast_lite": "gemini-3.5-flash-lite",
    # Calibrated multimodal routing, gating, and rubric scoring (v1beta)
    "decisions": "gemini-decision-1",
    # Managed agents (v1beta)
    "antigravity_agent": "antigravity-preview-09-2026",
    "deep_research": "deep-research-preview-04-2026",
    "deep_research_max": "deep-research-max-preview-04-2026",
    # Live voice, camera, transcription, translation, and speech
    "live_voice_vision": "gemini-3.8-live",
    "live_extended_thinking": "gemini-3.8-live-extended-thinking",
    "transcribe_batch": "gemini-3.5-transcribe",
    "transcribe_live": "gemini-3.5-transcribe-live",
    "live_translate": "gemini-3.5-live-translate-preview",
    "tts_studio": "gemini-3.8-flash-tts",
    "tts_fast": "gemini-3.8-flash-lite-tts",
    # Native images, video with audio, and music
    "image_default": "gemini-nano-banana-2.1",
    "image_pro": "gemini-3-pro-image",
    "image_fast": "gemini-3.1-flash-lite-image",
    "video_audio": "gemini-omni-1.2-flash",
    "music_song": "lyria-3.5",
    "music_loop": "lyria-3-clip-preview",
    # Open-weight Gemma 4 models on the Interactions API
    "gemma_dense": "gemma-4-31b-it",
    "gemma_moe": "gemma-4-26b-a4b-it",
}

# Role-specific aliases used across agent-backend (docs/INTERFACES.md section 3)
AGENT_MODEL: Final[str] = MODEL_IDS["frontier_fast"]          # gemini-4-neon
WORKER_MODEL: Final[str] = MODEL_IDS["fast_workhorse"]        # gemini-4-hydrogen
DECISION_MODEL: Final[str] = MODEL_IDS["decisions"]           # gemini-decision-1
TRANSCRIBE_MODEL: Final[str] = MODEL_IDS["transcribe_batch"]  # gemini-3.5-transcribe
TTS_MODEL: Final[str] = MODEL_IDS["tts_studio"]               # gemini-3.8-flash-tts
MANAGED_AGENT_ID: Final[str] = MODEL_IDS["antigravity_agent"] # antigravity-preview-09-2026


def require_api_key() -> str:
    """Return GEMINI_API_KEY from environment or raise RuntimeError cleanly."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is missing from environment / .env")
    return key


def get_client() -> genai.Client:
    """Stable v1 client for Interactions API model calls."""
    return genai.Client(api_key=require_api_key())


def get_beta_client() -> genai.Client:
    """v1beta client for Managed Agents, Environments, and the Decisions API."""
    return genai.Client(api_key=require_api_key(), http_options={"api_version": "v1beta"})
