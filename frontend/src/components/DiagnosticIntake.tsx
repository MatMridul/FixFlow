import React from "react";
import { Search, ChevronRight } from "lucide-react";
import { BENCHMARK_SCENARIOS } from "../services/api";
import type { MetaPayload } from "../types/engine";

interface DiagnosticIntakeProps {
  query: string;
  setQuery: (q: string) => void;
  onSubmit: (customQuery?: string, siisTitle?: string, siisContent?: string) => void;
  isLoading: boolean;
  meta?: MetaPayload | null;
}

export const DiagnosticIntake: React.FC<DiagnosticIntakeProps> = ({
  query,
  setQuery,
  onSubmit,
  isLoading,
}) => {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && query.trim() && !isLoading) {
      onSubmit(query.trim());
    }
  };

  return (
    <section className="w-full bg-[#13151A] border border-white/[0.07] rounded-xl p-5 sm:p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/[0.05] pb-3">
        <div>
          <h2 className="text-sm font-semibold text-white tracking-tight">
            Galaxy Device Diagnostics
          </h2>
          <p className="text-xs text-zinc-400 mt-0.5">
            Identify issues and generate verified step-by-step solutions for your device.
          </p>
        </div>
        <div className="text-[11px] font-mono text-zinc-400 bg-[#191C23] px-2.5 py-1 rounded border border-white/[0.06]">
          One UI 6.1
        </div>
      </div>

      {/* Search Input Bar (Rule 6: Zero placeholder text) */}
      <div className="space-y-1.5">
        <label htmlFor="diagnostic-search" className="text-xs font-medium text-zinc-300 block">
          Describe what's happening with your Galaxy device:
        </label>
        <div className="relative flex items-center">
          <div className="absolute left-3.5 text-zinc-500 pointer-events-none">
            <Search className="w-4 h-4" />
          </div>
          <input
            id="diagnostic-search"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            className="w-full pl-10 pr-24 py-2.5 rounded-lg bg-[#0E1013] border border-white/[0.1] focus:border-[#1E56FF] focus:outline-none focus:ring-1 focus:ring-[#1E56FF] text-white text-xs sm:text-sm font-normal transition-colors"
          />
          <button
            onClick={() => onSubmit(query.trim())}
            disabled={isLoading || !query.trim()}
            className="absolute right-1.5 px-3.5 py-1.5 rounded-md bg-[#1E56FF] hover:bg-[#2F68FD] text-white text-xs font-medium active:scale-95 disabled:opacity-40 disabled:pointer-events-none transition-all flex items-center gap-1"
          >
            {isLoading ? (
              <span className="animate-spin text-xs">⟳</span>
            ) : (
              <>
                <span>Diagnose</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
      </div>

      {/* Common Galaxy Issues & Quick Guides */}
      <div className="space-y-2 pt-1">
        <span className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider block">
          Common Galaxy Issues &amp; Quick Guides
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {BENCHMARK_SCENARIOS.map((scenario) => {
            const isSelected = query.trim().toLowerCase() === scenario.query.trim().toLowerCase();
            return (
              <button
                key={scenario.id}
                onClick={() => {
                  setQuery(scenario.query);
                  onSubmit(scenario.query, scenario.siis_title, scenario.siis_content);
                }}
                disabled={isLoading}
                className={`p-2.5 rounded-lg border text-left transition-all flex items-center justify-between gap-2 group ${
                  isSelected
                    ? "bg-[#1E56FF]/10 border-[#1E56FF]/40 text-white"
                    : "bg-[#191C23] border-white/[0.05] hover:bg-[#20242D] hover:border-white/[0.1] text-zinc-300"
                }`}
              >
                <div className="min-w-0">
                  <span className="text-[10px] font-mono text-zinc-400 uppercase tracking-wider block">
                    {scenario.tag}
                  </span>
                  <span className="text-xs font-medium text-zinc-200 group-hover:text-white truncate block">
                    {scenario.label}
                  </span>
                </div>
                <ChevronRight className="w-3.5 h-3.5 text-zinc-500 group-hover:text-zinc-300 shrink-0 transition-colors" />
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
};
