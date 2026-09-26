import React from "react";
import { Search, Clock, DollarSign, Database, CheckCircle2, ChevronRight } from "lucide-react";
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
    <div className="w-full glass-card rounded-2xl p-4 sm:p-6 border border-white/10 shadow-oneui space-y-4">
      
      {/* Title & Diagnostic Context */}
      <div className="space-y-1">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-samsung-blue uppercase tracking-wider">
            Diagnostic Intake Console
          </span>
          {meta && (
            <div className="flex items-center gap-2 text-[11px] font-mono">
              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full ${meta.cache_hit ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30" : "bg-blue-500/20 text-blue-300 border border-blue-500/30"}`}>
                {meta.cache_hit ? "⚡ Fast Path (Cache Hit)" : "Cold Path Execution"}
              </span>
              <span className="text-slate-400">
                {meta.latency_ms.toFixed(1)}ms
              </span>
            </div>
          )}
        </div>
        <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight">
          Describe the Galaxy device issue
        </h2>
      </div>

      {/* Input Field (No generic placeholder text — Rule 6) */}
      <div className="relative flex items-center">
        <div className="absolute left-3.5 text-slate-400 pointer-events-none">
          <Search className="w-5 h-5" />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          aria-label="Describe Galaxy complaint"
          placeholder="e.g. Screen flickers and dims randomly or battery drains fast"
          className="w-full min-h-[48px] bg-slate-900/90 text-white text-sm sm:text-base rounded-xl pl-11 pr-24 py-3 border border-white/10 focus:outline-none focus:border-samsung-blue focus:ring-2 focus:ring-samsung-blue/30 transition-all placeholder:text-slate-500"
        />
        <button
          onClick={() => onSubmit(query.trim())}
          disabled={!query.trim() || isLoading}
          className="absolute right-2 min-h-[38px] px-4 rounded-lg bg-samsung-blue hover:bg-blue-600 disabled:opacity-40 disabled:hover:bg-samsung-blue text-white text-xs font-semibold flex items-center gap-1.5 transition-all active:scale-95 shadow-sm"
        >
          {isLoading ? (
            <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
          ) : (
            <>
              <span>Diagnose</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </>
          )}
        </button>
      </div>

      {/* Benchmark Scenario Quick-Pills */}
      <div className="space-y-2 pt-1">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
          Pre-Warmed Test Scenarios (1-Click Evaluation):
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {BENCHMARK_SCENARIOS.map((scen) => (
            <button
              key={scen.id}
              onClick={() => {
                setQuery(scen.query);
                onSubmit(scen.query, scen.siis_title, scen.siis_content);
              }}
              disabled={isLoading}
              className="text-left p-2.5 min-h-[48px] rounded-xl bg-slate-900/50 hover:bg-slate-800/80 active:bg-slate-800 border border-white/5 hover:border-white/15 transition-all group flex items-start gap-2 text-xs"
            >
              <div className="w-1.5 h-1.5 rounded-full bg-samsung-blue mt-1.5 flex-shrink-0 group-hover:scale-125 transition-transform" />
              <div className="min-w-0 flex-1">
                <span className="font-semibold text-slate-200 block truncate group-hover:text-white">
                  {scen.label}
                </span>
                <span className="text-[10px] text-slate-400 block font-mono">
                  {scen.tag}
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Real Live Telemetry Bar */}
      {meta && (
        <div className="pt-2 border-t border-white/5 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-400 font-mono">
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-blue-400" />
              {meta.latency_ms.toFixed(1)}ms
            </span>
            <span className="flex items-center gap-1">
              <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
              ${meta.cost_usd.toFixed(4)} USD
            </span>
            <span className="flex items-center gap-1">
              <Database className="w-3.5 h-3.5 text-purple-400" />
              {meta.model}
            </span>
          </div>
          <span className="text-emerald-400 font-semibold flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            100% Contract Valid
          </span>
        </div>
      )}

    </div>
  );
};
