import React from "react";
import type { CandidateRow } from "../services/hireblindApi";

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
        <div className="text-sm text-slate-600">Sorted by score descending</div>
      </div>
      <div className="overflow-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-slate-700">
            <tr>
              <th className="text-left px-4 py-2">Candidate</th>
              <th className="text-left px-4 py-2">Score</th>
              <th className="text-left px-4 py-2">Explanation</th>
            </tr>
          </thead>
          <tbody>
            {candidates.map((c, idx) => {
              const label = LETTERS[idx % LETTERS.length];
              const score = c.final_score ?? c.score;
              return (
                <tr
                  key={c.candidate_id}
                  className={`border-t ${selectedId === c.candidate_id ? "bg-slate-100" : "bg-white"} hover:bg-slate-50`}
                >
                  <td className="px-4 py-3 whitespace-nowrap">
                    <button
                      className="text-slate-900 font-medium hover:underline"
                      type="button"
                      onClick={() => onSelect(c)}
                    >
                      Candidate {label}
                    </button>
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap font-semibold">
                    {score ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-slate-700">
                      {c.explanation?.length ? (
                        <span>{c.explanation.slice(0, 3).join(", ")}</span>
                      ) : (
                        <span className="text-slate-500">No tags</span>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
            {candidates.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-4 py-6 text-slate-600">
                  No candidates yet. Ask admin to process resumes (seed demo users can log in immediately).
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}

