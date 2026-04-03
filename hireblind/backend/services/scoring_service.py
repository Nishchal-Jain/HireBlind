from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any, Dict, List, Tuple


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

# Job/resume tokens: first char alpha, rest allows tech punctuation (C#, node.js, ci/cd).
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9\+\#\.]{1,}")
YEARS_RE = re.compile(r"(\d{1,2})\s*\+?\s*years?\b", flags=re.IGNORECASE)

# Multi-word technology / practice phrases (scored as units).
KEYWORD_PHRASES = [
    "machine learning",
    "computer vision",
    "natural language",
    "deep learning",
    "rest api",
    "rest apis",
    "data privacy",
    "data engineering",
    "full stack",
    "full-stack",
    "ci/cd",
    "object oriented",
    "test driven",
    "spring boot",
    "spring mvc",
    "unit testing",
    "integration testing",
    "ruby on rails",
    "react native",
    "asp.net",
    ".net core",
    "java ee",
    "jakarta ee",
]

# Curated technology vocabulary only — no generic English “importance” words.
TECH_KEYWORDS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "react",
    "angular",
    "vue",
    "svelte",
    "html",
    "html5",
    "css",
    "css3",
    "node",
    "nodejs",
    "golang",
    "express",
    "nextjs",
    "nestjs",
    "django",
    "fastapi",
    "flask",
    "spring",
    "hibernate",
    "junit",
    "maven",
    "gradle",
    "kotlin",
    "scala",
    "swift",
    "dart",
    "go",
    "rust",
    "ruby",
    "php",
    "laravel",
    "sql",
    "nosql",
    "postgres",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "elasticsearch",
    "snowflake",
    "databricks",
    "rest",
    "graphql",
    "grpc",
    "api",
    "openapi",
    "swagger",
    "microservices",
    "kafka",
    "rabbitmq",
    "nginx",
    "jwt",
    "oauth",
    "authentication",
    "authorization",
    "docker",
    "kubernetes",
    "helm",
    "aws",
    "gcp",
    "azure",
    "terraform",
    "ansible",
    "jenkins",
    "github",
    "gitlab",
    "git",
    "ci",
    "cd",
    "vite",
    "webpack",
    "rollup",
    "tailwind",
    "tailwindcss",
    "c++",
    "c#",
    ".net",
    "linux",
    "unix",
    "bash",
    "pandas",
    "numpy",
    "pytorch",
    "tensorflow",
    "scikit",
    "spark",
    "hadoop",
    "airflow",
    "dbt",
    "privacy",
    "compliance",
    "gdpr",
    "soc2",
    # Expanded for real-world JDs / résumés (keeps anonymisation + scoring in sync via iter_tech_surface_forms).
    "prisma",
    "websocket",
    "websockets",
    "sqlite",
    "dynamodb",
    "cassandra",
    "couchdb",
    "memcached",
    "influxdb",
    "cockroachdb",
    "protobuf",
    "grpc",
    "webrtc",
    "oauth2",
    "saml",
    "ldap",
    "opentelemetry",
    "prometheus",
    "grafana",
    "datadog",
    "splunk",
    "elk",
    "pulumi",
    "crossplane",
    "istio",
    "linkerd",
    "consul",
    "vault",
    "argo",
    "tekton",
    "circleci",
    "bitbucket",
    "nix",
    "bazel",
    "maven",
    "gradle",
    "nixos",
    "nixpacks",
    "redux",
    "mobx",
    "zustand",
    "nuxt",
    "nuxtjs",
    "remix",
    "sveltekit",
    "astro",
    "solidjs",
    "electron",
    "tauri",
    "capacitor",
    "ionic",
    "android",
    "ios",
    "swiftui",
    "jetpack",
    "xamarin",
    "flutter",
    "dartlang",
    "cuda",
    "opencv",
    "selenium",
    "cypress",
    "playwright",
    "jest",
    "mocha",
    "vitest",
    "pytest",
    "rspec",
    "liquibase",
    "flyway",
    "camel",
    "mulesoft",
    "salesforce",
    "sap",
    "servicenow",
    "dotnet",
    "blazor",
    "wcf",
    "wpf",
    "verilog",
    "vhdl",
    "fpga",
    "arduino",
    "raspberry",
    "mqtt",
    "coap",
    "ffmpeg",
    "gstreamer",
    "opencv",
    "hadoop",
    "hive",
    "presto",
    "trino",
    "clickhouse",
    "duckdb",
    "bigquery",
    "redshift",
    "bigtable",
    "cosmosdb",
    "firebase",
    "supabase",
    "appwrite",
    "strapi",
    "drupal",
    "wordpress",
    "magento",
    "shopify",
    "stripe",
    "paypal",
    "braintree",
    "ethereum",
    "solidity",
    "hardhat",
    "truffle",
    "web3",
    "rustlang",
}

