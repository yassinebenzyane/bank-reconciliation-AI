"use client";
import { useState } from "react";
import {
  BarChart2, ArrowDownUp, FileText, PieChart, Landmark, X,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface Transaction {
  date_operation: string;
  sens: string;
  montant: number;
  type_operation: string;
  libelle: string;
  reference?: string;
}
interface Facture {
  id: string;
  client: string;
  montant_ttc: number;
  date_echeance: string;
}
interface Pret {
  nom: string;
  montant_initial: number;
  mensualite_totale: number;
  mensualite_remboursement: number;
  assurance_mensuelle: number;
  rembourse_a_date: number;
  reste_a_rembourser: number;
  derniere_echeance: string;
}
interface TvaRow {
  mois: string;
  tva_collectee?: number;
  tva_deductible_st?: number;
  tva_deductible_fg?: number;
  tva_due?: number;
}
interface BudgetRow {
  mois: string;
  total_encaissements?: number;
  total_decaissements?: number;
  variation_tresorerie?: number;
  tresorerie_debut?: number;
  tresorerie_fin?: number;
  ca_reellement_encaisse?: number;
  st_reellement_payes?: number;
}

export interface ParsedData {
  csv?: {
    nb_transactions: number;
    solde_initial: number;
    solde_final: number;
    total_debits: number;
    total_credits: number;
    types: Record<string, number>;
    transactions: Transaction[];
  };
  xlsx?: {
    nb_ouvertes: number;
    nb_payees: number;
    total_ouvert: number;
    clients: string[];
    factures: Facture[];
    nb_st_ouverts: number;
    total_st_ouvert: number;
    st_ouverts: Array<{ id: string; client: string; montant_ttc: number }>;
    nb_fg: number;
    nb_ndf: number;
    nb_paies: number;
    tva: TvaRow[];
    pret?: Pret;
    budget_treso: BudgetRow[];
  };
}

const fmt = (n?: number | null) =>
  n != null ? n.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " €" : "—";

const TYPE_LABELS: Record<string, string> = {
  "05": "Vir. clients", "06": "Vir. ST", "08": "Prélèvements",
  "11": "Carte/NdF", "44": "International", "62": "Frais bancaires", "91": "Divers",
};

type Tab = "resume" | "transactions" | "factures" | "budget" | "tva";

const TABS: Array<{ id: Tab; label: string; icon: React.ReactNode }> = [
  { id: "resume",       label: "Résumé",       icon: <BarChart2 size={13} /> },
  { id: "transactions", label: "Transactions",  icon: <ArrowDownUp size={13} /> },
  { id: "factures",     label: "Factures",      icon: <FileText size={13} /> },
  { id: "budget",       label: "Budget",        icon: <PieChart size={13} /> },
  { id: "tva",          label: "TVA / Prêt",    icon: <Landmark size={13} /> },
];

interface DataInspectorProps {
  data: ParsedData;
  onClose: () => void;
}

export function DataInspector({ data, onClose }: DataInspectorProps) {
  const [tab, setTab] = useState<Tab>("resume");
  const { csv, xlsx } = data;

  return (
    <div className="flex flex-col h-full animate-slide-up" style={{ background: "rgba(8,13,26,0.98)" }}>

      <div
        className="flex items-center justify-between px-4 py-2.5 shrink-0"
        style={{ borderBottom: "1px solid rgba(26,42,68,0.9)" }}
      >
        <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "#4d7ab5" }}>
          Inspection des données
        </span>
        <button
          onClick={onClose}
          className="p-1 rounded-md transition-colors"
          style={{ color: "#334155" }}
          onMouseEnter={(e) => ((e.target as HTMLElement).style.color = "#94a3b8")}
          onMouseLeave={(e) => ((e.target as HTMLElement).style.color = "#334155")}
        >
          <X size={14} />
        </button>
      </div>

      <div
        className="flex shrink-0 px-2 pt-1.5 gap-0.5 overflow-x-auto"
        style={{ borderBottom: "1px solid rgba(26,42,68,0.9)" }}
      >
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-t-md text-[11px] font-medium whitespace-nowrap transition-all"
            style={
              tab === t.id
                ? { color: "#60a5fa", background: "rgba(59,130,246,0.1)", borderBottom: "2px solid #3b82f6" }
                : { color: "#475569" }
            }
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-3">
        {tab === "resume"       && <TabResume csv={csv} xlsx={xlsx} />}
        {tab === "transactions" && <TabTransactions csv={csv} />}
        {tab === "factures"     && <TabFactures xlsx={xlsx} />}
        {tab === "budget"       && <TabBudget xlsx={xlsx} />}
        {tab === "tva"          && <TabTvaPret xlsx={xlsx} />}
      </div>
    </div>
  );
}

