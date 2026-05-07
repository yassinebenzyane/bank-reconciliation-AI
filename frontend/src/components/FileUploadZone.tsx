"use client";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { FileSpreadsheet, FileText, Upload, X, CheckCircle2 } from "lucide-react";
import { cn, formatFileSize } from "@/lib/utils";
import type { UploadedFile } from "@/lib/types";

interface FileUploadZoneProps {
  csvFile: UploadedFile | null;
  xlsxFile: UploadedFile | null;
  onFilesSelected: (csv: File | null, xlsx: File | null) => void;
  disabled?: boolean;
}

export function FileUploadZone({
  csvFile,
  xlsxFile,
  onFilesSelected,
  disabled = false,
}: FileUploadZoneProps) {
  const [pendingCsv, setPendingCsv] = useState<File | null>(null);
  const [pendingXlsx, setPendingXlsx] = useState<File | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      let newCsv = pendingCsv;
      let newXlsx = pendingXlsx;

      for (const file of acceptedFiles) {
        if (file.name.toLowerCase().endsWith(".csv")) {
          newCsv = file;
          setPendingCsv(file);
        } else if (
          file.name.toLowerCase().endsWith(".xlsx") ||
          file.name.toLowerCase().endsWith(".xls")
        ) {
          newXlsx = file;
          setPendingXlsx(file);
        }
      }
      onFilesSelected(newCsv, newXlsx);
    },
    [pendingCsv, pendingXlsx, onFilesSelected],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "application/vnd.ms-excel": [".xls"],
    },
    disabled,
    multiple: true,
  });

  const hasFiles = csvFile || xlsxFile || pendingCsv || pendingXlsx;

  return (
    <div className="w-full space-y-3">
      {/* Drop zone */}
      {!hasFiles && (
        <div
          {...getRootProps()}
          className={cn(
            "border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200",
            isDragActive
              ? "border-blue-500 bg-blue-500/10 scale-[1.01]"
              : "border-slate-600 hover:border-blue-500/60 hover:bg-slate-800/60",
            disabled && "opacity-50 cursor-not-allowed",
          )}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center gap-2">
            <div className="w-10 h-10 rounded-full bg-slate-700 flex items-center justify-center">
              <Upload size={18} className={isDragActive ? "text-blue-400" : "text-slate-400"} />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-200">
                {isDragActive ? "Déposez vos fichiers ici" : "Glisser-déposer ou cliquer"}
              </p>
              <p className="text-xs text-slate-500 mt-0.5">
                Relevé <span className="text-slate-400 font-mono">.csv</span> + Matrice{" "}
                <span className="text-slate-400 font-mono">.xlsx</span>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* File pills */}
      {hasFiles && (
        <div className="flex flex-col gap-2">
          <FilePill
            icon={<FileText size={14} />}
            label="Relevé bancaire (.csv)"
            file={pendingCsv}
            uploaded={csvFile}
            onRemove={() => {
              setPendingCsv(null);
              onFilesSelected(null, pendingXlsx);
            }}
          />
          <FilePill
            icon={<FileSpreadsheet size={14} />}
            label="Matrice Excel (.xlsx)"
            file={pendingXlsx}
            uploaded={xlsxFile}
            onRemove={() => {
              setPendingXlsx(null);
              onFilesSelected(pendingCsv, null);
            }}
          />
          {/* Add more files */}
          {(!pendingCsv || !pendingXlsx) && (
            <div
              {...getRootProps()}
              className={cn(
                "border border-dashed border-slate-600 rounded-lg px-4 py-2 text-center cursor-pointer",
                "text-xs text-slate-500 hover:border-blue-500/60 hover:text-slate-400 transition-colors",
              )}
            >
              <input {...getInputProps()} />
              <span>+ Ajouter l&apos;autre fichier</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function FilePill({
  icon,
  label,
  file,
  uploaded,
  onRemove,
}: {
  icon: React.ReactNode;
  label: string;
  file: File | null;
  uploaded: UploadedFile | null;
  onRemove: () => void;
}) {
  const name = file?.name ?? uploaded?.name;
  const size = file?.size ?? uploaded?.size;
  const isUploaded = Boolean(uploaded);

  if (!file && !uploaded)
    return (
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-700 border-dashed">
        <span className="text-slate-600">{icon}</span>
        <span className="text-xs text-slate-600 italic">{label} — manquant</span>
      </div>
    );

  return (
    <div
      className={cn(
        "flex items-center gap-2 px-3 py-2 rounded-lg border text-sm",
        isUploaded
          ? "border-emerald-500/30 bg-emerald-500/5"
          : "border-blue-500/30 bg-blue-500/5",
      )}
    >
      <span className={isUploaded ? "text-emerald-400" : "text-blue-400"}>{icon}</span>
      <span className="flex-1 text-slate-200 truncate text-xs">{name}</span>
      {size && (
        <span className="text-xs text-slate-500 shrink-0">{formatFileSize(size)}</span>
      )}
      {isUploaded && <CheckCircle2 size={13} className="text-emerald-400 shrink-0" />}
      {!isUploaded && (
        <button
          onClick={onRemove}
          className="text-slate-500 hover:text-slate-300 transition-colors shrink-0"
        >
          <X size={13} />
        </button>
      )}
    </div>
  );
}
