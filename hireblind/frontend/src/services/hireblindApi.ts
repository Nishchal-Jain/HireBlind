import { api } from "./api";

export type ScoringBreakdown = {
  method?: string;
  formula?: string;
  units_extracted_from_job?: number;
  units_matched_in_resume?: number;
  matched_keywords?: string[];
  missing_keywords?: string[];
  extraction_source?: string;
  resume_skill_lines_merged?: number;
  years_requirement?: {
    required_min_years?: number;
    max_years_mentioned_in_resume?: number | null;
    requirement_met?: boolean | null;
    note?: string;
  } | null;
};

export type CandidateRow = {
  candidate_id: number;
  upload_label: string | null;
  anonymised_resume_text: string;
  score: number | null;
  final_score: number | null;
  explanation: string[];
  scoring_breakdown?: ScoringBreakdown | null;
  is_override: boolean;
  override_score: number | null;
  override_reason: string | null;
  override_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AuditLogRow = {
  id: number;
  candidate_id: number;
  removed_field: string;
  timestamp: string;
  details: string | null;
};

export async function processResumes(job_description: string): Promise<void> {
  await api.post("/process-resumes", { job_description });
}

export async function uploadResumes(
  files: File[],
  onProgress?: (progressPct: number) => void,
): Promise<number[]> {
  const formData = new FormData();
  for (const f of files) formData.append("files", f);

  const res = await api.post<{ candidate_ids: number[] }>("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (evt) => {
      if (!evt.total) return;
      const pct = Math.round((evt.loaded / evt.total) * 100);
      onProgress?.(pct);
    },
  });

  return res.data.candidate_ids;
}

export async function getCandidates(): Promise<CandidateRow[]> {
  const res = await api.get<CandidateRow[]>("/get-candidates");
  return res.data;
}

export async function getAuditLogs(candidateId?: number): Promise<AuditLogRow[]> {
  const res = await api.get<AuditLogRow[]>("/get-audit-logs", {
    params: candidateId ? { candidate_id: candidateId } : {},
  });
  return res.data;
}

export async function updateRanking(params: {
  candidate_id: number;
  reason: string;
  override_score?: number;
}): Promise<{ ok: boolean; override_at: string | null; override_score: number | null; final_score: number | null }> {
  const res = await api.post("/update-ranking", params);
  return res.data;
}

export async function deleteCandidate(candidateId: number): Promise<void> {
  await api.delete(`/candidates/${candidateId}`);
}

export function formatCandidateTitle(candidate: CandidateRow, labelLetter: string): string {
  const name = candidate.upload_label?.trim();
  return name ? name : `Candidate ${labelLetter}`;
}

/** Coerce API/legacy values to string[] so .map / .join never throw. */
export function coerceStringArray(value: unknown): string[] {
  if (Array.isArray(value)) return value.map((x) => String(x));
  if (value === null || value === undefined) return [];
  if (typeof value === "string") return value.trim() ? [value] : [];
  return [];
}

/** API sends UTC ISO strings; display in the user's locale with offset (not ambiguous). */
export function formatLocalDateTime(iso: string | null | undefined): string {
  if (iso == null || iso === "") return "—";
  if (typeof iso !== "string") return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  try {
    return d.toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "medium",
      timeZoneName: "short",
    });
  } catch {
    return d.toISOString();
  }
}

/** Full local date + time with seconds (e.g. manual override timestamps). */
export function formatDetailedLocalDateTime(iso: string | null | undefined): string {
  if (iso == null || iso === "") return "—";
  if (typeof iso !== "string") return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  try {
    return d.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      timeZoneName: "short",
    });
  } catch {
    return d.toISOString();
  }
}
