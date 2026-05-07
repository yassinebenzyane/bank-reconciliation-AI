"use client";
import { useRef, KeyboardEvent, ChangeEvent } from "react";
import { Send, Paperclip, Square } from "lucide-react";
import { cn } from "@/lib/utils";

interface MessageInputProps {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  onFileClick: () => void;
  isStreaming: boolean;
  onStop?: () => void;
  disabled?: boolean;
  placeholder?: string;
}

export function MessageInput({
  value,
  onChange,
  onSend,
  onFileClick,
  isStreaming,
  onStop,
  disabled = false,
  placeholder = "Posez une question ou déposez vos fichiers…",
}: MessageInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isStreaming && value.trim()) onSend();
    }
  };

  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
    const ta = e.target;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 140) + "px";
  };

  const hasValue = value.trim().length > 0;

  return (
    <div className="px-4 pb-4 pt-2">
      <div
        className={cn(
          "flex items-end gap-2 rounded-2xl px-3 py-2 transition-all duration-200",
          disabled && "opacity-50 pointer-events-none",
        )}
        style={{
          background: "rgba(12,21,38,0.95)",
          border: "1px solid rgba(26,42,68,0.9)",
        }}
        onFocus={() => {}}
      >
        <button
          onClick={onFileClick}
          disabled={disabled || isStreaming}
          title="Importer des fichiers"
          className="shrink-0 mb-0.5 p-1.5 rounded-lg transition-colors disabled:opacity-40"
          style={{ color: "#475569" }}
          onMouseEnter={(e) => ((e.target as HTMLButtonElement).style.color = "#94a3b8")}
          onMouseLeave={(e) => ((e.target as HTMLButtonElement).style.color = "#475569")}
        >
          <Paperclip size={16} />
        </button>

        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={disabled || isStreaming}
          placeholder={placeholder}
          rows={1}
          className="flex-1 resize-none bg-transparent text-sm outline-none min-h-[24px] max-h-[140px] leading-6"
          style={{ color: "#e2e8f0" }}
        />

        {isStreaming ? (
          <button
            onClick={onStop}
            className="shrink-0 mb-0.5 p-1.5 rounded-lg transition-colors"
            style={{
              background: "rgba(239,68,68,0.15)",
              color: "#f87171",
              border: "1px solid rgba(239,68,68,0.2)",
            }}
            title="Arrêter"
          >
            <Square size={14} />
          </button>
        ) : (
          <button
            onClick={onSend}
            disabled={disabled || !hasValue}
            title="Envoyer (Entrée)"
            className="shrink-0 mb-0.5 p-1.5 rounded-lg transition-all duration-150"
            style={
              hasValue
                ? {
                    background: "linear-gradient(135deg, #1d4ed8, #3b82f6)",
                    color: "white",
                    boxShadow: "0 2px 8px rgba(59,130,246,0.35)",
                  }
                : {
                    background: "rgba(30,42,68,0.6)",
                    color: "#334155",
                    cursor: "not-allowed",
                  }
            }
          >
            <Send size={14} />
          </button>
        )}
      </div>
      <p className="text-center mt-1.5" style={{ fontSize: 10, color: "#1e3a5f" }}>
        Entrée pour envoyer · Maj+Entrée nouvelle ligne
      </p>
    </div>
  );
}