KNOWN_TECH_ACRONYMS_RAW: frozenset[str] = frozenset(
    {
        "AWS",
        "GCP",
        "API",
        "SQL",
        "HTTP",
        "HTTPS",
        "TCP",
        "UDP",
        "TLS",
        "SSH",
        "SSL",
        "DNS",
        "CDN",
        "VPC",
        "IAM",
        "RDS",
        "S3",
        "EC2",
        "EKS",
        "GKE",
        "AKS",
        "K8S",
        "REST",
        "SOAP",
        "GRPC",
        "RPC",
        "JWT",
        "JWE",
        "JWS",
        "ORM",
        "CRUD",
        "CLI",
        "GUI",
        "SDK",
        "IDE",
        "CI",
        "CD",
        "ETL",
        "ELT",
        "NLP",
        "LLM",
        "ML",
        "AI",
        "BI",
        "GPU",
        "CPU",
        "FPGA",
        "UML",
        "JSON",
        "YAML",
        "XML",
        "HTML",
        "CSS",
        "DOM",
        "XHR",
        "CSRF",
        "XSS",
        "SSO",
        "OIDC",
        "SAML",
        "LDAP",
        "MTLS",
        "RBAC",
        "ABAC",
        "PCI",
        "HIPAA",
        "SLA",
        "SLO",
        "SLI",
        "APM",
        "SEO",
    }
)

# Uppercase tokens in prose that are almost never technologies (avoid false units).
_ACRONYM_DENYLIST: frozenset[str] = frozenset(
    {
        "THE",
        "AND",
        "FOR",
        "ARE",
        "BUT",
        "NOT",
        "ALL",
        "CAN",
        "HER",
        "WAS",
        "ONE",
        "OUR",
        "YOU",
        "HAD",
        "HAS",
        "HIM",
        "HIS",
        "HOW",
        "ITS",
        "MAY",
        "NEW",
        "NOW",
        "OLD",
        "WAY",
        "WHO",
        "BOY",
        "DID",
        "GET",
        "HAS",
        "LET",
        "PUT",
        "SAY",
        "SHE",
        "TOO",
        "USE",
        "USA",
        "UK",
        "EU",
        "UN",
        "GMT",
        "UTC",
        "EST",
        "PST",
        "CST",
        "EDT",
        "CEO",
        "CFO",
        "CTO",
        "VP",
        "SVP",
        "EVP",
        "PM",
        "BA",
        "QA",
        "HR",
        "IT",
        "HRIS",
        "EOE",
        "DOE",
    }
)

# Lowercase unit -> extra literal forms to find in resume (already lowercased).
# Matching is always case-insensitive; this improves recall (e.g. JAVA, JVM, Jakarta).
_UNIT_MATCH_ALIASES: dict[str, tuple[str, ...]] = {
    "java": (
        "java",
        "jvm",
        "j2ee",
        "jdbc",
        "jdk",
        "jdk8",
        "jdk11",
        "jdk17",
        "jdk21",
        "jdk 8",
        "jdk 11",
        "jdk 17",
        "jakarta ee",
        "jakarta",
    ),
    "javascript": ("javascript", "node.js", "nodejs"),
    "typescript": ("typescript", "ts",),
    "python": ("python", "python3", "py3"),
    "react": ("react", "react.js", "reactjs"),
    "kubernetes": ("kubernetes", "k8s"),
    "postgres": ("postgres", "postgresql"),
    "postgresql": ("postgresql", "postgres"),
    "c#": ("c#", "c sharp", "csharp"),
    "c++": ("c++", "cpp"),
    "go": ("golang", "go"),
    "node": ("node.js", "node", "nodejs"),
    "nextjs": ("nextjs", "next.js"),
    "vue": ("vue", "vue.js", "vuejs"),
    "angular": ("angular", "angularjs"),
}


