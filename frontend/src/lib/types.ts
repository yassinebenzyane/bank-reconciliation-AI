export type MessageRole = "user" | "assistant" | "system";

export interface Facture {
  date_facturation: string;
  mois_facturation: string;
  n_facture:        string;
  projet:           string;
  sous_traitant:    string;
  mois_prestation:  string;
  n_contrat:        string;
  client:           string;
  montant_ttc:      number;
}

export interface ChoiceOption {
  label:    string;      // "A", "B", ...
  text:     string;      // résumé textuel
  factures?: Facture[];  // détails complets de chaque facture de la combinaison
  total?:   number;
  ecart?:   number;
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
