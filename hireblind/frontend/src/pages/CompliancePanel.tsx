import React, { useEffect, useMemo, useState } from "react";
import {
  formatDetailedLocalDateTime,
  formatLocalDateTime,
  getAuditLogs,
  getCandidates,
} from "../services/hireblindApi";
import type { AuditLogRow, CandidateRow } from "../services/hireblindApi";
import { formatCandidateTitle } from "../services/hireblindApi";

const LETTERS = ["A", "B", "C"] as const;

function formatAuditDetails(raw: string | null): string {
  if (!raw) return "—";
  const t = raw.trim();
  if (t.startsWith("{") && t.endsWith("}")) {
    try {
      const o = JSON.parse(t) as Record<string, unknown>;
      const lines = Object.entries(o).map(([k, v]) => {
        if (k === "recorded_at" && typeof v === "string") {
          return `${k}: ${formatLocalDateTime(v)}`;
        }
        return `${k}: ${typeof v === "object" ? JSON.stringify(v) : String(v)}`;
      });
      return lines.join("\n");
    } catch {
      return raw;
    }
  }
  return raw;
}

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

  const selectedIdx = useMemo(
    () => (selectedId == null ? -1 : candidates.findIndex((c) => c.candidate_id === selectedId)),
    [candidates, selectedId],
  );
  const letter = LETTERS[(selectedIdx >= 0 ? selectedIdx : 0) % LETTERS.length];

  useEffect(() => {
    if (selectedId == null) return;
    setStatus(null);
    void getAuditLogs(selectedId)
      .then((rows) => setAudit(rows))
      .catch((err: unknown) => {
        const e = err as { message?: string };
        setStatus(e?.message ?? "Failed");
      });
  }, [selectedId]);

  const effectiveScore = selected?.final_score ?? selected?.score ?? null;
  const bd = selected?.scoring_breakdown;

  return (
    <div className="mx-auto max-w-6xl p-6">
      <div className="mb-4">
        <div className="text-xl font-semibold text-slate-800">EU AI Act compliance panel (mini)</div>
        <div className="text-sm text-slate-600">
          Audit evidence for PII removal and scoring rationale. Times are stored in UTC on the server and shown in your local
          timezone below.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-1 rounded-lg bg-white border border-slate-200 p-4">
          <div className="text-sm font-semibold text-slate-800 mb-2">Select candidate</div>
          <select
            value={selectedId ?? ""}
            onChange={(e) => setSelectedId(e.target.value ? parseInt(e.target.value, 10) : null)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 mb-3"
          >
            {candidates.map((c, idx) => {
              const lab = LETTERS[idx % LETTERS.length];
              const label = formatCandidateTitle(c, lab);
              return (
                <option key={c.candidate_id} value={c.candidate_id}>
                  {label} (#{c.candidate_id})
                </option>
              );
            })}
          </select>
          {status ? <div className="text-sm text-red-600">{status}</div> : null}

          <div className="mt-2 text-sm space-y-2">
            <div>
              <div className="font-semibold text-slate-800">Last updated</div>
              <div className="text-slate-700">{selected?.updated_at ? formatLocalDateTime(selected.updated_at) : "—"}</div>
              <div className="text-xs text-slate-500">Upload, scoring, or override refreshes this timestamp.</div>
            </div>
            <div>
              <div className="font-semibold text-slate-800">Score used for ranking</div>
              <div className="text-lg font-bold text-slate-900">{effectiveScore ?? "—"}</div>
              {selected?.is_override ? (
                <div className="mt-1 text-xs text-amber-900">
                  Manual override
                  {selected.override_at ? ` · ${formatDetailedLocalDateTime(selected.override_at)}` : ""}
                </div>
              ) : null}
            </div>
          </div>

          <div className="mt-4">
            <div className="font-semibold text-slate-800 text-sm mb-2">Scoring rationale</div>
            {bd ? (
              <div className="text-sm text-slate-700 space-y-2">
                <div>{bd.formula}</div>
                <div>
                  Matched {bd.units_matched_in_resume ?? 0} / {bd.units_extracted_from_job ?? 0} technology units
                  {bd.extraction_source ? ` (${String(bd.extraction_source)})` : ""}.
                </div>
                {bd.missing_keywords?.length ? (
                  <div className="text-xs text-slate-600">Missing vs job: {bd.missing_keywords.join(", ")}</div>
                ) : null}
              </div>
            ) : (
              <div className="text-sm text-slate-600">No breakdown stored yet.</div>
            )}
          </div>

          <div className="mt-4">
            <div className="font-semibold text-slate-800 text-sm mb-2">Tags</div>
            {selected?.explanation?.length ? (
              <div className="flex flex-wrap gap-2">
                {selected.explanation.map((t) => (
                  <span key={t} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
                    {t}
                  </span>
                ))}
              </div>
            ) : (
              <div className="text-sm text-slate-600">No tags yet.</div>
            )}
          </div>
        </div>

        <div className="lg:col-span-2 rounded-lg bg-white border border-slate-200 p-4">
          <div className="font-semibold text-slate-800 text-sm mb-2">
            Audit log{selected ? ` (${formatCandidateTitle(selected, letter)})` : ""}
          </div>
          {!selected ? <div className="text-sm text-slate-600">No candidate selected.</div> : null}
          {audit.length ? (
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-slate-700">
                  <tr>
                    <th className="text-left px-3 py-2">Event</th>
                    <th className="text-left px-3 py-2">Time (your device)</th>
                    <th className="text-left px-3 py-2">Details</th>
                  </tr>
                </thead>
                <tbody>
                  {audit.map((l) => (
                    <tr key={l.id} className="border-t border-slate-200 align-top">
                      <td className="px-3 py-2 font-medium text-slate-800 whitespace-nowrap">{l.removed_field}</td>
                      <td className="px-3 py-2 text-slate-700 whitespace-nowrap">{formatLocalDateTime(l.timestamp)}</td>
                      <td className="px-3 py-2 text-slate-700 whitespace-pre-wrap font-mono text-xs">
                        {formatAuditDetails(l.details)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-sm text-slate-600">{selected ? "No audit logs yet." : null}</div>
          )}
          <div className="mt-4 text-xs text-slate-500">
            Note: Original PII is not stored in the database; only anonymised resume text and audit logs are persisted.
          </div>
        </div>
      </div>
    </div>
  );
}
