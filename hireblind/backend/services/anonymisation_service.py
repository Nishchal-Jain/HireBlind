from __future__ import annotations

import re
from functools import lru_cache
from typing import Optional


EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s\-\.]?)?(?:\(?\d{3}\)?[\s\-\.]?)\d{3}[\s\-\.]?\d{4}")
GENDER_RE = re.compile(r"\b(he|she|him|her)\b", flags=re.IGNORECASE)
GENDER_PAIR_RE = re.compile(r"\b(he/she|him/her)\b", flags=re.IGNORECASE)

UNIVERSITY_KEYWORDS_RE = re.compile(r"\b(university|college|institute|school)\b", flags=re.IGNORECASE)

# When spaCy marks "Java Developer" as PERSON, subtracting the protected "Java" leaves "Developer".
# Do not redact role-only fragments (keeps skills visible in anonymised text).
_ROLE_TITLE_TOKENS = frozenset(
    {
        "developer",
        "engineers",
        "engineer",
        "engineering",
        "architect",
        "architects",
        "manager",
        "managers",
        "lead",
        "consultant",
        "specialist",
        "specialists",
        "analyst",
        "analysts",
        "programmer",
        "designer",
        "designers",
        "admin",
        "administrator",
        "intern",
        "interns",
        "contractor",
        "devops",
        "sre",
        "software",
        "full",
        "stack",
        "frontend",
        "front-end",
        "backend",
        "back-end",
        "web",
        "mobile",
        "cloud",
        "data",
        "scientist",
        "product",
        "owner",
        "director",
    }
)
_ROLE_TITLE_MODIFIERS = frozenset(
    {
        "senior",
        "junior",
        "sr",
        "jr",
        "principal",
        "staff",
        "associate",
        "ii",
        "iii",
        "i",
    }
)

# Surface forms that must never be anonymised (languages, stacks, vendors). Used to build protected
# character ranges so spaCy NER (GPE "Java", PERSON on "Java Developer", etc.) cannot erase them.
_TECH_SURFACE_TERMS: tuple[str, ...] = (
    "javascript",
    "typescript",
    "python",
    "java",
    "ruby",
    "rust",
    "kotlin",
    "scala",
    "swift",
    "dart",
    "perl",
    "haskell",
    "elixir",
    "clojure",
    "matlab",
    "sql",
    "html",
    "html5",
    "css",
    "css3",
    "react",
    "angular",
    "vue",
    "node",
    "nodejs",
    "node.js",
    "golang",
    "jvm",
    "jdk",
    "jdbc",
    "jakarta",
    "nestjs",
    "hibernate",
    "spring",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "redis",
    "mongodb",
    "mysql",
    "postgres",
    "postgresql",
    "django",
    "flask",
    "fastapi",
    "express",
    "nextjs",
    "next.js",
    "vite",
    "webpack",
    "terraform",
    "graphql",
    "nginx",
    "kafka",
    "rabbitmq",
    "linux",
    "jenkins",
    "git",
    "github",
    "gitlab",
    "tailwind",
    "tailwindcss",
    "microservices",
    "openapi",
    "swagger",
    "oauth",
    "jwt",
    "rest",
    "springboot",
    "spring boot",
    "c++",
    "c#",
    ".net",
    "dotnet",
    "pandas",
    "numpy",
    "pytorch",
    "tensorflow",
    "spark",
    "hadoop",
    "snowflake",
    "databricks",
)


