import React, { useEffect, useMemo, useState } from "react";
import ResumePreviewModal, { type PreviewTarget } from "./ResumePreviewModal";
import {
  coerceStringArray,
  deleteCandidate,
  formatCandidateTitle,
  formatDetailedLocalDateTime,
  formatLocalDateTime,
  updateRanking,
} from "../services/hireblindApi";
import type { CandidateRow } from "../services/hireblindApi";

export default function CandidateDrawer({
  candidate,
  labelLetter,
  onUpdated,
  onDeleted,
}: {
  candidate: CandidateRow | null;
  labelLetter: string;
  onUpdated: () => Promise<void>;
  onDeleted?: () => Promise<void>;
}) {
  const [revealState, setRevealState] = useState<"hidden" | "revealed">("hidden");
  const [overrideScore, setOverrideScore] = useState<number>(candidate?.final_score ?? candidate?.score ?? 0);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [resumeModal, setResumeModal] = useState<PreviewTarget | null>(null);

  const effectiveScore = useMemo(() => candidate?.final_score ?? candidate?.score ?? null, [candidate]);
  const title = useMemo(
    () => (candidate ? formatCandidateTitle(candidate, labelLetter) : ""),
    [candidate, labelLetter],
  );

  const bd = candidate?.scoring_breakdown;
  const explanationTags = useMemo(() => coerceStringArray(candidate?.explanation), [candidate]);
  const matchedKeywords = useMemo(() => coerceStringArray(bd?.matched_keywords), [bd]);
  const missingKeywords = useMemo(() => coerceStringArray(bd?.missing_keywords), [bd]);

  useEffect(() => {
    setRevealState("hidden");
    setStatus(null);
    setReason("");
    setOverrideScore(candidate?.final_score ?? candidate?.score ?? 0);
  }, [candidate?.candidate_id]);

  useEffect(() => {
    if (!candidate) setResumeModal(null);
  }, [candidate]);

  if (!candidate) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-600">
        Select a resume row to view anonymised text, scoring rationale, and actions.
      </div>
    );
  }

  async function onRevealIdentity() {
    if (busy) return;
    setBusy(true);
    setStatus(null);
    try {
      await updateRanking({
        candidate_id: candidate.candidate_id,
        reason: `Blind reveal simulation for ${title}`,
      });
      setRevealState("revealed");
      await onUpdated();
      setStatus("Reveal logged (simulated).");
    } catch (err: unknown) {
      const e = err as { message?: string };
      setStatus(e?.message ?? "Failed");
    } finally {
      setBusy(false);
    }
  }

  async function onApplyOverride() {
    if (busy) return;
    setBusy(true);
    setStatus(null);
    try {
      const res = await updateRanking({
        candidate_id: candidate.candidate_id,
        override_score: overrideScore,
        reason: reason.trim(),
      });
      await onUpdated();
      setReason("");
      setStatus(
        res.override_at
          ? `Override saved · ${formatDetailedLocalDateTime(res.override_at)}`
          : "Override saved.",
      );
    } catch (err: unknown) {
      const e = err as { message?: string };
      setStatus(e?.message ?? "Failed");
    } finally {
      setBusy(false);
    }
  }

  async function onDelete() {
    if (busy) return;
    const ok = window.confirm(
      `Delete this scored candidate and all audit rows for ID #${candidate.candidate_id}? This cannot be undone.`,
    );
    if (!ok) return;
    setBusy(true);
    setStatus(null);
    try {
      await deleteCandidate(candidate.candidate_id);
      await onDeleted?.();
      await onUpdated();
      setStatus("Candidate removed.");
    } catch (err: unknown) {
      const e = err as { message?: string };
      setStatus(e?.message ?? "Delete failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <ResumePreviewModal
        target={resumeModal}
        onClose={() => setResumeModal(null)}
      />
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-lg font-semibold text-slate-900">{title}</div>
          <div className="text-sm text-slate-600">Blind label: Candidate {labelLetter} · Database ID #{candidate.candidate_id}</div>
          <div className="text-xs text-slate-500 mt-1">Last updated: {formatLocalDateTime(candidate.updated_at)}</div>
          <div className="mt-2 text-sm">
            <span className="font-medium">Score used for ranking:</span>{" "}
            <span className="font-semibold text-slate-900">{effectiveScore ?? "—"}</span>
            {candidate.is_override ? (
              <span className="ml-2 text-xs font-medium text-amber-800">(manual override)</span>
            ) : null}
          </div>
          {candidate.is_override ? (
            <div className="mt-2 rounded-md bg-amber-50 border border-amber-200 px-3 py-2 text-sm text-amber-950">
              <div>
                <span className="font-medium">Override applied:</span>{" "}
                {formatDetailedLocalDateTime(candidate.override_at)}
              </div>
              {candidate.override_reason ? (
                <div className="mt-1">
                  <span className="font-medium">Reason on file:</span> {candidate.override_reason}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
        <div className="flex flex-col gap-2 items-end">
          <button
            type="button"
            disabled={busy || revealState === "revealed"}
            onClick={() => void onRevealIdentity()}
            className="rounded-md bg-amber-600 px-3 py-2 text-white text-sm hover:bg-amber-500 disabled:opacity-60"
          >
            {revealState === "revealed" ? "Identity Revealed" : "Reveal Identity"}
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => void onDelete()}
            className="rounded-md border border-red-300 bg-white px-3 py-2 text-sm text-red-800 hover:bg-red-50 disabled:opacity-60"
          >
            Delete candidate
          </button>
        </div>
      </div>

      <div className="mt-4 rounded-md bg-slate-50 border border-slate-200 p-3">
        <div className="text-sm font-semibold text-slate-800 mb-1">Why this score</div>
        {bd ? (
          <div className="text-sm text-slate-700 space-y-2">
            <div>
              {typeof bd.formula === "string"
                ? bd.formula
                : (bd.formula != null ? String(bd.formula) : null) ??
                  "Keywords from the job description are matched against the anonymised resume text."}
            </div>
            {typeof bd.resume_skill_lines_merged === "number" && bd.resume_skill_lines_merged > 0 ? (
              <div className="text-xs text-slate-600">
                Included {bd.resume_skill_lines_merged} technology term(s) from résumé skills / bullet lines (in addition to the
                job description).
              </div>
            ) : null}
            <div>
              <span className="font-medium">Alignment:</span> {bd.units_matched_in_resume ?? 0} matched out of{" "}
              {bd.units_extracted_from_job ?? 0} requirement units extracted from the job posting
              {typeof bd.units_extracted_from_job === "number" &&
              typeof bd.units_matched_in_resume === "number" &&
              bd.units_extracted_from_job > 0
                ? ` → ${Math.round(((bd.units_matched_in_resume ?? 0) / bd.units_extracted_from_job) * 100)}% raw match (total units may include job + résumé skill lines)`
                : ""}
              .
            </div>
            {matchedKeywords.length ? (
              <div>
                <span className="font-medium">Matched:</span> {matchedKeywords.join(", ")}
              </div>
            ) : null}
            {missingKeywords.length ? (
              <div>
                <span className="font-medium">Not found in resume (from job requirements):</span>{" "}
                {missingKeywords.join(", ")}
              </div>
            ) : null}
            {bd.years_requirement?.required_min_years != null ? (
              <div className="text-xs text-slate-600">
                Years check: job asks for {bd.years_requirement.required_min_years}+ years; resume mentions up to{" "}
                {bd.years_requirement.max_years_mentioned_in_resume ?? "—"}.{" "}
                {bd.years_requirement.note ?? ""}
              </div>
            ) : null}
          </div>
        ) : (
          <div className="text-sm text-slate-600">No scoring breakdown yet. Ask an admin to run Process Resumes.</div>
        )}
      </div>

      <div className="mt-4">
        <div className="text-sm font-semibold text-slate-800 mb-1">Quick signals (tags)</div>
        {explanationTags.length ? (
          <div className="flex flex-wrap gap-2">
            {explanationTags.map((t, i) => (
              <span key={`${i}-${t}`} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
                {t}
              </span>
            ))}
          </div>
        ) : (
          <div className="text-sm text-slate-600">No tags until scoring runs.</div>
        )}
      </div>

      <div className="mt-4">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
          <div className="text-sm font-semibold text-slate-800">Anonymised resume</div>
          <button
            type="button"
            onClick={() =>
              setResumeModal({
                kind: "text",
                title: `${title} — anonymised`,
                body: candidate.anonymised_resume_text || "(empty)",
              })
            }
            className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-800 hover:bg-slate-50"
          >
            View full anonymised resume
          </button>
        </div>
        <pre className="max-h-56 overflow-auto rounded-md bg-slate-50 border border-slate-200 p-3 text-xs leading-relaxed whitespace-pre-wrap font-mono">
          {candidate.anonymised_resume_text}
        </pre>
      </div>

      <div className="mt-5 border-t border-slate-200 pt-4">
        <div className="text-sm font-semibold text-slate-800 mb-2">Bias override (manual ranking)</div>
        <p className="text-xs text-slate-600 mb-3">
          Overrides are stamped with the current time (UTC on the server) and stored with your reason. Re-processing resumes
          keeps an override unless you change it here.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Override score (0–100)</label>
            <input
              type="number"
              value={overrideScore}
              onChange={(e) => setOverrideScore(parseInt(e.target.value || "0", 10))}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              min={0}
              max={100}
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-xs font-medium text-slate-700 mb-1">Reason (required, min 3 characters)</label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              placeholder="Explain why you changed the ranking (stored with date/time)..."
            />
          </div>
        </div>

        <div className="mt-3 flex items-center gap-3 flex-wrap">
          <button
            type="button"
            disabled={busy || reason.trim().length < 3}
            onClick={() => void onApplyOverride()}
            className="rounded-md bg-slate-800 px-4 py-2 text-white text-sm hover:bg-slate-700 disabled:opacity-60"
          >
            Apply override
          </button>
          {status ? <div className="text-sm text-slate-700">{status}</div> : null}
        </div>
      </div>
    </div>
  );
}