def iter_tech_surface_forms() -> tuple[str, ...]:
    """Technology strings used for scoring — same set drives anonymisation protection so stacks are not stripped."""
    seen: set[str] = set()
    out: list[str] = []

    def add(raw: str) -> None:
        s = (raw or "").strip()
        if not s:
            return
        k = s.lower()
        if k in seen:
            return
        seen.add(k)
        out.append(s)

    for kw in TECH_KEYWORDS:
        add(kw)
    for phrase in KEYWORD_PHRASES:
        add(phrase)
    for unit, aliases in _UNIT_MATCH_ALIASES.items():
        add(unit)
        for a in aliases:
            add(a)
    return tuple(out)


def _unit_alias_literals(unit_lower: str) -> tuple[str, ...]:
    """Distinct lowercase literals / phrases used to find this unit in resume text."""
    u = (unit_lower or "").strip().lower()
    if not u:
        return ()
    extras = _UNIT_MATCH_ALIASES.get(u, ())
    out: list[str] = []
    for x in (u,) + extras:
        s = (x or "").strip().lower()
        if s and s not in out:
            out.append(s)
    return tuple(out)


def _alias_matches_resume(resume_lower: str, alias_lower: str) -> bool:
    """True if alias_lower occurs in resume_lower with appropriate boundaries (case-insensitive)."""
    a = alias_lower.strip()
    if not a:
        return False
    if " " in a:
        return a in resume_lower
    if "/" in a:
        return a in resume_lower
    if "." in a or re.search(r"[+\#]", a):
        return a in resume_lower
    if a in ("js", "ts"):
        return re.search(rf"(?<![a-z0-9]){re.escape(a)}(?![a-z0-9])", resume_lower) is not None
    if a == "go":
        return bool(
            re.search(r"(?<![a-z0-9])golang(?![a-z0-9])", resume_lower)
            or re.search(r"(?<![a-z0-9])go(?![a-z0-9])", resume_lower)
        )
    if re.match(r"^[a-z0-9]+$", a):
        return re.search(rf"(?<![a-z0-9]){re.escape(a)}(?![a-z0-9])", resume_lower) is not None
    return a in resume_lower


SECTION_HEADINGS_RE = re.compile(
    r"(?i)^\s*(required|preferred|technologies|technology|tech\s*stack|skills|skill|must have|nice to have)\s*[:\-]?",
    flags=re.IGNORECASE,
)


def _extract_scoring_text(job_description: str) -> str:
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
        if (ln.startswith("-") or ln.startswith("*") or ln.startswith("•")) and len(ln) <= 200:
            selected.append(ln)
            continue
        if re.search(r"(?i)\b(tech|stack|skills|technologies|required|preferred)\b", ln):
            selected.append(ln)

    scoring_text = "\n".join(selected).strip()
    return scoring_text if scoring_text else (job_description or "")


def _is_tech_token(tok_original: str, tok_lower: str) -> bool:
    if tok_lower in STOPWORDS:
        return False
    if tok_lower in TECH_KEYWORDS:
        return True
    if re.search(r"[+\#\.]", tok_original):
        return True
    return False


def _extract_phrases_in_text(scoring_text_lower: str) -> List[str]:
    found: list[str] = []
    for phrase in sorted(KEYWORD_PHRASES, key=len, reverse=True):
        if phrase in scoring_text_lower:
            found.append(phrase)
    return found


