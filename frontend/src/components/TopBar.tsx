import React from "react";
import { Smartphone, Zap, Sparkles, ShieldCheck } from "lucide-react";

interface TopBarProps {
  serverOnline: boolean;
  onReset: () => void;
  onToggleMobileSim: () => void;
  isMobileSimOpen: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({
  serverOnline,
  onReset,
  onToggleMobileSim,
  isMobileSimOpen,
}) => {
  return (
    <header className="sticky top-0 z-40 w-full glass-panel border-b border-white/5 px-4 sm:px-8 py-3 transition-colors">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Rule 13: Clickable Logo */}
        <button
          onClick={onReset}
          className="flex items-center gap-2.5 text-left group focus:outline-none focus-visible:ring-2 focus-visible:ring-samsung-blue rounded-lg p-1 -m-1"
          aria-label="FixFlow Home - Reset Diagnostic Console"
        >
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-samsung-blue to-blue-400 flex items-center justify-center shadow-blue-glow group-hover:scale-105 transition-transform duration-200">
            <Zap className="w-4 h-4 text-white fill-white" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-lg tracking-tight text-white group-hover:text-blue-200 transition-colors">
                FixFlow
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-samsung-blue"></span>
            </div>
            <p className="text-[10px] text-slate-400 font-medium tracking-wider uppercase hidden sm:block">
              One UI Troubleshooting Engine
            </p>
          </div>
        </button>

        {/* Desktop Engine Badges */}
        <div className="hidden md:flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-white/10 text-xs text-slate-300">
            <span className={`w-2 h-2 rounded-full ${serverOnline ? "bg-emerald-400 shadow-[0_0_8px_#34d399]" : "bg-amber-400 shadow-[0_0_8px_#fbbf24]"}`}></span>
            <span className="font-medium">
              {serverOnline ? "Engine Online (FastAPI:8000)" : "Deterministic Engine (Offline Mode)"}
            </span>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-blue-950/40 border border-blue-500/20 text-xs text-blue-300">
            <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
            <span className="font-medium">Theme 02 Certified</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-full bg-slate-800/60 border border-white/5 text-[11px] text-slate-400">
            <Sparkles className="w-3 h-3 text-amber-300" />
            <span>AI-Ready</span>
          </div>
        </div>

        {/* Rule 5: Mobile Drawer Toggle */}
        <div className="flex items-center gap-2 lg:hidden">
          <button
            onClick={onToggleMobileSim}
            className="flex items-center gap-2 px-3.5 py-2 min-h-[44px] rounded-xl bg-samsung-blue/15 hover:bg-samsung-blue/25 border border-samsung-blue/30 text-samsung-blue text-xs font-semibold active:scale-95 transition-all"
            aria-label="Toggle Samsung Galaxy Simulator"
          >
            <Smartphone className="w-4 h-4" />
            <span>{isMobileSimOpen ? "Hide Phone" : "Show Phone"}</span>
          </button>
        </div>

      </div>
    </header>
  );
};
