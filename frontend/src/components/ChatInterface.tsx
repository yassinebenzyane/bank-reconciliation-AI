"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { X, ChevronDown, AlertTriangle, WifiOff, Sparkles, Download, Loader2 } from "lucide-react";
import { MessageBubble } from "./MessageBubble";
import { MessageInput } from "./MessageInput";
import { WelcomeScreen } from "./WelcomeScreen";
import { FileUploadZone } from "./FileUploadZone";
import { uploadFiles, streamChat, exportMatrix } from "@/lib/api";
import { generateId } from "@/lib/utils";
import type { Message, SessionState, UploadedFile, ChoiceOption } from "@/lib/types";

interface ChatInterfaceProps {
  backendOnline: boolean;
  onParsed?: (sessionId: string) => void;
}

const POST_PARSE_SUGGESTIONS = [
  "Vérifie la balance comptable du relevé",
  "Montre les transactions de type 44",
  "Quelles factures sont ouvertes ?",
  "Y a-t-il des anomalies ou incohérences ?",
];

export function ChatInterface({ backendOnline, onParsed }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [showUploadPanel, setShowUploadPanel] = useState(false);
  const [pendingCsv, setPendingCsv] = useState<File | null>(null);
  const [pendingXlsx, setPendingXlsx] = useState<File | null>(null);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);
  const [isParsed, setIsParsed] = useState(false);
  const [isReconDone, setIsReconDone] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [pendingChoices, setPendingChoices] = useState<ChoiceOption[] | null>(null);

  const [session, setSession] = useState<SessionState>({
    sessionId: null,
    csvFile: null,
    xlsxFile: null,
    isReady: false,
  });

  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const addMessage = (role: Message["role"], content: string, streaming = false): string => {
    const id = generateId();
    setMessages((prev) => [...prev, { id, role, content, timestamp: new Date(), isStreaming: streaming }]);
    return id;
  };

  const updateMessage = (id: string, content: string, streaming = false) => {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, content, isStreaming: streaming } : m)));
  };

  const removeMessage = (id: string) => {
    setMessages((prev) => prev.filter((m) => m.id !== id));
  };

  const showError = (msg: string) => {
    setErrorBanner(msg);
    setTimeout(() => setErrorBanner(null), 6000);
  };

  const triggerParsing = async (s: typeof session) => {
    const assistantId = addMessage("assistant", "", true);
    setIsStreaming(true);
    let accumulated = "";
    try {
      const gen = streamChat("lancer", s.sessionId, s.csvFile?.name, s.xlsxFile?.name);
      for await (const delta of gen) {
        accumulated += delta;
        updateMessage(assistantId, accumulated, true);
      }
      updateMessage(assistantId, accumulated, false);
      setIsParsed(true);
      if (s.sessionId) onParsed?.(s.sessionId);
    } catch {
      removeMessage(assistantId);
      showError("Erreur lors du parsing. Vérifiez que le backend tourne.");
    } finally {
      setIsStreaming(false);
    }
  };

  const handleChoiceClick = (choice: ChoiceOption) => {
    setPendingChoices(null);
    handleSend(choice.label);
  };

  const handleExport = async () => {
    if (!session.sessionId || isExporting) return;
    setIsExporting(true);
    try {
      const { blob, filename } = await exportMatrix(session.sessionId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      addMessage("assistant", `✅ Matrice générée et téléchargée : **${filename}**`);
    } catch (err) {
      showError(`Erreur lors de la génération : ${String(err)}`);
    } finally {
      setIsExporting(false);
    }
  };

  const handleUpload = useCallback(async () => {
    if (!pendingCsv && !pendingXlsx) return;
    setIsUploading(true);
    try {
      const result = await uploadFiles(pendingCsv, pendingXlsx);

      const csvUploaded: UploadedFile | null = result.csv_filename
        ? { name: result.csv_filename, type: "csv", size: pendingCsv?.size ?? 0 }
        : null;
      const xlsxUploaded: UploadedFile | null = result.xlsx_filename
        ? { name: result.xlsx_filename, type: "xlsx", size: pendingXlsx?.size ?? 0 }
        : null;

      const newSession: SessionState = {
        sessionId: result.session_id,
        csvFile: csvUploaded,
        xlsxFile: xlsxUploaded,
        isReady: Boolean(csvUploaded && xlsxUploaded),
      };
      setSession(newSession);
      setPendingCsv(null);
      setPendingXlsx(null);
      setShowUploadPanel(false);
      addMessage("assistant", result.message);

      if (csvUploaded && xlsxUploaded) {
        setTimeout(() => triggerParsing(newSession), 400);
      }
    } catch (err) {
      const msg = String(err).includes("fetch")
        ? "Impossible de contacter le backend. Vérifiez que uvicorn tourne sur le port 8001."
        : `Erreur lors de l'upload : ${String(err)}`;
      showError(msg);
    } finally {
      setIsUploading(false);
    }
  }, [pendingCsv, pendingXlsx]);

  useEffect(() => {
    if (pendingCsv && pendingXlsx) handleUpload();
  }, [pendingCsv, pendingXlsx, handleUpload]);

  const handleSend = async (overrideText?: string) => {
    const text = (overrideText ?? input).trim();
    if (!text || isStreaming || !backendOnline) return;

    setInput("");
    addMessage("user", text);

    const assistantId = addMessage("assistant", "", true);
    setIsStreaming(true);
    let accumulated = "";

    try {
      setPendingChoices(null);
      const gen = streamChat(text, session.sessionId, session.csvFile?.name, session.xlsxFile?.name, setPendingChoices);
      for await (const delta of gen) {
        accumulated += delta;
        updateMessage(assistantId, accumulated, true);
      }
      updateMessage(assistantId, accumulated, false);
      if (text.toLowerCase().includes("lancer") || text.toLowerCase().includes("parser")) {
        setIsParsed(true);
      }
      if (accumulated.toLowerCase().includes("générer la matrice") || accumulated.toLowerCase().includes("rapprochement terminé")) {
        setIsReconDone(true);
      }
    } catch (err) {
      removeMessage(assistantId);
      const isNetworkError = ["fetch", "network", "failed"].some((w) =>
        String(err).toLowerCase().includes(w),
      );
      showError(
        isNetworkError
          ? "Connexion au backend perdue. Vérifiez que uvicorn tourne sur http://localhost:8001."
          : `Erreur : ${String(err)}`,
      );
    } finally {
      setIsStreaming(false);
    }
  };

  const handleStop = () => {
    abortRef.current?.abort();
    setIsStreaming(false);
  };

  const handleSuggestion = (text: string) => {
    setInput(text);
  };

  const handleQuickSend = (text: string) => {
    handleSend(text);
  };

  return (
    <div className="flex flex-col h-full">
      {!backendOnline && (
        <div className="flex items-center gap-2 px-4 py-2.5 bg-amber-500/10 border-b border-amber-500/20 text-amber-400 text-xs animate-fade-in">
          <WifiOff size={13} className="shrink-0" />
          <span className="flex-1">
            Backend hors ligne —{" "}
            <code className="font-mono bg-amber-500/10 px-1 py-0.5 rounded">
              cd backend &amp;&amp; C:\Users\Asus\miniconda3\python.exe -m uvicorn main:app --reload --port 8001
            </code>
          </span>
        </div>
      )}

      {errorBanner && (
        <div className="flex items-start gap-2 px-4 py-2.5 bg-red-500/10 border-b border-red-500/20 text-red-400 text-xs animate-fade-in">
          <AlertTriangle size={13} className="shrink-0 mt-0.5" />
          <span className="flex-1">{errorBanner}</span>
          <button onClick={() => setErrorBanner(null)} className="shrink-0 hover:text-red-300 transition-colors">
            <X size={13} />
          </button>
        </div>
      )}

      {(showUploadPanel || pendingCsv || pendingXlsx) && (
        <div className="border-b border-slate-700/60 bg-slate-900/60 px-4 py-3 animate-slide-up">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">Fichiers</span>
            <button onClick={() => setShowUploadPanel(false)} className="text-slate-500 hover:text-slate-300 transition-colors">
              <X size={14} />
            </button>
          </div>
          <FileUploadZone
            csvFile={session.csvFile}
            xlsxFile={session.xlsxFile}
            onFilesSelected={(csv, xlsx) => { setPendingCsv(csv); setPendingXlsx(xlsx); }}
            disabled={isUploading}
          />
          {(pendingCsv || pendingXlsx) && !(pendingCsv && pendingXlsx) && (
            <button
              onClick={handleUpload}
              disabled={isUploading}
              className="mt-2 w-full py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition-colors disabled:opacity-50"
            >
              {isUploading ? "Envoi en cours…" : "Envoyer le fichier"}
            </button>
          )}
        </div>
      )}

      {(session.csvFile || session.xlsxFile) && !showUploadPanel && (
        <div className="px-4 py-2 border-b border-slate-700/60 bg-slate-900/40">
          <button
            onClick={() => setShowUploadPanel(true)}
            className="flex items-center gap-2 text-xs text-slate-400 hover:text-slate-200 transition-colors"
          >
            <span className="flex gap-1.5">
              {session.csvFile && (
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                  CSV ✓
                </span>
              )}
              {session.xlsxFile && (
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                  XLSX ✓
                </span>
              )}
            </span>
            <span className={isParsed ? "text-blue-400 font-medium" : session.isReady ? "text-emerald-400 font-medium" : ""}>
              {isParsed ? "Données ingérées" : session.isReady ? "Prêt pour le parsing" : "1 fichier manquant"}
            </span>
            <ChevronDown size={12} />
          </button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-4 py-6">
        {messages.length === 0 ? (
          <WelcomeScreen onSuggestion={handleSuggestion} />
        ) : (
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}

            {pendingChoices && !isStreaming && (
              <div className="animate-fade-in px-1">
                <p className="text-xs text-amber-400 mb-3 font-medium">
                  Plusieurs combinaisons possibles — choisissez :
                </p>
                <div className="flex flex-col gap-4">
                  {pendingChoices.map((opt) => (
                    <div
                      key={opt.label}
                      className="rounded-xl border border-amber-500/30 bg-amber-500/5 overflow-hidden"
                    >
                      {/* En-tête de l'option */}
                      <div className="flex items-center justify-between px-4 py-2.5 border-b border-amber-500/20">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-amber-500/20 border border-amber-500/40
                                           flex items-center justify-center text-xs font-bold text-amber-300">
                            {opt.label}
                          </span>
                          <span className="text-sm font-medium text-amber-200">
                            Option {opt.label}
                          </span>
                          {opt.factures && (
                            <span className="text-xs text-amber-400/70">
                              · {opt.factures.length} facture{opt.factures.length > 1 ? "s" : ""}
                            </span>
                          )}
                        </div>
                        <div className="text-right">
                          <span className="text-sm font-semibold text-amber-200">
                            {opt.total?.toLocaleString("fr-FR", { minimumFractionDigits: 2 })} €
                          </span>
                          {opt.ecart !== undefined && opt.ecart > 0 && (
                            <span className="ml-2 text-xs text-amber-400/70">
                              écart {opt.ecart.toFixed(2)} €
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Tableau des factures */}
                      {opt.factures && opt.factures.length > 0 && (
                        <div className="overflow-x-auto">
                          <table className="w-full text-xs">
                            <thead>
                              <tr className="bg-amber-500/10 text-amber-400/80">
                                <th className="px-3 py-2 text-left font-medium whitespace-nowrap">N° Facture</th>
                                <th className="px-3 py-2 text-left font-medium whitespace-nowrap">Date</th>
                                <th className="px-3 py-2 text-left font-medium whitespace-nowrap">Mois Fact.</th>
                                <th className="px-3 py-2 text-left font-medium whitespace-nowrap">Projet / Contrat</th>
                                <th className="px-3 py-2 text-left font-medium whitespace-nowrap">Sous-traitant</th>
                                <th className="px-3 py-2 text-left font-medium whitespace-nowrap">Mois Prest.</th>
                                <th className="px-3 py-2 text-left font-medium whitespace-nowrap">N° Contrat</th>
                                <th className="px-3 py-2 text-left font-medium whitespace-nowrap">Client</th>
                                <th className="px-3 py-2 text-right font-medium whitespace-nowrap">Montant TTC</th>
                              </tr>
                            </thead>
                            <tbody>
                              {opt.factures.map((f, fi) => (
                                <tr
                                  key={fi}
                                  className="border-t border-amber-500/10 text-slate-300 hover:bg-amber-500/5"
                                >
                                  <td className="px-3 py-2 font-mono text-amber-300 whitespace-nowrap">{f.n_facture || "—"}</td>
                                  <td className="px-3 py-2 whitespace-nowrap">{f.date_facturation || "—"}</td>
                                  <td className="px-3 py-2 whitespace-nowrap">{f.mois_facturation || "—"}</td>
                                  <td className="px-3 py-2 max-w-[200px] truncate" title={f.projet}>{f.projet || "—"}</td>
                                  <td className="px-3 py-2 max-w-[140px] truncate" title={f.sous_traitant}>{f.sous_traitant || "—"}</td>
                                  <td className="px-3 py-2 whitespace-nowrap">{f.mois_prestation || "—"}</td>
                                  <td className="px-3 py-2 whitespace-nowrap">{f.n_contrat || "—"}</td>
                                  <td className="px-3 py-2 whitespace-nowrap">{f.client || "—"}</td>
                                  <td className="px-3 py-2 text-right font-mono whitespace-nowrap">
                                    {f.montant_ttc.toLocaleString("fr-FR", { minimumFractionDigits: 2 })} €
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}

                      {/* Bouton de sélection */}
                      <div className="px-4 py-2.5 flex justify-end border-t border-amber-500/20">
                        <button
                          onClick={() => handleChoiceClick(opt)}
                          className="px-4 py-1.5 rounded-lg text-sm font-medium
                                     bg-amber-500/20 border border-amber-500/40 text-amber-200
                                     hover:bg-amber-500/35 hover:border-amber-400/60
                                     transition-all duration-150"
                        >
                          Choisir l&apos;option {opt.label}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {isParsed && !isStreaming && !pendingChoices && (
              <div className="pt-1">
                <div className="flex items-center gap-1.5 mb-2 text-xs text-slate-500">
                  <Sparkles size={11} />
                  <span>Questions de vérification</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {POST_PARSE_SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => handleQuickSend(s)}
                      disabled={isStreaming}
                      className="px-3 py-1.5 rounded-xl border border-slate-600/60 bg-slate-800/50
                                 text-xs text-slate-300 hover:border-blue-500/50 hover:bg-slate-800 hover:text-white
                                 transition-all duration-150 disabled:opacity-40"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {isReconDone && !isStreaming && !pendingChoices && (
              <div className="animate-fade-in flex justify-center pt-2 pb-1">
                <button
                  onClick={handleExport}
                  disabled={isExporting}
                  className="flex items-center gap-2.5 px-6 py-3 rounded-xl text-sm font-semibold
                             bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-800/60
                             text-white shadow-lg shadow-emerald-500/20
                             transition-all duration-150 disabled:cursor-not-allowed"
                >
                  {isExporting ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Génération en cours…
                    </>
                  ) : (
                    <>
                      <Download size={16} />
                      Générer la matrice Excel
                    </>
                  )}
                </button>
              </div>
            )}

            {session.isReady && !isParsed && !isStreaming && !pendingChoices && (
              <div className="flex justify-center pt-2">
                <button
                  onClick={() => handleQuickSend("Lancer le parsing")}
                  className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition-colors shadow-lg shadow-blue-500/20"
                >
                  Lancer le parsing
                </button>
              </div>
            )}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="shrink-0 border-t border-slate-700/60 bg-slate-900/60 backdrop-blur-sm">
        <MessageInput
          value={input}
          onChange={setInput}
          onSend={() => handleSend()}
          onFileClick={() => setShowUploadPanel(true)}
          isStreaming={isStreaming}
          onStop={handleStop}
          disabled={!backendOnline}
          placeholder={
            !backendOnline
              ? "Backend hors ligne — démarrez uvicorn d'abord"
              : isParsed
              ? "Posez une question sur les données ingérées…"
              : session.isReady
              ? "Tapez votre message ou lancez le parsing…"
              : "Déposez vos fichiers ou posez une question…"
          }
        />
      </div>
    </div>
  );
}
