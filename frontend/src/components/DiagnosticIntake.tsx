import React from "react";
import { Search, Sparkles, ChevronRight } from "lucide-react";
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
    <div className="w-full relative overflow-hidden rounded-3xl p-5 sm:p-7 border border-slate-800/80 bg-slate-900/60 backdrop-blur-2xl shadow-2xl space-y-5">
      {/* Specular Ambient Glow */}
      <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-br from-sky-500/10 via-blue-600/5 to-transparent rounded-full blur-3xl pointer-events-none" />

      {/* Header with Galaxy AI Badge */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/70 pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-sky-500/15 border border-sky-400/30 text-sky-400">
            <Sparkles className="w-4 h-4 fill-sky-400/20" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-100 tracking-wide">
              Galaxy AI Troubleshooting Assistant
            </span>
            <span className="text-[10px] text-slate-400 block font-medium">
              Samsung One UI 6.1 Diagnostic Care
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/20 text-xs text-sky-300 font-medium">
          <Sparkles className="w-3.5 h-3.5 text-sky-400" />
          <span>Smart Assistant Ready</span>
        </div>
      </div>

      {/* Search Input Bar (Zero placeholder text — Rule 6) */}
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-slate-300 block">
          Describe what's happening with your Galaxy device:
        </label>
        <div className="relative flex items-center">
          <div className="absolute left-4 text-sky-400 pointer-events-none">
            <Search className="w-4 h-4" />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            className="w-full pl-11 pr-28 py-3.5 rounded-2xl bg-slate-950/80 border border-slate-700/80 focus:border-sky-400 focus:ring-2 focus:ring-sky-500/20 text-white text-xs sm:text-sm font-medium transition-all shadow-inner"
          />
          <button
            onClick={() => onSubmit(query.trim())}
            disabled={isLoading || !query.trim()}
            className="absolute right-2 px-4 py-2 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white text-xs font-semibold shadow-md shadow-sky-500/25 active:scale-95 disabled:opacity-50 disabled:pointer-events-none transition-all flex items-center gap-1.5"
          >
            {isLoading ? (
              <span className="animate-spin">⟳</span>
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
      <div className="space-y-2">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
          Common Galaxy Issues &amp; Quick Guides
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
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
                className={`p-3 rounded-2xl border text-left transition-all flex items-start justify-between gap-2.5 group ${
                  isSelected
                    ? "bg-sky-500/15 border-sky-400/50 ring-1 ring-sky-400/30 text-white"
                    : "bg-slate-950/50 border-slate-800/80 hover:bg-slate-800/40 hover:border-slate-700 text-slate-300"
                }`}
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 mb-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-sky-400 group-hover:scale-125 transition-transform" />
                    <span className="text-[10px] font-mono text-sky-300 font-bold uppercase truncate">
                      {scenario.tag}
                    </span>
                  </div>
                  <span className="text-xs font-semibold block text-slate-200 group-hover:text-white leading-snug">
                    {scenario.label}
                  </span>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-sky-400 shrink-0 mt-2 transition-colors" />
              </button>
            );
          })}
        </div>
      </div>

      {/* Official Samsung Support Guarantee Footer */}
      <div className="pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400">
        <div className="flex items-center gap-1.5 text-slate-300">
          <Sparkles className="w-3.5 h-3.5 text-sky-400" />
          <span>Official Samsung One UI 6.1 Diagnostic Solutions</span>
        </div>
        <span className="text-[11px] text-slate-500 font-medium">Samsung Electronics · Care+</span>
      </div>
    </div>
  );
};
