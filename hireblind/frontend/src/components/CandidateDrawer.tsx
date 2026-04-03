import React, { useEffect, useMemo, useState } from "react";
import { updateRanking } from "../services/hireblindApi";
import type { CandidateRow } from "../services/hireblindApi";

export default function CandidateDrawer({
  candidate,
  labelLetter,
  onUpdated,
}: {
  candidate: CandidateRow | null;
  labelLetter: string;
  onUpdated: () => Promise<void>;
}) {
  const [revealState, setRevealState] = useState<"hidden" | "revealed">("hidden");
  const [overrideScore, setOverrideScore] = useState<number>(candidate?.final_score ?? candidate?.score ?? 0);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  const effectiveScore = useMemo(() => candidate?.final_score ?? candidate?.score ?? null, [candidate]);

  useEffect(() => {
    setRevealState("hidden");
    setStatus(null);
    setReason("");
    setOverrideScore(candidate?.final_score ?? candidate?.score ?? 0);
  }, [candidate?.candidate_id]);

  if (!candidate) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-600">
        Select a candidate to view details.
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
        reason: `Blind reveal simulation for Candidate ${labelLetter}`,
      });
      setRevealState("revealed");
      await onUpdated();
      setStatus("Reveal logged (simulated).");
    } catch (err: any) {
      setStatus(err?.response?.data?.detail ?? err?.message ?? "Failed");
    } finally {
      setBusy(false);
    }
  }

  async function onApplyOverride() {
    if (busy) return;
    setBusy(true);
    setStatus(null);
    try {
      await updateRanking({
        candidate_id: candidate.candidate_id,
        override_score: overrideScore,
        reason,
      });
      await onUpdated();
      setReason("");
      setStatus("Override applied.");
    } catch (err: any) {
      setStatus(err?.response?.data?.detail ?? err?.message ?? "Failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-lg font-semibold text-slate-900">Candidate {labelLetter}</div>
          <div className="text-sm text-slate-600">Candidate ID: {candidate.candidate_id}</div>
          <div className="mt-2 text-sm">
            <span className="font-medium">Confidence:</span>{" "}
            <span className="font-semibold text-slate-900">{effectiveScore ?? "—"}</span>
          </div>
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
        </div>
      </div>

      <div className="mt-4">
        <div className="text-sm font-semibold text-slate-800 mb-1">Why ranked (explanations)</div>
        {candidate.explanation?.length ? (
          <div className="flex flex-wrap gap-2">
            {candidate.explanation.map((t) => (
              <span key={t} className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
                {t}
              </span>
            ))}
          </div>
        ) : (
          <div className="text-sm text-slate-600">No explanations yet. Ask admin to process resumes.</div>
        )}
      </div>

      <div className="mt-4">
        <div className="text-sm font-semibold text-slate-800 mb-1">Anonymised resume</div>
        <pre className="max-h-56 overflow-auto rounded-md bg-slate-50 border border-slate-200 p-3 text-xs leading-relaxed whitespace-pre-wrap font-mono">
          {candidate.anonymised_resume_text}
        </pre>
      </div>

      <div className="mt-5 border-t border-slate-200 pt-4">
        <div className="text-sm font-semibold text-slate-800 mb-2">Bias Override (manual ranking)</div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">Override score (0-100)</label>
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
            <label className="block text-xs font-medium text-slate-700 mb-1">Reason (required)</label>
            <input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              placeholder="Explain why you changed the ranking..."
            />
          </div>
        </div>

        <div className="mt-3 flex items-center gap-3">
          <button
            type="button"
            disabled={busy || !reason.trim()}
            onClick={() => void onApplyOverride()}
            className="rounded-md bg-slate-800 px-4 py-2 text-white text-sm hover:bg-slate-700 disabled:opacity-60"
          >
            Apply Override
          </button>
          {status ? <div className="text-sm text-slate-700">{status}</div> : null}
        </div>
      </div>
    </div>
  );
}

