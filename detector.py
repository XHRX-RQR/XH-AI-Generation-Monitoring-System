"""
AI Generated Content Detector - Core Detection Engine

Multi-round LLM-based detection using OpenAI-compatible API.
Uses plain-text labeled output for maximum API compatibility.
"""

import re
import time
import requests
from prompts import get_round1_messages, get_round2_messages, get_round3_messages


class DetectionError(Exception):
    """Custom exception for detection failures."""
    pass


def _extract_field(text: str, label: str, default: str = "") -> str:
    """Extract a labeled field value from plain-text LLM output."""
    pattern = re.compile(rf"^{re.escape(label)}:\s*(.+)$", re.MULTILINE | re.IGNORECASE)
    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    # Fallback: try without the colon (some APIs strip colons)
    pattern2 = re.compile(rf"^{re.escape(label)}\s+(.+)$", re.MULTILINE | re.IGNORECASE)
    match2 = pattern2.search(text)
    if match2:
        return match2.group(1).strip()
    return default


def _extract_int(text: str, label: str, default: int = 0) -> int:
    """Extract an integer field value."""
    raw = _extract_field(text, label, str(default))
    # Extract first number found in the value
    num = re.search(r"\d+", raw)
    return int(num.group()) if num else default


def _parse_round1(text: str) -> dict:
    """Parse Round 1 plain-text response into structured dict."""
    return {
        "lexical_diversity": {
            "score": _extract_int(text, "LEXICAL_DIVERSITY_SCORE", 5),
            "evidence": _extract_field(text, "LEXICAL_DIVERSITY_EVIDENCE", "N/A"),
        },
        "sentence_burstiness": {
            "score": _extract_int(text, "BURSTINESS_SCORE", 5),
            "evidence": _extract_field(text, "BURSTINESS_EVIDENCE", "N/A"),
        },
        "discourse_patterns": {
            "score": _extract_int(text, "DISCOURSE_SCORE", 5),
            "evidence": _extract_field(text, "DISCOURSE_EVIDENCE", "N/A"),
        },
        "content_semantics": {
            "score": _extract_int(text, "SEMANTICS_SCORE", 5),
            "evidence": _extract_field(text, "SEMANTICS_EVIDENCE", "N/A"),
        },
        "stylistic_consistency": {
            "score": _extract_int(text, "CONSISTENCY_SCORE", 5),
            "evidence": _extract_field(text, "CONSISTENCY_EVIDENCE", "N/A"),
        },
        "preliminary_assessment": _extract_field(text, "PRELIMINARY_ASSESSMENT", "Uncertain"),
        "confidence": _extract_int(text, "PRELIMINARY_CONFIDENCE", 50),
    }


def _parse_round2(text: str) -> dict:
    """Parse Round 2 plain-text response into structured dict."""
    key_evidence = []
    for i in range(1, 6):
        ev = _extract_field(text, f"KEY_EVIDENCE_{i}", "")
        if ev and ev != "N/A":
            key_evidence.append(ev)

    return {
        "micro_patterns": {
            "score": _extract_int(text, "MICRO_PATTERNS_SCORE", 5),
            "details": _extract_field(text, "MICRO_PATTERNS_DETAILS", "N/A"),
        },
        "semantic_depth": {
            "score": _extract_int(text, "SEMANTIC_DEPTH_SCORE", 5),
            "details": _extract_field(text, "SEMANTIC_DEPTH_DETAILS", "N/A"),
        },
        "linguistic_fingerprint": {
            "score": _extract_int(text, "FINGERPRINT_SCORE", 5),
            "details": _extract_field(text, "FINGERPRINT_DETAILS", "N/A"),
        },
        "ai_telltales": {
            "score": _extract_int(text, "AI_TELLTALES_SCORE", 5),
            "details": _extract_field(text, "AI_TELLTALES_DETAILS", "N/A"),
        },
        "revised_assessment": _extract_field(text, "REVISED_ASSESSMENT", "Uncertain"),
        "revised_confidence": _extract_int(text, "REVISED_CONFIDENCE", 50),
        "key_evidence": key_evidence,
    }


