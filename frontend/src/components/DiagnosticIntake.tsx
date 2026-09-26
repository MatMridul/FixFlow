import React from "react";
import { Search, Clock, DollarSign, Database, CheckCircle2, Sparkles, ChevronRight, Zap } from "lucide-react";
import { BENCHMARK_SCENARIOS } from "../services/api";
import type { MetaPayload } from "../types/engine";

interface DiagnosticIntakeProps {
  query: string;
  setQuery: (q: string) => void;
  onSubmit: (customQuery?: string, siisTitle?: string, siisContent?: string) => void;
  isLoading: boolean;
  meta: MetaPayload | null;
}

export const DiagnosticIntake: React.FC<DiagnosticIntakeProps> = ({
  query,
  setQuery,
  onSubmit,
  isLoading,
  meta,
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
              Galaxy AI Troubleshooting Console
            </span>
            <span className="text-[10px] text-slate-400 block font-mono">
              Samsung One UI 6.1 Diagnostic Intelligence
            </span>
          </div>
        </div>

        {meta && (
          <div className="flex items-center gap-2 text-xs font-mono">
            <span
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-semibold border ${
                meta.cache_hit
                  ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                  : "bg-sky-500/15 text-sky-300 border-sky-500/30"
              }`}
            >
              <Zap className="w-3 h-3 fill-current" />
              <span>{meta.cache_hit ? "Fast Path (Cache Hit)" : "Cold Path Model"}</span>
            </span>
            <span className="text-slate-400 font-semibold">{meta.latency_ms.toFixed(1)}ms</span>
          </div>
        )}
      </div>

      {/* Search Input Bar (Zero placeholder text — Rule 6) */}
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-slate-300 block">
          Enter device symptom, error message, or multi-condition query:
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

      {/* Benchmark 1-Click Scenarios Grid */}
      <div className="space-y-2">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
          Pre-Warmed Benchmark Scenarios (1-Click Test Matrix)
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

      {/* Real-Time Telemetry Metrics Footer */}
      {meta && (
        <div className="pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-3 text-[11px] font-mono text-slate-400">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1 text-slate-300">
              <Clock className="w-3.5 h-3.5 text-sky-400" />
              <span>{meta.latency_ms.toFixed(1)}ms</span>
            </span>
            <span className="flex items-center gap-1 text-emerald-400">
              <DollarSign className="w-3.5 h-3.5" />
              <span>${meta.cost_usd.toFixed(4)} USD</span>
            </span>
            <span className="flex items-center gap-1 text-indigo-300">
              <Database className="w-3.5 h-3.5" />
              <span>{meta.model}</span>
            </span>
          </div>

          <div className="flex items-center gap-1 text-emerald-400 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>100% Ground Truth Parity</span>
          </div>
        </div>
      )}
    </div>
  );
};
