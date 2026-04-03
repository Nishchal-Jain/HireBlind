import React from "react";
import type { CandidateRow } from "../services/hireblindApi";
import { coerceStringArray, formatCandidateTitle } from "../services/hireblindApi";

const LETTERS = ["A", "B", "C"] as const;

export default function CandidatesTable({
  candidates,
  selectedId,
  onSelect,
}: {
  candidates: CandidateRow[];
  selectedId: number | null;
  onSelect: (candidate: CandidateRow) => void;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-200">
        <div className="font-semibold text-slate-800">Ranking</div>
        <div className="text-sm text-slate-600">Sorted by score (highest first). Names come from uploaded filenames.</div>
      </div>
      <div className="overflow-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-700">
            <tr>
              <th className="text-left px-4 py-2">Resume</th>
              <th className="text-left px-4 py-2">Score</th>
              <th className="text-left px-4 py-2">Match summary</th>
            </tr>
          </thead>
          <tbody>
            {candidates.map((c, idx) => {
              const label = LETTERS[idx % LETTERS.length];
              const score = c.final_score ?? c.score;
              const title = formatCandidateTitle(c, label);
              const tags = coerceStringArray(c.explanation);
              return (
                <tr
                  key={c.candidate_id}
                  className={`border-t ${selectedId === c.candidate_id ? "bg-slate-100" : "bg-white"} hover:bg-slate-50`}
                >
                  <td className="px-4 py-3">
                    <button
                      className="text-left text-slate-900 font-medium hover:underline"
                      type="button"
                      onClick={() => onSelect(c)}
                    >
                      <div>{title}</div>
                      <div className="text-xs font-normal text-slate-500">ID #{c.candidate_id}</div>
                    </button>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap font-semibold">
                    {score ?? "—"}
                    {c.is_override ? (
                      <span className="ml-2 rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-900">
                        override
                      </span>
                    ) : null}
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-slate-700">
                      {tags.length ? (
                        <span>{tags.slice(0, 3).join(", ")}</span>
                      ) : (
                        <span className="text-slate-500">No score yet — ask admin to process resumes</span>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
            {candidates.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-4 py-6 text-slate-600">
                  No candidates yet. Upload resumes here, then ask an admin to run Process Resumes.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
