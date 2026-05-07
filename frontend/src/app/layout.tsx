import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Rapprochement Bancaire — ECO Steering",
  description: "Assistant IA de rapprochement bancaire automatisé",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" className="dark">
      <body className="bg-slate-925 text-slate-100 h-screen overflow-hidden">
        {children}
      </body>
    </html>
  );
}
