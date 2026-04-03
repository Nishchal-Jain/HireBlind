import React, { useEffect, useState } from "react";
import UploadDropzone from "../components/UploadDropzone";
import CandidatesTable from "../components/CandidatesTable";
import CandidateDrawer from "../components/CandidateDrawer";
import { getCandidates, uploadResumes } from "../services/hireblindApi";
import type { CandidateRow } from "../services/hireblindApi";

export default function RecruiterDashboard() {
  const [candidates, setCandidates] = useState<CandidateRow[]>([]);
  const [selected, setSelected] = useState<CandidateRow | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [uploading, setUploading] = useState(false);
  const [uploadFileNames, setUploadFileNames] = useState<string[]>([]);
  const [status, setStatus] = useState<string | null>(null);

  async function refresh() {
    const rows = await getCandidates();
    setCandidates(rows);
    // Keep selection stable when possible.
    setSelected((prev) => (prev ? rows.find((r) => r.candidate_id === prev.candidate_id) ?? prev : null));
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function onFilesPicked(files: File[]) {
    if (!files.length) return;
    setUploading(true);
    setUploadProgress(0);
    setUploadFileNames(files.map((f) => f.name));
    setStatus(null);
    try {
      const ids = await uploadResumes(files, (pct) => setUploadProgress(pct));
      setStatus(`Uploaded ${files.length} file(s). Candidate IDs: ${ids.join(", ")}`);
      await refresh();
    } catch (err: any) {
      setStatus(err?.response?.data?.detail ?? err?.message ?? "Upload failed");
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  }

  const labelLetter = (() => {
    if (!selected) return "A";
    const idx = candidates.findIndex((c) => c.candidate_id === selected.candidate_id);
    const letters = ["A", "B", "C"];
    return letters[(idx >= 0 ? idx : 0) % letters.length];
  })();

  return (
    <div className="mx-auto max-w-6xl p-6">
      <div className="mb-4">
        <div className="text-xl font-semibold text-slate-800">Recruiter Dashboard</div>
        <div className="text-sm text-slate-600">Upload resumes, view ranking, anonymised candidate details, and audit actions.</div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-1">
          <UploadDropzone onFilesPicked={onFilesPicked} disabled={uploading} />
          {uploading ? (
            <div className="mt-3">
              <div className="text-sm font-medium text-slate-700">Upload progress: {uploadProgress}%</div>
              <div className="mt-2 text-xs text-slate-600">
                Uploading:
                <div className="mt-1 flex flex-wrap gap-2">
                  {uploadFileNames.map((n) => (
                    <span key={n} className="rounded bg-slate-100 px-2 py-1 border border-slate-200">
                      {n}
                    </span>
                  ))}
                </div>
              </div>
              <div className="mt-2 h-2 rounded bg-slate-200 overflow-hidden">
                <div className="h-full bg-slate-800" style={{ width: `${uploadProgress}%` }} />
              </div>
            </div>
          ) : null}
          {status ? <div className="mt-3 text-sm text-slate-700">{status}</div> : null}

          <div className="mt-4 rounded-lg bg-white border border-slate-200 p-4">
            <div className="text-sm font-semibold text-slate-800 mb-2">Next step</div>
            <div className="text-sm text-slate-600">
              After upload, new candidates will appear in the ranking list. Admin must run{" "}
              <code className="font-mono">Process Resumes</code> to compute scores.
            </div>
            <button
              className="mt-3 rounded-md bg-slate-800 px-3 py-2 text-white text-sm hover:bg-slate-700"
              type="button"
              onClick={() => void refresh()}
            >
              Refresh ranking
            </button>
          </div>
        </div>

        <div className="lg:col-span-2 flex flex-col gap-4">
          <CandidatesTable candidates={candidates} selectedId={selected?.candidate_id ?? null} onSelect={setSelected} />
          <CandidateDrawer
            candidate={selected}
            labelLetter={labelLetter}
            onUpdated={async () => {
              await refresh();
            }}
          />
        </div>
      </div>
    </div>
  );
}

