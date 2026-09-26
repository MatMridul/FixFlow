import React from "react";
import { Smartphone, Zap, Sparkles } from "lucide-react";

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
              Samsung Smart Care · Galaxy AI
            </p>
          </div>
        </button>

        {/* Consumer Device & Care Status Badges */}
        <div className="hidden md:flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-white/10 text-xs text-slate-300">
            <Smartphone className="w-3.5 h-3.5 text-sky-400" />
            <span className="font-medium">Galaxy S24 Ultra</span>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-950/40 border border-emerald-500/20 text-xs text-emerald-300">
            <span className={`w-2 h-2 rounded-full ${serverOnline ? "bg-emerald-400 shadow-[0_0_8px_#34d399]" : "bg-amber-400 shadow-[0_0_8px_#fbbf24]"}`}></span>
            <span className="font-medium">
              {serverOnline ? "Device Connected" : "Device Offline"}
            </span>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-sky-500/10 border border-sky-500/20 text-xs text-sky-300">
            <Sparkles className="w-3.5 h-3.5 text-sky-400" />
            <span className="font-medium">Galaxy AI Support</span>
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
