"use client";
import { TrendingUp, FileSpreadsheet, FileText, HelpCircle, CheckCircle } from "lucide-react";

interface WelcomeScreenProps {
  onSuggestion: (text: string) => void;
}

const SUGGESTIONS = [
  {
    icon: <FileText size={15} />,
    label: "Déposer mes fichiers",
    desc: "Relevé CSV + Matrice Excel",
    text: "Je veux déposer mon relevé CSV et ma matrice Excel",
  },
  {
    icon: <FileSpreadsheet size={15} />,
    label: "Lancer le rapprochement",
    desc: "Parsing et analyse automatique",
    text: "Lancer le rapprochement",
  },
  {
    icon: <HelpCircle size={15} />,
    label: "Comment ça fonctionne ?",
    desc: "Explication du processus",
    text: "Comment fonctionne le rapprochement automatique ?",
  },
];

const FEATURES = [
  "Parsing 100% déterministe",
  "Matching multi-factures",
  "0 perte de formule Excel",
  "Q&A en langage naturel",
];

export function WelcomeScreen({ onSuggestion }: WelcomeScreenProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-6 pb-12 text-center animate-fade-in">
      <div className="relative mb-6">
        <div
          className="absolute inset-0 rounded-2xl blur-xl opacity-40"
          style={{ background: "linear-gradient(135deg,#1d4ed8,#06b6d4)" }}
        />
        <div
          className="relative w-16 h-16 rounded-2xl flex items-center justify-center"
          style={{
            background: "linear-gradient(135deg, #1d4ed8 0%, #3b82f6 50%, #06b6d4 100%)",
            boxShadow: "0 8px 32px rgba(59,130,246,0.4)",
          }}
        >
          <TrendingUp size={28} className="text-white" />
        </div>
      </div>

      <h2 className="text-2xl font-bold text-white mb-2 tracking-tight">
        Assistant Rapprochement
      </h2>
      <p className="text-sm max-w-sm mb-7 leading-relaxed" style={{ color: "#64748b" }}>
        Déposez votre relevé bancaire et votre matrice Excel.
        L&apos;IA classe, rapproche et met à jour automatiquement.
      </p>

      <div className="flex flex-wrap justify-center gap-2 mb-8">
        {FEATURES.map((f) => (
          <div
            key={f}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium"
            style={{
              background: "rgba(59,130,246,0.08)",
              border: "1px solid rgba(59,130,246,0.18)",
              color: "#93c5fd",
            }}
          >
            <CheckCircle size={11} style={{ color: "#10b981" }} />
            {f}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 w-full max-w-xl">
        {SUGGESTIONS.map((s) => (
          <button
            key={s.label}
            onClick={() => onSuggestion(s.text)}
            className="group flex flex-col gap-2 p-3.5 rounded-xl text-left transition-all duration-200"
            style={{
              background: "rgba(12,21,38,0.8)",
              border: "1px solid rgba(26,42,68,0.9)",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.borderColor = "rgba(59,130,246,0.4)";
              (e.currentTarget as HTMLButtonElement).style.background = "rgba(59,130,246,0.06)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.borderColor = "rgba(26,42,68,0.9)";
              (e.currentTarget as HTMLButtonElement).style.background = "rgba(12,21,38,0.8)";
            }}
          >
            <span
              className="flex items-center justify-center w-7 h-7 rounded-lg"
              style={{ background: "rgba(59,130,246,0.12)", color: "#60a5fa" }}
            >
              {s.icon}
            </span>
            <div>
              <p className="text-sm font-medium text-white">{s.label}</p>
              <p className="text-[11px] mt-0.5" style={{ color: "#475569" }}>{s.desc}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
