"use client";
import { useEffect, useState, useCallback } from "react";
import { Header } from "@/components/Header";
import { ChatInterface } from "@/components/ChatInterface";
import { DataInspector, type ParsedData } from "@/components/DataInspector";
import { checkHealth, getSessionData } from "@/lib/api";
import { BarChart2 } from "lucide-react";

export default function Home() {
  const [backendOnline, setBackendOnline] = useState(false);
  const [inspectorData, setInspectorData] = useState<ParsedData | null>(null);
  const [showInspector, setShowInspector] = useState(true);

  useEffect(() => {
    const ping = async () => setBackendOnline(await checkHealth());
    ping();
    const interval = setInterval(ping, 10_000);
    return () => clearInterval(interval);
  }, []);

  const handleParsed = useCallback(async (sessionId: string) => {
    try {
      const res = await getSessionData(sessionId);
      if (res.status === "ok" && res.data) {
        setInspectorData(res.data as ParsedData);
        setShowInspector(true);
      }
    } catch {
      // inspector optional — parsing still worked
    }
  }, []);

  const hasInspector = Boolean(inspectorData && showInspector);

  return (
    <div className="flex flex-col h-screen" style={{ background: "var(--bg-base)" }}>
      <Header
        backendOnline={backendOnline}
        hasData={Boolean(inspectorData)}
        inspectorOpen={showInspector}
        onToggleInspector={() => setShowInspector((v) => !v)}
      />

      <main className="flex-1 overflow-hidden flex">
        <div
          className="flex flex-col overflow-hidden transition-all duration-300"
          style={{ width: hasInspector ? "55%" : "100%" }}
        >
          <ChatInterface backendOnline={backendOnline} onParsed={handleParsed} />
        </div>

        {hasInspector && (
          <div
            className="overflow-hidden transition-all duration-300"
            style={{
              width: "45%",
              borderLeft: "1px solid rgba(26,42,68,0.9)",
            }}
          >
            <DataInspector
              data={inspectorData!}
              onClose={() => setShowInspector(false)}
            />
          </div>
        )}
      </main>
    </div>
  );
}
