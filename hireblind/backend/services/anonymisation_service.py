from __future__ import annotations

import re
from functools import lru_cache
from typing import Optional


EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
# Pragmatic phone matcher (US-ish, but works for most resumes).
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s\-\.]?)?(?:\(?\d{3}\)?[\s\-\.]?)\d{3}[\s\-\.]?\d{4}")
GENDER_RE = re.compile(r"\b(he|she|him|her)\b", flags=re.IGNORECASE)
GENDER_PAIR_RE = re.compile(r"\b(he/she|him/her)\b", flags=re.IGNORECASE)

UNIVERSITY_KEYWORDS_RE = re.compile(r"\b(university|college|institute|school)\b", flags=re.IGNORECASE)


@lru_cache(maxsize=1)
def _load_spacy_model() -> Optional[object]:
    """
    Load spaCy when available.
    In constrained environments (like some local Windows setups), spaCy may not install.
    In that case we return None and fall back to heuristics so the app remains runnable.
    """
    try:
        import spacy  # type: ignore

        return spacy.load("en_core_web_sm")
    except Exception:
        return None


def _next_letter(n: int) -> str:
    letters = ["A", "B", "C"]
    return letters[n % len(letters)]


class AnonymisationService:
    def anonymize(self, text: str, candidate_letter: str) -> tuple[str, list[str]]:
        """
        Returns:
          anonymised_text: string with PII replaced
          removed_fields: list of field categories that were removed (for audit logging)
        """
        candidate_placeholder = f"Candidate {candidate_letter}"
        removed_fields: set[str] = set()

        if not text.strip():
            return "", []

        # Try spaCy NER first. If unavailable, use lightweight heuristics.
        nlp = _load_spacy_model()

        # Build replacements from spaCy entities first, using character spans.
        # We store university entities separately so we can map them to University A/B/C.
        university_map: dict[str, str] = {}
        next_uni_index = 0

        spans: list[tuple[int, int, str, str]] = []
        # (start, end, replacement, removed_field_category)

        if nlp is not None:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    spans.append((ent.start_char, ent.end_char, candidate_placeholder, "name"))
                elif ent.label_ in {"GPE", "LOC"}:
                    spans.append((ent.start_char, ent.end_char, candidate_placeholder, "location"))
                elif ent.label_ == "ORG":
                    if UNIVERSITY_KEYWORDS_RE.search(ent.text or ""):
                        uni_norm = (ent.text or "").strip().lower()
                        if uni_norm not in university_map:
                            university_map[uni_norm] = f"University {_next_letter(next_uni_index)}"
                            next_uni_index += 1
                        spans.append(
                            (ent.start_char, ent.end_char, university_map[uni_norm], "university")
                        )
        else:
            # Heuristic fallbacks (best-effort) so the app can still run locally.
            # Name heuristic: 2+ capitalized words (e.g., "John Doe", "Maria Gomez").
            name_re = re.compile(r"\b(?:[A-Z][a-z]+)\s+(?:[A-Z][a-z]+)(?:\s+[A-Z][a-z]+)?\b")
            for m in name_re.finditer(text):
                spans.append((m.start(), m.end(), candidate_placeholder, "name"))

            # Location heuristic: "City, ST" or "City, Country"
            location_re = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*(?:[A-Z]{2}|[A-Z][a-z]+)\b")
            for m in location_re.finditer(text):
                spans.append((m.start(), m.end(), candidate_placeholder, "location"))

            # University heuristic: anything containing "University/College/Institute/School"
            uni_re = re.compile(r"([A-Za-z0-9&'\\-\\.\\s]+(?:University|College|Institute|School)[A-Za-z0-9&'\\-\\.\\s]*)")
            for m in uni_re.finditer(text):
                uni_text = (m.group(1) or "").strip()
                if not uni_text:
                    continue
                uni_norm = uni_text.lower()
                if uni_norm not in university_map:
                    university_map[uni_norm] = f"University {_next_letter(next_uni_index)}"
                    next_uni_index += 1
                spans.append((m.start(), m.end(), university_map[uni_norm], "university"))

        spans.sort(key=lambda s: s[0])
        # Avoid overlapping replacements (best-effort; spaCy spans rarely overlap for these labels).
        merged: list[tuple[int, int, str, str]] = []
        last_end = -1
        for start, end, repl, field in spans:
            if start < last_end:
                continue
            merged.append((start, end, repl, field))
            last_end = end

        redacted = text
        if merged:
            out: list[str] = []
            cursor = 0
            for start, end, repl, field in merged:
                out.append(redacted[cursor:start])
                out.append(repl)
                cursor = end
                removed_fields.add(field)
            out.append(redacted[cursor:])
            redacted = "".join(out)

        # Now remove PII via regex (these don't need NER indices).
        # Emails
        if EMAIL_RE.search(redacted):
            redacted = EMAIL_RE.sub(candidate_placeholder, redacted)
            removed_fields.add("email")

        # Phones
        if PHONE_RE.search(redacted):
            redacted = PHONE_RE.sub(candidate_placeholder, redacted)
            removed_fields.add("phone")

        # Gender
        if GENDER_PAIR_RE.search(redacted):
            redacted = GENDER_PAIR_RE.sub(candidate_placeholder, redacted)
            removed_fields.add("gender")
        if GENDER_RE.search(redacted):
            redacted = GENDER_RE.sub(candidate_placeholder, redacted)
            removed_fields.add("gender")

        return redacted, sorted(removed_fields)