def _scan_full_job_for_tech(job_lower: str, seen: set[str], max_units: int, units: list[str]) -> None:
    """If structured extraction is empty, pull only known tech terms from the full job text."""
    for phrase in sorted(KEYWORD_PHRASES, key=len, reverse=True):
        if len(units) >= max_units:
            return
        if phrase in job_lower and phrase not in seen:
            seen.add(phrase)
            units.append(phrase)
    for kw in sorted(TECH_KEYWORDS, key=len, reverse=True):
        if len(units) >= max_units:
            return
        if kw in seen:
            continue
        if re.search(rf"(?<![a-z0-9]){re.escape(kw)}(?![a-z0-9])", job_lower):
            seen.add(kw)
            units.append(kw)


def _inject_job_acronyms(job_raw: str, seen: set[str], units: list[str], max_add: int = 16) -> None:
    """Pick up ALL-CAPS tech in real JDs (AWS, K8S, GRPC) that token rules might miss."""
    added = 0
    for m in re.finditer(r"\b[A-Z][A-Z0-9]{1,5}\b", job_raw):
        raw = m.group(0)
        if raw in _ACRONYM_DENYLIST:
            continue
        low = raw.lower()
        if low in seen:
            continue
        if low in TECH_KEYWORDS or raw in KNOWN_TECH_ACRONYMS_RAW:
            seen.add(low)
            units.append(raw)
            added += 1
            if added >= max_add:
                return


def _units_from_resume_skill_lines(resume_text: str, seen: set[str], units: list[str], max_add: int = 18) -> int:
    """Bullet / skills lines on résumés often list stack explicitly — add known tech units for matching."""
    added = 0
    for ln in (resume_text or "").splitlines():
        st = ln.strip()
        if not st or len(st) > 280:
            continue
        is_bullet = st[0] in "-*•" or bool(re.match(r"^\d+[\.\)]\s+", st))
        is_heading = bool(re.match(r"(?i)^(skills|technologies|tech stack|tools|core competencies)\s*:\s*", st))
        if not (is_bullet or is_heading):
            continue
        for raw in TOKEN_RE.findall(st):
            raw = raw.rstrip(".,;:")
            if len(raw) < 2:
                continue
            low = raw.lower()
            if low not in TECH_KEYWORDS:
                continue
            if low in seen:
                continue
            seen.add(low)
            units.append(raw)
            added += 1
            if added >= max_add:
                return added
    return added


def _extract_keywords(job_description: str, max_units: int = 40) -> tuple[list[str], str]:
    """
    Return (units, source_note). Units are technologies / concrete skills only — no random English words.
    """
    job_raw = job_description or ""
    job_lower = job_raw.lower()
    scoring_text = _extract_scoring_text(job_raw)
    scoring_lower = (scoring_text or "").lower()

    units: list[str] = []
    seen: set[str] = set()

    for phrase in _extract_phrases_in_text(scoring_lower):
        if phrase in seen:
            continue
        seen.add(phrase)
        units.append(phrase)

    tokens = TOKEN_RE.findall(scoring_text or "")
    representative: dict[str, str] = {}
    counts: Counter[str] = Counter()

    for tok in tokens:
        tok = tok.rstrip(".,;:")
        if len(tok) < 2:
            continue
        low = tok.lower()
        if not _is_tech_token(tok, low):
            continue
        counts[low] += 1
        representative.setdefault(low, tok)

    for low, _ in counts.most_common(max_units):
        if low in seen:
            continue
        seen.add(low)
        units.append(representative[low])

    source_note = "requirements_sections"
    if not units:
        _scan_full_job_for_tech(job_lower, seen, max_units, units)
        source_note = "full_job_tech_scan"

    if not units:
        source_note = "no_tech_keywords_found"

    _inject_job_acronyms(job_raw, seen, units)
    return units[:max_units], source_note


def _extract_required_years(job_description: str) -> int | None:
    years = [int(m.group(1)) for m in YEARS_RE.finditer(job_description or "")]
    return max(years) if years else None


def _extract_resume_years(resume_text: str) -> int | None:
    years = [int(m.group(1)) for m in YEARS_RE.finditer(resume_text or "")]
    return max(years) if years else None


