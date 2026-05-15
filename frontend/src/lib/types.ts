export type MessageRole = "user" | "assistant" | "system";

export interface ChoiceOption {
  label: string;  // "A", "B", ...
  text: string;   // "FC1183, FC1184 → 53 346,00 €"
}

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  choices?: ChoiceOption[];
}

export interface UploadedFile {
  name: string;
  type: "csv" | "xlsx";
  size: number;
}

export interface SessionState {
  sessionId: string | null;
  csvFile: UploadedFile | null;
  xlsxFile: UploadedFile | null;
  isReady: boolean;
}

export type ReconciliationStep =
  | "idle"
  | "uploading"
  | "parsing"
  | "classifying"
  | "matching"
  | "verifying"
  | "writing"
  | "done"
  | "error";

export interface StepInfo {
  id: ReconciliationStep;
  label: string;
  description: string;
}

export const STEPS: StepInfo[] = [
  { id: "uploading",   label: "Chargement",    description: "Réception des fichiers" },
  { id: "parsing",     label: "Parsing",       description: "Lecture CSV et Excel" },
  { id: "classifying", label: "Classification",description: "Règles + LLM Mistral" },
  { id: "matching",    label: "Rapprochement", description: "Matching multi-factures" },
  { id: "verifying",   label: "Vérification",  description: "Contrôle de cohérence" },
  { id: "writing",     label: "Écriture",      description: "Mise à jour Excel" },
];
