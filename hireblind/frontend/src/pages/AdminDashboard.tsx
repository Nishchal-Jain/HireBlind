import React, { useState } from "react";
import { processResumes } from "../services/hireblindApi";

const SAMPLE_JOB_DESCRIPTION = `We are looking for a Python/React engineer to build bias-free resume screening tools.
Required: 3+ years experience with Python, SQL, and REST APIs.
Preferred: React, machine learning basics, and data privacy compliance.`;

export default function AdminDashboard() {
  const [jobDescription, setJobDescription] = useState(SAMPLE_JOB_DESCRIPTION);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  async function onProcess() {
    setLoading(true);
    setStatus(null);
    try {
      await processResumes(jobDescription);
      setStatus("Done: candidates scored successfully.");
    } catch (err: any) {
      setStatus(err?.response?.data?.detail ?? err?.message ?? "Failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl p-6">
      <div className="mb-4">
        <div className="text-xl font-semibold text-slate-800">Admin Dashboard</div>
        <div className="text-sm text-slate-600">Set the job description and score candidates.</div>
      </div>

      <div className="rounded-lg bg-white border border-slate-200 p-5 shadow-sm">
        <label className="block text-sm font-medium text-slate-800 mb-2">Job Description</label>
        <textarea
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          rows={10}
          className="w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-sm"
        />

        <div className="mt-4 flex items-center gap-3">
          <button
            onClick={onProcess}
            disabled={loading}
            className="rounded-md bg-slate-800 px-4 py-2 text-white font-medium hover:bg-slate-700 disabled:opacity-60"
          >
            {loading ? "Processing..." : "Process Resumes"}
          </button>
          <div className="text-sm text-slate-600">{status ? status : " "}</div>
        </div>
      </div>
    </div>
  );
}