def _merge_intervals(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not ranges:
        return []
    ranges = sorted(ranges)
    out: list[tuple[int, int]] = [ranges[0]]
    for s, e in ranges[1:]:
        ls, le = out[-1]
        if s <= le:
            out[-1] = (ls, max(le, e))
        else:
            out.append((s, e))
    return out


def _subtract_interval(span: tuple[int, int], blocks: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Return sub-intervals of span that are not covered by merged blocks."""
    s, e = span
    if s >= e:
        return []
    if not blocks:
        return [(s, e)]
    cur = s
    out: list[tuple[int, int]] = []
    for bs, be in blocks:
        if be <= cur or bs >= e:
            continue
        if cur < bs:
            out.append((cur, min(bs, e)))
        cur = max(cur, be)
        if cur >= e:
            return [(a, b) for a, b in out if b > a]
    if cur < e:
        out.append((cur, e))
    return [(a, b) for a, b in out if b > a]


@lru_cache(maxsize=1)
def _tech_surface_pattern() -> re.Pattern[str]:
    """Protect the same tech surface forms scoring uses, plus legacy extras (Java must survive GPE / fake 'name' hits)."""
    from hireblind.backend.services.scoring_service import iter_tech_surface_forms

    by_lower: dict[str, str] = {}
    for t in _TECH_SURFACE_TERMS + tuple(iter_tech_surface_forms()):
        s = (t or "").strip()
        if not s:
            continue
        by_lower.setdefault(s.lower(), s)
    terms = sorted(by_lower.values(), key=len, reverse=True)
    parts: list[str] = []
    for t in terms:
        if " " in t:
            inner = r"\s+".join(re.escape(b) for b in t.split())
            parts.append(rf"(?<![A-Za-z0-9])(?:{inner})(?![A-Za-z0-9])")
            continue
        e = re.escape(t)
        if re.match(r"^[A-Za-z0-9]+$", t):
            parts.append(rf"\b{e}\b")
        else:
            parts.append(e)
    return re.compile("|".join(parts), flags=re.IGNORECASE)


def _protected_tech_ranges(text: str) -> list[tuple[int, int]]:
    pat = _tech_surface_pattern()
    raw = [(m.start(), m.end()) for m in pat.finditer(text)]
    return _merge_intervals(raw)


def _covered_length(span: tuple[int, int], protected: list[tuple[int, int]]) -> int:
    """How many chars of span [s,e) overlap protected tech intervals (after merge)."""
    s0, e0 = span
    if s0 >= e0:
        return 0
    n = 0
    for ps, pe in protected:
        lo = max(s0, ps)
        hi = min(e0, pe)
        if hi > lo:
            n += hi - lo
    return n


def _fragment_is_role_only(text: str, s: int, e: int) -> bool:
    raw = text[s:e].strip().lower()
    if not raw:
        return True
    parts = [p for p in re.split(r"[\s/,]+", raw) if p]
    if not parts:
        return True
    allowed = _ROLE_TITLE_TOKENS | _ROLE_TITLE_MODIFIERS
    return all(p.replace(".", "") in allowed for p in parts)


def _append_spans_minus_protected(
    text: str,
    spans: list[tuple[int, int, str, str]],
    span_ent: tuple[int, int],
    protected: list[tuple[int, int]],
    replacement: str,
    field: str,
) -> None:
    """Subtract protected tech ranges; skip whitespace-only gaps (stops name-regex eating 'Java Spring')."""
    for s, e in _subtract_interval(span_ent, protected):
        if e <= s:
            continue
        if not text[s:e].strip():
            continue
        if field == "name" and _fragment_is_role_only(text, s, e):
            continue
        spans.append((s, e, replacement, field))


@lru_cache(maxsize=1)
def _load_spacy_model() -> Optional[object]:
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
        candidate_placeholder = f"Candidate {candidate_letter}"
        removed_fields: set[str] = set()

        if not text.strip():
            return "", []

        protected = _protected_tech_ranges(text)

        nlp = _load_spacy_model()

        university_map: dict[str, str] = {}
        next_uni_index = 0

        spans: list[tuple[int, int, str, str]] = []

        if nlp is not None:
            doc = nlp(text)
            for ent in doc.ents:
                es, ee = ent.start_char, ent.end_char
                span = (es, ee)
                if ent.label_ == "PERSON":
                    _append_spans_minus_protected(text, spans, span, protected, candidate_placeholder, "name")
                elif ent.label_ in {"GPE", "LOC", "FAC"}:
                    _append_spans_minus_protected(text, spans, span, protected, candidate_placeholder, "location")
                elif ent.label_ == "ORG":
                    if UNIVERSITY_KEYWORDS_RE.search(ent.text or ""):
                        uni_norm = (ent.text or "").strip().lower()
                        if uni_norm not in university_map:
                            university_map[uni_norm] = f"University {_next_letter(next_uni_index)}"
                            next_uni_index += 1
                        repl = university_map[uni_norm]
                        _append_spans_minus_protected(text, spans, span, protected, repl, "university")
        else:
            # Use horizontal whitespace only — \s would join "Doe" and "Senior" across a newline.
            name_re = re.compile(
                r"\b(?:[A-Z][a-z]+)(?:[ \t]+(?:[A-Z][a-z]+)){1,2}\b"
            )
            for m in name_re.finditer(text):
                span_m = (m.start(), m.end())
                if _covered_length(span_m, protected) >= (m.end() - m.start()):
                    continue
                _append_spans_minus_protected(text, spans, span_m, protected, candidate_placeholder, "name")

            location_re = re.compile(
                r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*(?:[A-Z]{2}|[A-Z][a-z]+)\b"
            )
            for m in location_re.finditer(text):
                _append_spans_minus_protected(
                    text, spans, (m.start(), m.end()), protected, candidate_placeholder, "location"
                )

            uni_re = re.compile(
                r"([A-Za-z0-9&'\\-\\.\\s]+(?:University|College|Institute|School)[A-Za-z0-9&'\\-\\.\\s]*)"
            )
            for m in uni_re.finditer(text):
                uni_text = (m.group(1) or "").strip()
                if not uni_text:
                    continue
                uni_norm = uni_text.lower()
                if uni_norm not in university_map:
                    university_map[uni_norm] = f"University {_next_letter(next_uni_index)}"
                    next_uni_index += 1
                repl = university_map[uni_norm]
                _append_spans_minus_protected(text, spans, (m.start(), m.end()), protected, repl, "university")

        spans.sort(key=lambda s: s[0])
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

        if EMAIL_RE.search(redacted):
            redacted = EMAIL_RE.sub(candidate_placeholder, redacted)
            removed_fields.add("email")

        if PHONE_RE.search(redacted):
            redacted = PHONE_RE.sub(candidate_placeholder, redacted)
            removed_fields.add("phone")

        if GENDER_PAIR_RE.search(redacted):
            redacted = GENDER_PAIR_RE.sub(candidate_placeholder, redacted)
            removed_fields.add("gender")
        if GENDER_RE.search(redacted):
            redacted = GENDER_RE.sub(candidate_placeholder, redacted)
            removed_fields.add("gender")

        return redacted, sorted(removed_fields)
