"use client";
import { TrendingUp, BarChart2 } from "lucide-react";

interface HeaderProps {
  backendOnline: boolean;
  hasData?: boolean;
  inspectorOpen?: boolean;
  onToggleInspector?: () => void;
}

export function Header({ backendOnline, hasData, inspectorOpen, onToggleInspector }: HeaderProps) {
  return (
    <header
      className="relative flex items-center justify-between px-5 py-3 z-10 shrink-0"
      style={{
        background: "rgba(8,13,26,0.85)",
        backdropFilter: "blur(16px)",
        borderBottom: "1px solid rgba(26,42,68,0.9)",
      }}
    >
      <div className="flex items-center gap-3">
        <div
          className="flex items-center justify-center w-8 h-8 rounded-xl animate-glow"
          style={{
            background: "linear-gradient(135deg, #1d4ed8 0%, #3b82f6 50%, #06b6d4 100%)",
            boxShadow: "0 2px 12px rgba(59,130,246,0.35)",
          }}
        >
          <TrendingUp size={15} className="text-white" />
        </div>
        <div>
          <h1 className="text-sm font-semibold leading-none" style={{ color: "#f1f5f9" }}>
            Rapprochement Bancaire
          </h1>
          <p className="text-[10px] mt-0.5 font-medium" style={{ color: "#4d7ab5" }}>
            ECO Steering · IA
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {hasData && onToggleInspector && (
          <button
            onClick={onToggleInspector}
            title={inspectorOpen ? "Fermer l'inspection" : "Ouvrir l'inspection des données"}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-medium transition-all duration-150"
            style={
              inspectorOpen
                ? {
                    background: "rgba(59,130,246,0.15)",
                    border: "1px solid rgba(59,130,246,0.3)",
                    color: "#60a5fa",
                  }
                : {
                    background: "rgba(26,42,68,0.6)",
                    border: "1px solid rgba(26,42,68,0.9)",
                    color: "#475569",
                  }
            }
            onMouseEnter={(e) => {
              if (!inspectorOpen)
                (e.currentTarget as HTMLButtonElement).style.color = "#94a3b8";
            }}
            onMouseLeave={(e) => {
              if (!inspectorOpen)
                (e.currentTarget as HTMLButtonElement).style.color = "#475569";
            }}
          >
            <BarChart2 size={12} />
            Données
          </button>
        )}

        <div
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-full"
          style={{
            background: backendOnline ? "rgba(16,185,129,0.08)" : "rgba(239,68,68,0.08)",
            border: `1px solid ${backendOnline ? "rgba(16,185,129,0.2)" : "rgba(239,68,68,0.2)"}`,
          }}
        >
          <span
            className={backendOnline ? "animate-ping-dot" : ""}
            style={{
              display: "inline-block",
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: backendOnline ? "#10b981" : "#ef4444",
            }}
          />
          <span
            className="text-[11px] font-medium"
            style={{ color: backendOnline ? "#34d399" : "#f87171" }}
          >
            {backendOnline ? "API connectée" : "API hors ligne"}
          </span>
        </div>
      </div>
    </header>
  );
}