def _parse_round3(text: str) -> dict:
    """Parse Round 3 plain-text response into structured dict."""
    indicators = []
    for i in range(1, 7):
        feature = _extract_field(text, f"INDICATOR_{i}_FEATURE", "")
        if feature and feature != "N/A":
            indicators.append({
                "feature": feature,
                "signal": _extract_field(text, f"INDICATOR_{i}_SIGNAL", "AI"),
                "strength": _extract_field(text, f"INDICATOR_{i}_STRENGTH", "Moderate"),
                "detail": _extract_field(text, f"INDICATOR_{i}_DETAIL", ""),
            })

    caveats = []
    for i in range(1, 4):
        c = _extract_field(text, f"CAVEAT_{i}", "")
        if c and c != "N/A":
            caveats.append(c)

    return {
        "verdict": _extract_field(text, "FINAL_VERDICT", "Inconclusive"),
        "confidence": _extract_int(text, "FINAL_CONFIDENCE", 50),
        "ai_probability": _extract_int(text, "AI_PROBABILITY", 50),
        "summary": _extract_field(text, "SUMMARY", "Analysis complete."),
        "key_indicators": indicators,
        "caveats": caveats,
    }


class AIDetector:
    """Multi-round AI content detector using LLM analysis."""

    def __init__(self, api_base: str, api_key: str, model: str,
                 temperature: float = 0.1, timeout: int = 120):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

    def _chat(self, messages: list) -> str:
        """Send a chat completion request to the OpenAI-compatible API."""
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": 4096,
        }

        try:
            resp = requests.post(url, json=payload, headers=headers,
                                 timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            raise DetectionError("API request timed out. Please check your API endpoint.")
        except requests.exceptions.ConnectionError:
            raise DetectionError("Cannot connect to API endpoint. Please verify the URL.")
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "unknown"
            raise DetectionError(f"API returned HTTP {status}. Check your API key and endpoint.")
        except (KeyError, IndexError):
            raise DetectionError("Unexpected API response format.")

    def detect(self, text: str, progress_callback=None) -> dict:
        """
        Run the full 3-round detection pipeline.

        Args:
            text: The text to analyze.
            progress_callback: Optional callable(round_num, round_name, result_str)

        Returns:
            Final detection result dict with verdict, confidence, and analysis details.
        """
        if not text or not text.strip():
            raise DetectionError("Input text is empty.")

        if len(text.strip()) < 50:
            raise DetectionError("Input text is too short (minimum 50 characters) for reliable analysis.")

        start = time.time()

        # ── Round 1: Initial Feature Extraction ──
        if progress_callback:
            progress_callback(1, "Initial Feature Extraction", None)

        r1_messages = get_round1_messages(text)
        r1_raw = self._chat(r1_messages)
        r1_parsed = _parse_round1(r1_raw)

        if progress_callback:
            progress_callback(1, "Initial Feature Extraction", r1_raw)

        # ── Round 2: Deep Pattern Analysis ──
        if progress_callback:
            progress_callback(2, "Deep Pattern Analysis", None)

        r2_messages = get_round2_messages(text, r1_raw)
        r2_raw = self._chat(r2_messages)
        r2_parsed = _parse_round2(r2_raw)

        if progress_callback:
            progress_callback(2, "Deep Pattern Analysis", r2_raw)

        # ── Round 3: Final Synthesis ──
        if progress_callback:
            progress_callback(3, "Final Synthesis & Verdict", None)

        r3_messages = get_round3_messages(r1_raw, r2_raw)
        r3_raw = self._chat(r3_messages)
        r3_parsed = _parse_round3(r3_raw)

        if progress_callback:
            progress_callback(3, "Final Synthesis & Verdict", r3_raw)

        elapsed = round(time.time() - start, 2)

        # Build final response
        final = {
            "verdict": r3_parsed.get("verdict", "Inconclusive"),
            "confidence": r3_parsed.get("confidence", 0),
            "ai_probability": r3_parsed.get("ai_probability", 0),
            "summary": r3_parsed.get("summary", ""),
            "key_indicators": r3_parsed.get("key_indicators", []),
            "caveats": r3_parsed.get("caveats", []),
            "analysis_rounds": {
                "round1_features": r1_parsed,
                "round2_deep_analysis": r2_parsed,
            },
            "elapsed_seconds": elapsed,
            "text_length": len(text),
            "model_used": self.model,
        }
        return final
