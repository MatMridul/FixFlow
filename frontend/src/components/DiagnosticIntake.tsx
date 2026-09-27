import React from "react";
import { motion } from "framer-motion";
import { Search, ChevronRight } from "lucide-react";
import { BENCHMARK_SCENARIOS } from "../services/api";
import type { MetaPayload } from "../types/engine";
import { springs, microInteractions } from "../theme/motion";

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
    <motion.section
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={springs.snappy}
      className="w-full bg-[#080808] border border-white/[0.08] rounded-xl p-5 sm:p-6 space-y-4"
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
        <div>
          <h2 className="text-sm font-semibold text-white tracking-tight">
            Galaxy Device Diagnostics
          </h2>
          <p className="text-xs text-neutral-400 mt-0.5">
            Identify issues and generate verified step-by-step solutions for your device.
          </p>
        </div>
        <div className="text-[11px] font-mono text-neutral-300 bg-[#121212] px-2.5 py-1 rounded border border-white/[0.08]">
          One UI 6.1
        </div>
      </div>

      {/* Search Input Bar (Rule 6: Zero placeholder text) */}
      <div className="space-y-1.5">
        <label htmlFor="diagnostic-search" className="text-xs font-medium text-neutral-300 block">
          Describe what's happening with your Galaxy device:
        </label>
        <div className="relative flex items-center">
          <div className="absolute left-3.5 text-neutral-500 pointer-events-none">
            <Search className="w-4 h-4" />
          </div>
          <input
            id="diagnostic-search"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            className="w-full pl-10 pr-24 py-2.5 rounded bg-black border border-white/[0.12] focus:border-white focus:outline-none focus:ring-1 focus:ring-white text-white text-xs sm:text-sm font-normal transition-colors"
          />
          <motion.button
            whileHover={microInteractions.hoverButton}
            whileTap={microInteractions.tap}
            onClick={() => onSubmit(query.trim())}
            disabled={isLoading || !query.trim()}
            className="absolute right-1.5 px-3.5 py-1.5 rounded bg-white hover:bg-neutral-200 text-black text-xs font-semibold disabled:opacity-30 disabled:pointer-events-none transition-colors flex items-center gap-1 cursor-pointer"
          >
            {isLoading ? (
              <span className="animate-spin text-xs">⟳</span>
            ) : (
              <>
                <span>Diagnose</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </>
            )}
          </motion.button>
        </div>
      </div>

      {/* Common Galaxy Issues & Quick Guides */}
      <div className="space-y-2 pt-1">
        <span className="text-[11px] font-medium text-neutral-400 uppercase tracking-wider block">
          Common Galaxy Issues &amp; Quick Guides
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {BENCHMARK_SCENARIOS.map((scenario) => {
            const isSelected = query.trim().toLowerCase() === scenario.query.trim().toLowerCase();
            return (
              <motion.button
                key={scenario.id}
                whileHover={{ y: -1, transition: { duration: 0.12 } }}
                whileTap={{ scale: 0.98 }}
                onClick={() => {
                  setQuery(scenario.query);
                  onSubmit(scenario.query, scenario.siis_title, scenario.siis_content);
                }}
                disabled={isLoading}
                className={`relative p-2.5 rounded border text-left transition-all flex items-center justify-between gap-2 group cursor-pointer ${
                  isSelected
                    ? "bg-[#181818] border-white text-white shadow-sm ring-1 ring-white/20"
                    : "bg-[#0D0D0D] border-white/[0.06] hover:bg-[#141414] hover:border-white/[0.15] text-neutral-300"
                }`}
              >
                <div className="min-w-0">
                  <span className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider block">
                    {scenario.tag}
                  </span>
                  <span className="text-xs font-medium text-neutral-200 group-hover:text-white truncate block">
                    {scenario.label}
                  </span>
                </div>
                <ChevronRight className="w-3.5 h-3.5 text-neutral-500 group-hover:text-white shrink-0 transition-colors" />
              </motion.button>
            );
          })}
        </div>
      </div>
    </motion.section>
  );
};
