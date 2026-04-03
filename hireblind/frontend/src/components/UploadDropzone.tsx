import React, { useCallback, useRef } from "react";

type Props = {
  onFilesPicked: (files: File[]) => Promise<void>;
  /** Called with validated files immediately (e.g. open local PDF preview). */
  onFilesSelected?: (files: File[]) => void;
  disabled?: boolean;
};

const ALLOWED = new Set([".pdf", ".docx"]);

function fileExt(name: string) {
  const lower = name.toLowerCase();
  const idx = lower.lastIndexOf(".");
  return idx >= 0 ? lower.slice(idx) : "";
}

export default function UploadDropzone({ onFilesPicked, onFilesSelected, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  const pickFiles = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const handleFiles = useCallback(
    async (files: FileList | File[]) => {
      const list = Array.from(files);
      if (!list.length) return;
      const valid = list.filter((f) => ALLOWED.has(fileExt(f.name)));
      if (valid.length) onFilesSelected?.(valid);
      await onFilesPicked(valid);
    },
    [onFilesPicked],
  );

  return (
    <div
      className={`rounded-lg border-2 border-dashed p-5 ${
        disabled ? "border-slate-200 bg-slate-50" : "border-slate-300 bg-white"
      }`}
      onDragOver={(e) => {
        e.preventDefault();
      }}
      onDrop={(e) => {
        e.preventDefault();
        if (disabled) return;
        void handleFiles(e.dataTransfer.files);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".pdf,.docx"
        className="hidden"
        onChange={(e) => {
          if (!e.target.files) return;
          void handleFiles(e.target.files);
        }}
      />

      <div className="flex flex-col gap-2 items-start">
        <div className="font-medium text-slate-800">Drag & drop PDFs/DOCX here</div>
        <div className="text-sm text-slate-600">Select or drop multiple files at once (up to server limit).</div>
        <div className="text-sm text-slate-600">Or</div>
        <button
          type="button"
          disabled={disabled}
          onClick={pickFiles}
          className="rounded-md bg-slate-800 px-3 py-2 text-white text-sm hover:bg-slate-700 disabled:opacity-60"
        >
          Select files
        </button>
      </div>
    </div>
  );
}

