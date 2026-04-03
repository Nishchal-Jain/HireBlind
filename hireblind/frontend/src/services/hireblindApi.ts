import { api } from "./api";

export type CandidateRow = {
  candidate_id: number;
  anonymised_resume_text: string;
  score: number | null;
  final_score: number | null;
  explanation: string[];
  created_at: string;
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
}): Promise<void> {
  await api.post("/update-ranking", params);
}

