import React, { useEffect, useMemo, useState } from "react";
import { getAuditLogs, getCandidates } from "../services/hireblindApi";
import type { AuditLogRow, CandidateRow } from "../services/hireblindApi";

export default function CompliancePanel() {
  const [candidates, setCandidates] = useState<CandidateRow[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [audit, setAudit] = useState<AuditLogRow[]>([]);
  const [status, setStatus] = useState<string | null>(null);

  async function refreshCandidates() {
    const rows = await getCandidates();
    setCandidates(rows);
    if (rows.length && selectedId == null) setSelectedId(rows[0].candidate_id);
  }

  useEffect(() => {
    void refreshCandidates();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selected = useMemo(
    () => (selectedId == null ? null : candidates.find((c) => c.candidate_id === selectedId) ?? null),
    [candidates, selectedId],
  );

  useEffect(() => {
    if (selectedId == null) return;
    setStatus(null);
    void getAuditLogs(selectedId)
      .then((rows) => setAudit(rows))
      .catch((err: any) => setStatus(err?.response?.data?.detail ?? err?.message ?? "Failed"));
  }, [selectedId]);

  const effectiveScore = selected?.final_score ?? selected?.score ?? null;

  return (
    <div className="mx-auto max-w-6xl p-6">
      <div className="mb-4">
        <div className="text-xl font-semibold text-slate-800">EU AI Act Compliance Panel (Mini)</div>
        <div className="text-sm text-slate-600">Audit evidence for PII removal and the scoring explanations used for ranking.</div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-1 rounded-lg bg-white border border-slate-200 p-4">
          <div className="text-sm font-semibold text-slate-800 mb-2">Select candidate</div>
          <select
            value={selectedId ?? ""}
            onChange={(e) => setSelectedId(e.target.value ? parseInt(e.target.value, 10) : null)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 mb-3"
          >
            {candidates.map((c) => (
              <option key={c.candidate_id} value={c.candidate_id}>
                Candidate ID {c.candidate_id}
              </option>
            ))}
          </select>
          {status ? <div className="text-sm text-red-600">{status}</div> : null}

          <div className="mt-2 text-sm">
            <div className="font-semibold text-slate-800">Confidence (same as score)</div>
            <div className="text-lg font-bold text-slate-900">{effectiveScore ?? "—"}</div>
          </div>

          <div className="mt-4">
            <div className="font-semibold text-slate-800 text-sm mb-2">Why ranked</div>
            {selected?.explanation?.length ? (
              <div className="flex flex-wrap gap-2">
                {selected.explanation.map((t) => (
                  <span key={t} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
                    {t}
                  </span>
                ))}
              </div>
            ) : (
              <div className="text-sm text-slate-600">No explanations stored yet.</div>
            )}
          </div>
        </div>

        <div className="lg:col-span-2 rounded-lg bg-white border border-slate-200 p-4">
          <div className="font-semibold text-slate-800 text-sm mb-2">What PII was removed</div>
          {audit.length ? (
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-slate-700">
                  <tr>
                    <th className="text-left px-3 py-2">Removed field</th>
                    <th className="text-left px-3 py-2">Timestamp</th>
                    <th className="text-left px-3 py-2">Details</th>
                  </tr>
                </thead>
                <tbody>
                  {audit.map((l) => (
                    <tr key={l.id} className="border-t border-slate-200">
                      <td className="px-3 py-2 font-medium text-slate-800">{l.removed_field}</td>
                      <td className="px-3 py-2 text-slate-600">{new Date(l.timestamp).toLocaleString()}</td>
                      <td className="px-3 py-2 text-slate-600">{l.details ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-sm text-slate-600">No audit logs yet.</div>
          )}
          <div className="mt-4 text-xs text-slate-500">
            Note: Original PII is not stored in the database; only anonymised resume text and audit logs are persisted.
          </div>
        </div>
      </div>
    </div>
  );
}