function Kpi({ label, value, sub, color = "#60a5fa" }: {
  label: string; value: string; sub?: string; color?: string;
}) {
  return (
    <div
      className="rounded-xl p-3"
      style={{ background: "rgba(12,21,38,0.9)", border: "1px solid rgba(26,42,68,0.9)" }}
    >
      <p className="text-[10px] uppercase tracking-wider mb-1" style={{ color: "#475569" }}>{label}</p>
      <p className="text-base font-bold" style={{ color }}>{value}</p>
      {sub && <p className="text-[10px] mt-0.5" style={{ color: "#334155" }}>{sub}</p>}
    </div>
  );
}

function InspectorTable({ headers, rows }: {
  headers: string[];
  rows: (string | number | React.ReactNode)[][];
}) {
  return (
    <div className="overflow-x-auto rounded-xl" style={{ border: "1px solid rgba(26,42,68,0.9)" }}>
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr style={{ borderBottom: "1px solid rgba(59,130,246,0.2)" }}>
            {headers.map((h, i) => (
              <th
                key={i}
                className="px-3 py-2 text-left font-semibold uppercase tracking-wider text-[10px] whitespace-nowrap"
                style={{ background: "rgba(59,130,246,0.07)", color: "#4d7ab5" }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={i}
              style={{ borderBottom: "1px solid rgba(26,42,68,0.6)" }}
              className="transition-colors"
              onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.background = "rgba(59,130,246,0.04)")}
              onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.background = "transparent")}
            >
              {row.map((cell, j) => (
                <td key={j} className="px-3 py-2" style={{ color: "#94a3b8" }}>
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TabResume({ csv, xlsx }: { csv?: ParsedData["csv"]; xlsx?: ParsedData["xlsx"] }) {
  const balanceOk = csv
    ? Math.abs(csv.solde_initial + csv.total_credits - csv.total_debits - csv.solde_final) <= 1
    : null;

  return (
    <div className="space-y-4">
      {csv && (
        <>
          <p className="text-[10px] uppercase tracking-wider font-semibold" style={{ color: "#4d7ab5" }}>
            Relevé bancaire
          </p>
          <div className="grid grid-cols-2 gap-2">
            <Kpi label="Transactions" value={String(csv.nb_transactions)} />
            <Kpi
              label="Balance"
              value={balanceOk ? "✓ Équilibrée" : "✗ Écart"}
              color={balanceOk ? "#34d399" : "#f87171"}
            />
            <Kpi label="Solde initial" value={fmt(csv.solde_initial)} color="#94a3b8" />
            <Kpi label="Solde final"   value={fmt(csv.solde_final)}   color="#94a3b8" />
            <Kpi label="Débits"   value={fmt(csv.total_debits)}   color="#f87171" />
            <Kpi label="Crédits"  value={fmt(csv.total_credits)}  color="#34d399" />
          </div>
          <div className="grid grid-cols-2 gap-1">
            {Object.entries(csv.types).sort().map(([code, n]) => (
              <div
                key={code}
                className="flex justify-between items-center px-2.5 py-1.5 rounded-lg text-[11px]"
                style={{ background: "rgba(12,21,38,0.8)", border: "1px solid rgba(26,42,68,0.7)" }}
              >
                <span style={{ color: "#60a5fa" }}><code>{code}</code> {TYPE_LABELS[code] ?? ""}</span>
                <span className="font-semibold" style={{ color: "#e2e8f0" }}>{n}</span>
              </div>
            ))}
          </div>
        </>
      )}

      {xlsx && (
        <>
          <p className="text-[10px] uppercase tracking-wider font-semibold mt-4" style={{ color: "#4d7ab5" }}>
            Matrice Excel
          </p>
          <div className="grid grid-cols-2 gap-2">
            <Kpi label="Factures ouvertes" value={String(xlsx.nb_ouvertes)} sub={fmt(xlsx.total_ouvert)} color="#fb923c" />
            <Kpi label="Factures payées"   value={String(xlsx.nb_payees)}   color="#34d399" />
            <Kpi label="ST ouvertes"  value={String(xlsx.nb_st_ouverts)} sub={fmt(xlsx.total_st_ouvert)} color="#fb923c" />
            <Kpi label="Frais Gén."   value={String(xlsx.nb_fg)} color="#94a3b8" />
            <Kpi label="Notes de frais" value={String(xlsx.nb_ndf)}  color="#94a3b8" />
            <Kpi label="Paies"          value={String(xlsx.nb_paies)} color="#94a3b8" />
          </div>
          {xlsx.pret && (
            <Kpi
              label={`Prêt — ${xlsx.pret.nom}`}
              value={`${fmt(xlsx.pret.reste_a_rembourser)} restant`}
              sub={`${fmt(xlsx.pret.mensualite_totale)} / mois`}
              color="#a78bfa"
            />
          )}
        </>
      )}
    </div>
  );
}

function TabTransactions({ csv }: { csv?: ParsedData["csv"] }) {
  if (!csv?.transactions?.length) return <Empty>Aucune transaction disponible</Empty>;
  return (
    <div className="space-y-2">
      <p className="text-[10px]" style={{ color: "#475569" }}>{csv.transactions.length} transactions</p>
      <InspectorTable
        headers={["Date", "Sens", "Montant", "Type", "Libellé"]}
        rows={csv.transactions.map((t) => [
          <span key="d" style={{ color: "#64748b" }}>{t.date_operation}</span>,
          <span key="s" style={{ color: t.sens === "credit" ? "#34d399" : "#f87171" }}>
            {t.sens === "credit" ? "↑" : "↓"} {t.sens}
          </span>,
          <span key="m" className="font-medium" style={{ color: t.sens === "credit" ? "#34d399" : "#f87171" }}>
            {fmt(t.montant)}
          </span>,
          <code key="t" style={{ color: "#60a5fa", fontSize: 10 }}>{t.type_operation}</code>,
          <span key="l" style={{ color: "#94a3b8", maxWidth: 160, display: "block", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {String(t.libelle ?? "").slice(0, 45)}
          </span>,
        ])}
      />
    </div>
  );
}

function TabFactures({ xlsx }: { xlsx?: ParsedData["xlsx"] }) {
  if (!xlsx) return <Empty>Données Excel non disponibles</Empty>;
  const [showST, setShowST] = useState(false);

  const data = showST ? xlsx.st_ouverts : xlsx.factures;
  const total = showST ? xlsx.total_st_ouvert : xlsx.total_ouvert;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <button
          onClick={() => setShowST(false)}
          className="text-[11px] px-2.5 py-1 rounded-lg font-medium transition-all"
          style={!showST
            ? { background: "rgba(59,130,246,0.15)", color: "#60a5fa", border: "1px solid rgba(59,130,246,0.25)" }
            : { color: "#475569" }}
        >
          Clients ({xlsx.nb_ouvertes})
        </button>
        <button
          onClick={() => setShowST(true)}
          className="text-[11px] px-2.5 py-1 rounded-lg font-medium transition-all"
          style={showST
            ? { background: "rgba(59,130,246,0.15)", color: "#60a5fa", border: "1px solid rgba(59,130,246,0.25)" }
            : { color: "#475569" }}
        >
          Sous-traitants ({xlsx.nb_st_ouverts})
        </button>
        <span className="ml-auto text-[11px] font-semibold" style={{ color: "#fb923c" }}>
          Total : {fmt(total)}
        </span>
      </div>
      {data.length ? (
        <InspectorTable
          headers={showST ? ["N° Facture", "Client", "Montant TTC"] : ["N° Facture", "Client", "Montant TTC", "Échéance"]}
          rows={data.map((f) => [
            <span key="id" style={{ color: "#60a5fa" }}>{f.id}</span>,
            <span key="cl" style={{ color: "#e2e8f0" }}>{String(f.client ?? "").slice(0, 25)}</span>,
            <span key="m" className="font-semibold" style={{ color: "#fb923c" }}>{fmt(f.montant_ttc)}</span>,
            ...("date_echeance" in f && !showST
              ? [<span key="e" style={{ color: "#64748b" }}>{(f as Facture).date_echeance || "—"}</span>]
              : []),
          ])}
        />
      ) : <Empty>Aucune facture ouverte</Empty>}
    </div>
  );
}

function TabBudget({ xlsx }: { xlsx?: ParsedData["xlsx"] }) {
  if (!xlsx?.budget_treso?.length) return <Empty>Budget non disponible</Empty>;
  const latest = xlsx.budget_treso[xlsx.budget_treso.length - 1];
  const mois = latest?.mois?.slice(0, 7) ?? "";

  return (
    <div className="space-y-3">
      <p className="text-[10px]" style={{ color: "#475569" }}>Mois : <span style={{ color: "#60a5fa" }}>{mois}</span></p>
      <InspectorTable
        headers={["Poste", "Montant"]}
        rows={[
          ["Encaissements réels",   <span key="e" style={{ color: "#34d399" }}>{fmt(latest?.ca_reellement_encaisse)}</span>],
          ["ST réellement payés",   <span key="s" style={{ color: "#f87171" }}>{fmt(latest?.st_reellement_payes)}</span>],
          ["Total encaissements",   <span key="te" className="font-semibold" style={{ color: "#34d399" }}>{fmt(latest?.total_encaissements)}</span>],
          ["Total décaissements",   <span key="td" className="font-semibold" style={{ color: "#f87171" }}>{fmt(latest?.total_decaissements)}</span>],
          ["Variation tréso",       <span key="v"  className="font-bold" style={{ color: (latest?.variation_tresorerie ?? 0) >= 0 ? "#34d399" : "#f87171" }}>{fmt(latest?.variation_tresorerie)}</span>],
          ["Tréso début",           <span key="db" style={{ color: "#94a3b8" }}>{fmt(latest?.tresorerie_debut)}</span>],
          ["Tréso fin",             <span key="fin" className="font-bold" style={{ color: "#60a5fa" }}>{fmt(latest?.tresorerie_fin)}</span>],
        ]}
      />
    </div>
  );
}

function TabTvaPret({ xlsx }: { xlsx?: ParsedData["xlsx"] }) {
  if (!xlsx) return <Empty>Données Excel non disponibles</Empty>;

  return (
    <div className="space-y-4">
      {xlsx.tva?.length ? (
        <>
          <p className="text-[10px] uppercase tracking-wider font-semibold" style={{ color: "#4d7ab5" }}>TVA</p>
          <InspectorTable
            headers={["Mois", "Collectée", "Déd. ST", "Déd. FG", "Due"]}
            rows={xlsx.tva.slice(-6).map((t) => [
              <span key="m" style={{ color: "#60a5fa" }}>{t.mois?.slice(0, 7)}</span>,
              fmt(t.tva_collectee),
              fmt(t.tva_deductible_st),
              fmt(t.tva_deductible_fg),
              <span key="d" className="font-semibold" style={{ color: "#fb923c" }}>{fmt(t.tva_due)}</span>,
            ])}
          />
        </>
      ) : null}

      {xlsx.pret && (
        <>
          <p className="text-[10px] uppercase tracking-wider font-semibold mt-2" style={{ color: "#4d7ab5" }}>
            {xlsx.pret.nom}
          </p>
          <div className="grid grid-cols-2 gap-2">
            <Kpi label="Capital initial"   value={fmt(xlsx.pret.montant_initial)}          color="#94a3b8" />
            <Kpi label="Mensualité"         value={fmt(xlsx.pret.mensualite_totale)}         color="#60a5fa" />
            <Kpi label="Remboursé à date"  value={fmt(xlsx.pret.rembourse_a_date)}          color="#34d399" />
            <Kpi label="Reste à payer"     value={fmt(xlsx.pret.reste_a_rembourser)}        color="#fb923c" />
          </div>
          <p className="text-[11px]" style={{ color: "#475569" }}>
            Dernière échéance : <span style={{ color: "#60a5fa" }}>{xlsx.pret.derniere_echeance}</span>
          </p>
        </>
      )}
    </div>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-center h-32 text-sm" style={{ color: "#334155" }}>
      {children}
    </div>
  );
}
