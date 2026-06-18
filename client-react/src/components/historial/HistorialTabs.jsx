import React from 'react';
import { cn } from "@/lib/utils";

export default function HistorialTabs({ activeTab, setActiveTab, counts }) {
  const tabs = [
    { id: "actas", label: "Actas Generadas", count: counts.actas },
    { id: "atencion", label: "Requieren Atención", count: counts.atencion },
    { id: "borradores", label: "Borradores", count: counts.borradores },
  ];

  return (
    <div className="flex border-b border-border mb-6">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => setActiveTab(tab.id)}
          className={cn(
            "pb-4 px-4 text-sm font-medium transition-all relative",
            activeTab === tab.id ? "text-primary" : "text-muted-foreground hover:text-foreground"
          )}
        >
          {tab.label} ({tab.count})
          {activeTab === tab.id && (
            <div className="absolute bottom-0 left-0 w-full h-0.5 bg-gradient-to-r from-primary to-primary-container" />
          )}
        </button>
      ))}
    </div>
  );
}