def _unit_matches_resume(resume_text: str, unit: str) -> bool:
    """Case-insensitive match: unit + known aliases (e.g. Java ↔ JVM/JDK/Jakarta; avoids java ⊂ javascript)."""
    resume_lower = (resume_text or "").lower()
    ul = (unit or "").strip().lower()
    if not ul:
        return False
    for alias in _unit_alias_literals(ul):
        if _alias_matches_resume(resume_lower, alias):
            return True
    return False


def score_resume(job_description: str, anonymised_resume_text: str) -> Tuple[int, Dict[str, Any]]:
    units, job_source = _extract_keywords(job_description)
    resume_text = anonymised_resume_text or ""
    seen_units = {u.strip().lower() for u in units}
    n_resume_skills = _units_from_resume_skill_lines(resume_text, seen_units, units, max_add=22)
    units = units[:56]
    source_note = job_source if not n_resume_skills else f"{job_source}+resume_skills({n_resume_skills})"

    matched: list[str] = []
    missing: list[str] = []
    for u in units:
        if _unit_matches_resume(resume_text, u):
            matched.append(u)
        else:
            missing.append(u)

    n = len(units)
    m = len(matched)
    keyword_score = int(round((m / n) * 100)) if n else 0

    required_years = _extract_required_years(job_description)
    resume_years = _extract_resume_years(resume_text)
    years_met: bool | None = None
    if required_years is not None and resume_years is not None:
        years_met = resume_years >= required_years

    summary_tags: list[str] = [f"{kw} ✓" for kw in matched[:8]]
    if required_years is not None:
        if years_met is True:
            summary_tags.append(f"Meets {required_years}+ years requirement ✓")
        elif years_met is False:
            summary_tags.append(f"Years requirement: needs {required_years}+ (resume states up to {resume_years})")

    breakdown: Dict[str, Any] = {
        "method": "technology_keyword_alignment",
        "formula": "Score = round((matched_technology_units ÷ units_from_job) × 100). Matching is case-insensitive; related forms count (e.g. Java ↔ JVM/JDK/Jakarta).",
        "units_extracted_from_job": n,
        "units_matched_in_resume": m,
        "matched_keywords": matched,
        "missing_keywords": missing[:15],
        "extraction_source": source_note,
        "resume_skill_lines_merged": n_resume_skills,
        "years_requirement": None
        if required_years is None
        else {
            "required_min_years": required_years,
            "max_years_mentioned_in_resume": resume_years,
            "requirement_met": years_met,
            "note": "Years are informational; the numeric score is from technology alignment only.",
        },
    }

    explanation: Dict[str, Any] = {
        "summary_tags": summary_tags,
        "breakdown": breakdown,
    }

    confidence = max(0, min(100, keyword_score))
    return confidence, explanation


def _normalize_breakdown(bd: dict[str, Any]) -> dict[str, Any]:
    """Ensure list fields are JSON-serializable lists (avoid clients calling .join on wrong types)."""
    out = dict(bd)
    for key in ("matched_keywords", "missing_keywords"):
        v = out.get(key)
        if isinstance(v, list):
            out[key] = [str(x) for x in v]
        elif isinstance(v, str) and v.strip():
            out[key] = [v.strip()]
        else:
            out[key] = []
    yr = out.get("years_requirement")
    if yr is not None and not isinstance(yr, dict):
        out["years_requirement"] = None
    return out


def parse_explanation_json(raw: str | None) -> tuple[list[str], dict[str, Any] | None]:
    """Support legacy list-only JSON and new object shape."""
    if not raw:
        return [], None
    try:
        data = json.loads(raw)
    except Exception:
        return [], None
    if isinstance(data, list):
        return [str(x) for x in data], None
    if isinstance(data, dict):
        tags = data.get("summary_tags") or data.get("tags") or []
        if not isinstance(tags, list):
            tags = []
        bd = data.get("breakdown")
        breakdown = _normalize_breakdown(bd) if isinstance(bd, dict) else None
        return [str(t) for t in tags], breakdown
    return [], None
