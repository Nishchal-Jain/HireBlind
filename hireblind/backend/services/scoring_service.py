from __future__ import annotations

import re
from collections import Counter
from typing import List, Tuple


STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "are",
    "you",
    "your",
    "will",
    "have",
    "from",
    "into",
    "our",
    "we",
    "they",
    "their",
    "as",
    "to",
    "of",
    "in",
    "on",
    "at",
    "by",
    "an",
    "be",
    "or",
    "is",
    "it",
    "a",
    "job",
    "role",
    "experience",
    "years",
    "year",
    "required",
    "preferred",
    "skills",
    "skill",
    "responsibilities",
}

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9\+\#\.]{1,}")
YEARS_RE = re.compile(r"(\d{1,2})\s*\+?\s*years?\b", flags=re.IGNORECASE)


# Tech/important tokens used for refined scoring.
# This is intentionally small and hackathon-friendly; admins can influence scoring
# by using these terms in their job description.
TECH_KEYWORDS = {
    # Languages / frameworks
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "html",
    "html5",
    "css",
    "css3",
    "node",
    "nodejs",
    "express",
    "nextjs",
    "django",
    "fastapi",
    "flask",
    # Data / storage
    "sql",
    "postgres",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    # API / architecture
    "rest",
    "graphql",
    "api",
    "microservices",
    # Auth / security
    "jwt",
    "authentication",
    "authorization",
    "security",
    "oauth",
    # DevOps / tooling
    "docker",
    "kubernetes",
    "aws",
    "gcp",
    "azure",
    "terraform",
    "ci",
    "cd",
    "github",
    "git",
    # UI / build tooling
    "vite",
    "tailwind",
    "webpack",
    "tailwindcss",
    # Other tech tokens commonly seen in resumes
    "c++",
    "c#",
    ".net",
    "openapi",
    "swagger",
    "linux",
    "kafka",
    "rabbitmq",
    "nginx",
    # Privacy/Compliance
    "privacy",
    "compliance",
}

# Extra “important” keywords (still matched as tokens).
IMPORTANT_KEYWORDS = {
    "data",
    "engineering",
    "scalability",
    "performance",
    "testing",
    "quality",
    "audit",
    "evidence",
    "pipeline",
    "ranking",
    "scoring",
}


SECTION_HEADINGS_RE = re.compile(
    r"(?i)^\s*(required|preferred|technologies|technology|tech\s*stack|skills|skill|must have|nice to have)\s*[:\-]?",
    flags=re.IGNORECASE,
)


def _extract_scoring_text(job_description: str) -> str:
    """
    Refined scoring: only consider lines/sections likely to contain
    the *tech stack* and key requirements, instead of every token.
    """
    lines = [ln.strip() for ln in (job_description or "").splitlines()]
    if not lines:
        return ""

    selected: list[str] = []
    for ln in lines:
        if not ln:
            continue
        if SECTION_HEADINGS_RE.search(ln):
            selected.append(ln)
            continue
        # Include bullet-ish lines that are typically tech/skill lists.
        if (ln.startswith("-") or ln.startswith("*") or ln.startswith("•")) and len(ln) <= 200:
            selected.append(ln)
            continue
        # Include “inline tech stack” lines.
        if re.search(r"(?i)\b(tech|stack|skills|technologies|required|preferred)\b", ln):
            selected.append(ln)

    scoring_text = "\n".join(selected).strip()
    # Fallback: if admin didn't use headings/bullets, fall back to full text.
    return scoring_text if scoring_text else (job_description or "")


def _is_scoring_keyword(tok_original: str, tok_lower: str) -> bool:
    if tok_lower in STOPWORDS:
        return False
    if tok_lower in TECH_KEYWORDS or tok_lower in IMPORTANT_KEYWORDS:
        return True
    # Tokens containing punctuation are likely tech identifiers (e.g., C++, C#, .NET).
    if re.search(r"[+\#\.]", tok_original):
        return True
    return False


def _extract_keywords(job_description: str, max_keywords: int = 25) -> List[str]:
    scoring_text = _extract_scoring_text(job_description)
    tokens = TOKEN_RE.findall(scoring_text or "")
    if not tokens:
        return []

    representative: dict[str, str] = {}
    counts: Counter[str] = Counter()

    for tok in tokens:
        tok = tok.rstrip(".,;:")
        if len(tok) < 3:
            continue
        low = tok.lower()
        if not _is_scoring_keyword(tok, low):
            continue
        counts[low] += 1
        representative.setdefault(low, tok)

    # If nothing matched our refined keyword lists, fall back to the old behavior
    # so the UI still shows something rather than a blank score.
    if not counts:
        raw_tokens = TOKEN_RE.findall(job_description or "")
        for tok in raw_tokens:
            tok = tok.rstrip(".,;:")
            if len(tok) < 3:
                continue
            low = tok.lower()
            if low in STOPWORDS:
                continue
            counts[low] += 1
            representative.setdefault(low, tok)

    most_common = counts.most_common(max_keywords)
    return [representative[low] for low, _ in most_common]


def _extract_required_years(job_description: str) -> int | None:
    years = [int(m.group(1)) for m in YEARS_RE.finditer(job_description or "")]
    return max(years) if years else None


def _extract_resume_years(resume_text: str) -> int | None:
    years = [int(m.group(1)) for m in YEARS_RE.finditer(resume_text or "")]
    return max(years) if years else None


def _token_matches_resume(resume_lower: str, keyword: str) -> bool:
    """
    Reduce false positives by using word-boundary matching for pure alnum tokens.
    For tech identifiers with punctuation (C++, C#, .NET), use substring matching.
    """
    kw = keyword.lower()
    if re.match(r"^[a-z0-9]+$", kw):
        # Word-boundary match for cleaner precision.
        return re.search(rf"\b{re.escape(kw)}\b", resume_lower) is not None
    return kw in resume_lower


def score_resume(job_description: str, anonymised_resume_text: str) -> Tuple[int, List[str]]:
    """
    Score = percentage of extracted job keywords that appear in the anonymised resume text.
    Explanation tags include found keyword matches and (if possible) a years-of-experience check.
    """
    keywords = _extract_keywords(job_description)
    resume_lower = (anonymised_resume_text or "").lower()

    found_keywords: list[str] = []
    for kw in keywords:
        if _token_matches_resume(resume_lower, kw):
            found_keywords.append(kw)

    keyword_score = 0
    if keywords:
        keyword_score = int(round((len(found_keywords) / len(keywords)) * 100))

    explanation: List[str] = [f"{kw} ✓" for kw in found_keywords[:6]]

    required_years = _extract_required_years(job_description)
    if required_years is not None:
        resume_years = _extract_resume_years(anonymised_resume_text)
        if resume_years is not None and resume_years >= required_years:
            explanation.append(f"{required_years} years experience ✓")

    # Confidence score is the keyword match score (0-100).
    confidence = max(0, min(100, keyword_score))
    return confidence, explanation

