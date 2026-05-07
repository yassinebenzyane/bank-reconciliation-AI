"use client";
import { TrendingUp, User } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Message } from "@/lib/types";

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-3 animate-fade-in", isUser ? "flex-row-reverse" : "flex-row")}>
      {isUser ? (
        <div
          className="shrink-0 w-7 h-7 rounded-full flex items-center justify-center mt-0.5"
          style={{ background: "rgba(51,65,85,0.8)", border: "1px solid rgba(71,85,105,0.6)" }}
        >
          <User size={13} style={{ color: "#94a3b8" }} />
        </div>
      ) : (
        <div
          className="shrink-0 w-7 h-7 rounded-full flex items-center justify-center mt-0.5"
          style={{
            background: "linear-gradient(135deg, #1d4ed8, #3b82f6)",
            boxShadow: "0 2px 8px rgba(59,130,246,0.3)",
          }}
        >
          <TrendingUp size={13} className="text-white" />
        </div>
      )}

      <div
        className={cn(
          "rounded-2xl px-4 py-3 text-sm leading-relaxed",
          isUser
            ? "max-w-[75%] rounded-tr-sm"
            : "w-full max-w-[90%] rounded-tl-sm",
        )}
        style={
          isUser
            ? {
                background: "linear-gradient(135deg, rgba(37,99,235,0.25), rgba(29,78,216,0.15))",
                border: "1px solid rgba(59,130,246,0.25)",
                color: "#e2e8f0",
              }
            : {
                background: "rgba(12,21,38,0.9)",
                border: "1px solid rgba(26,42,68,0.9)",
                color: "#e2e8f0",
              }
        }
      >
        {message.isStreaming && message.content === "" ? (
          <TypingDots />
        ) : message.isStreaming ? (
          <>
            <RichContent content={message.content} />
            <span
              className="inline-block w-0.5 h-3.5 ml-0.5 align-middle animate-blink"
              style={{ background: "#60a5fa" }}
            />
          </>
        ) : (
          <RichContent content={message.content} />
        )}
      </div>
    </div>
  );
}

function TypingDots() {
  return (
    <span className="flex gap-1.5 items-center h-5">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-1.5 h-1.5 rounded-full animate-bounce"
          style={{
            background: "#3b82f6",
            animationDelay: `${i * 0.18}s`,
            animationDuration: "0.9s",
          }}
        />
      ))}
    </span>
  );
}

function RichContent({ content }: { content: string }) {
  return <div className="prose-chat">{buildNodes(content)}</div>;
}

function buildNodes(content: string): React.ReactNode[] {
  const lines = content.split("\n");
  const result: React.ReactNode[] = [];
  let i = 0;
  let listBuffer: { ordered: boolean; items: string[] } | null = null;

  const flushList = () => {
    if (!listBuffer) return;
    if (listBuffer.ordered) {
      result.push(
        <ol key={result.length} className="list-decimal ml-5 my-1 space-y-0.5">
          {listBuffer.items.map((item, j) => <li key={j}>{renderInline(item)}</li>)}
        </ol>,
      );
    } else {
      result.push(
        <ul key={result.length} className="list-disc ml-5 my-1 space-y-0.5">
          {listBuffer.items.map((item, j) => <li key={j}>{renderInline(item)}</li>)}
        </ul>,
      );
    }
    listBuffer = null;
  };

  while (i < lines.length) {
    const line = lines[i];

    if (line.trim().startsWith("|")) {
      flushList();
      const tableLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        tableLines.push(lines[i]);
        i++;
      }
      result.push(<MarkdownTable key={result.length} lines={tableLines} />);
      continue;
    }

    if (line.startsWith("- ") || line.startsWith("* ")) {
      const text = line.slice(2);
      if (listBuffer && !listBuffer.ordered) {
        listBuffer.items.push(text);
      } else {
        flushList();
        listBuffer = { ordered: false, items: [text] };
      }
      i++;
      continue;
    }

    const orderedMatch = line.match(/^(\d+)\.\s(.+)/);
    if (orderedMatch) {
      if (listBuffer?.ordered) {
        listBuffer.items.push(orderedMatch[2]);
      } else {
        flushList();
        listBuffer = { ordered: true, items: [orderedMatch[2]] };
      }
      i++;
      continue;
    }

    flushList();

    if (line.startsWith("---")) {
      result.push(<hr key={result.length} />);
    } else if (line.startsWith("### ")) {
      result.push(<h3 key={result.length}>{renderInline(line.slice(4))}</h3>);
    } else if (line.startsWith("## ")) {
      result.push(<h2 key={result.length}>{renderInline(line.slice(3))}</h2>);
    } else if (line.startsWith("# ")) {
      result.push(<h1 key={result.length}>{renderInline(line.slice(2))}</h1>);
    } else if (line.trim() === "") {
      result.push(<div key={result.length} className="h-1.5" />);
    } else {
      result.push(<p key={result.length}>{renderInline(line)}</p>);
    }

    i++;
  }

  flushList();
  return result;
}

function MarkdownTable({ lines }: { lines: string[] }) {
  if (lines.length < 2) return null;
  const isSep = (l: string) => /^\s*\|[\s\-:|]+\|/.test(l);
  const parseRow = (l: string) => l.split("|").slice(1, -1).map((c) => c.trim());

  const headers = parseRow(lines[0]);
  const rows = lines.filter((l, idx) => idx > 0 && !isSep(l)).map(parseRow);

  return (
    <div
      className="overflow-x-auto my-2 rounded-xl"
      style={{ border: "1px solid rgba(26,42,68,0.9)" }}
    >
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr>{headers.map((h, i) => <th key={i}>{renderInline(h)}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>{row.map((cell, j) => <td key={j}>{renderInline(cell)}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**"))
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    if (part.startsWith("`") && part.endsWith("`"))
      return <code key={i}>{part.slice(1, -1)}</code>;
    if (part.startsWith("*") && part.endsWith("*"))
      return <em key={i}>{part.slice(1, -1)}</em>;
    return part;
  });
}
