import React, { useEffect } from "react";

export type PreviewTarget =
  | { kind: "pdf"; url: string; name: string }
  | { kind: "docx"; name: string }
  | { kind: "text"; title: string; body: string };

export default function ResumePreviewModal({
  target,
  onClose,
}: {
  target: PreviewTarget | null;
  onClose: () => void;
}) {
  useEffect(() => {
    if (!target || target.kind !== "pdf") return;
    const url = target.url;
    return () => {
      URL.revokeObjectURL(url);
    };
  }, [target]);

  if (!target) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Resume preview"
    >
      <div className="relative flex max-h-[90vh] w-full max-w-4xl flex-col rounded-lg bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
          <div className="min-w-0">
            <div className="font-semibold text-slate-900 truncate">
              {target.kind === "text" ? target.title : target.name}
            </div>
            <div className="text-xs text-slate-500">
              {target.kind === "pdf"
                ? "PDF preview (local file — not uploaded to server until you confirm upload)."
                : target.kind === "docx"
                  ? "Word files preview as text only after upload (anonymised copy in candidate details)."
                  : "Anonymised text stored for this candidate."}
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Close
          </button>
        </div>
        <div className="min-h-[50vh] flex-1 overflow-hidden">
          {target.kind === "pdf" ? (
            <iframe title={target.name} src={target.url} className="h-[70vh] w-full border-0 bg-slate-100" />
          ) : target.kind === "docx" ? (
            <div className="p-6 text-sm text-slate-600">
              <p className="mb-3">
                Browsers cannot render <strong>.docx</strong> inline. After upload, open the candidate row and
                use <strong>View full anonymised resume</strong> to read the redacted text used for scoring.
              </p>
              <p className="text-xs text-slate-500">File: {target.name}</p>
            </div>
          ) : (
            <pre className="h-[70vh] overflow-auto p-4 text-xs leading-relaxed whitespace-pre-wrap font-mono text-slate-800">
              {target.body}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
