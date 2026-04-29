"""
Shared helper utilities for automation fill flows.
"""

from __future__ import annotations

import re


def normalize_text(text: str | None) -> str:
    if not text:
        return ""

    text = text.lower().strip()
    text = text.replace("’", "'")
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("don't", "do not")
    text = text.replace("dont", "do not")

    return re.sub(r"[^a-z0-9\s]", "", text).strip()


def normalize_choice_text(text: str | None) -> str:
    text = normalize_text(text)

    synonym_map = {
        "prefer not to self identify": "prefer not to answer",
        "prefer not to selfidentify": "prefer not to answer",
        "prefer not to self-identify": "prefer not to answer",
        "do not wish to answer": "prefer not to answer",
        "choose not to disclose": "prefer not to answer",
        "decline to answer": "prefer not to answer",
        "i do not wish to answer": "prefer not to answer",
        "i prefer not to answer": "prefer not to answer",
        "i do not have a disability": "no disability",
        "no i do not have a disability": "no disability",
        "no i dont have a disability": "no disability",
        "no i do not have disability": "no disability",
        "i am not a protected veteran": "not a protected veteran",
        "no i am not a protected veteran": "not a protected veteran",
        "not a veteran": "not a protected veteran",
    }

    for source, target in synonym_map.items():
        text = text.replace(source, target)

    return re.sub(r"[^a-z0-9\s]", "", text).strip()


def score_choice_match(target_value: str | None, option_text: str | None) -> int:
    target_norm = normalize_choice_text(target_value)
    option_norm = normalize_choice_text(option_text)

    if not target_norm or not option_norm:
        return 0

    if target_norm == option_norm:
        return 100

    if target_norm in option_norm:
        return 90

    if option_norm in target_norm:
        return 85

    target_tokens = set(target_norm.split())
    option_tokens = set(option_norm.split())
    overlap = len(target_tokens & option_tokens)

    if overlap == 0:
        return 0

    token_score = int((overlap / max(len(target_tokens), 1)) * 70)
    semantic_bonus = 0

    if "prefer not to answer" in target_norm:
        if any(
            phrase in option_norm
            for phrase in [
                "prefer not to answer",
                "prefer not to self identify",
                "prefer not to selfidentify",
                "do not wish to answer",
                "choose not to disclose",
                "decline to answer",
                "not wish to answer",
            ]
        ):
            semantic_bonus = 30

    if "not a protected veteran" in target_norm:
        if any(
            phrase in option_norm
            for phrase in [
                "not a protected veteran",
                "no i am not a protected veteran",
                "i am not a protected veteran",
                "not protected veteran",
            ]
        ):
            semantic_bonus = 30

    if "no disability" in target_norm:
        if any(
            phrase in option_norm
            for phrase in [
                "no disability",
                "do not have a disability",
                "do not have disability",
                "i do not have a disability",
                "no i do not have a disability",
                "no i do not have disability",
            ]
        ):
            semantic_bonus = 30

    return min(99, token_score + semantic_bonus)


def combobox_value_changed(before_value: str | None, after_value: str | None) -> bool:
    before_norm = normalize_choice_text(before_value)
    after_norm = normalize_choice_text(after_value)

    if not after_norm:
        return False

    if after_norm in {"select", "select option", "select answer"}:
        return False

    return after_norm != before_norm


def is_backing_input_label(label: str | None) -> bool:
    normalized = normalize_text(label)
    return normalized in {"select", "select option", "select answer"}