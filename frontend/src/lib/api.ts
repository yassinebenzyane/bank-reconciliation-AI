const BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export interface UploadResult {
  session_id: string;
  csv_filename: string | null;
  xlsx_filename: string | null;
  message: string;
}

export async function uploadFiles(
  csvFile: File | null,
  xlsxFile: File | null,
): Promise<UploadResult> {
  const form = new FormData();
  if (csvFile)  form.append("csv_file",  csvFile);
  if (xlsxFile) form.append("xlsx_file", xlsxFile);

  const res = await fetch(`${BASE}/api/upload`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Upload failed (${res.status})`);
  }
  return res.json();
}

import type { ChoiceOption } from "./types";

export async function* streamChat(
  message: string,
  sessionId: string | null,
  csvFilename?: string | null,
  xlsxFilename?: string | null,
  onChoices?: (options: ChoiceOption[]) => void,
): AsyncGenerator<string> {
  const res = await fetch(`${BASE}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      csv_filename: csvFilename,
      xlsx_filename: xlsxFilename,
    }),
  });

  if (!res.ok || !res.body) throw new Error(`Chat error (${res.status})`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const json = line.slice(6).trim();
      if (!json) continue;
      try {
        const parsed = JSON.parse(json);
        if (parsed.done) return;
        if (parsed.choices) { onChoices?.(parsed.choices); return; }
        if (parsed.delta) yield parsed.delta;
      } catch {
        // ignore malformed chunks
      }
    }
  }
}

export async function getSessionData(sessionId: string): Promise<{ status: string; data?: unknown }> {
  const res = await fetch(`${BASE}/api/session/${sessionId}/data`);
  if (!res.ok) throw new Error(`Data fetch failed (${res.status})`);
  return res.json();
}

export async function exportMatrix(sessionId: string): Promise<{ blob: Blob; filename: string }> {
  const res = await fetch(`${BASE}/api/session/${sessionId}/export`, { method: "POST" });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    let detail = `Export failed (${res.status})`;
    try { detail = JSON.parse(text)?.detail ?? detail; } catch { detail = text || detail; }
    throw new Error(detail);
  }
  const disposition = res.headers.get("content-disposition") ?? "";
  const match = disposition.match(/filename[^;=\n]*=([^;\n]*)/);
  const filename = match ? match[1].replace(/['"]/g, "").trim() : "matrice_updated.xlsx";
  const blob = await res.blob();
  return { blob, filename };
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/api/health`, { signal: AbortSignal.timeout(3000) });
    if (!res.ok) return false;
    const data = await res.json();
    return data?.version === "0.1.0";
  } catch {
    return false;
  }
}
