import React from "react";
import { Smartphone, ShieldCheck, RefreshCw } from "lucide-react";

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
    <header className="sticky top-0 z-40 w-full bg-[#0E1013]/90 backdrop-blur-md border-b border-white/[0.07] px-4 sm:px-8 py-3 transition-colors">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Clickable Logo (Rule 13) */}
        <button
          onClick={onReset}
          className="flex items-center gap-2.5 text-left group focus:outline-none focus-visible:ring-2 focus-visible:ring-[#1E56FF] rounded-lg p-1 -m-1"
          aria-label="FixFlow Home - Reset Diagnostic Console"
        >
          <div className="w-8 h-8 rounded-lg bg-[#1E56FF] flex items-center justify-center text-white font-semibold text-xs tracking-tight shadow-sm group-hover:bg-[#2F68FD] transition-colors">
            FF
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-semibold text-sm tracking-tight text-white group-hover:text-blue-100 transition-colors">
                FixFlow
              </span>
              <span className="text-[11px] text-zinc-500 font-normal">/</span>
              <span className="text-xs text-zinc-300 font-medium">Galaxy Care</span>
            </div>
            <p className="text-[10px] text-zinc-400 tracking-normal hidden sm:block">
              One UI 6.1 Intelligent Troubleshooting
            </p>
          </div>
        </button>

        {/* Consumer Device & Care Status Badges */}
        <div className="hidden md:flex items-center gap-2.5">
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-md bg-[#13151A] border border-white/[0.07] text-xs text-zinc-300 font-medium">
            <Smartphone className="w-3.5 h-3.5 text-zinc-400" />
            <span>Galaxy S24 Ultra</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#13151A] border border-white/[0.07] text-xs text-zinc-300">
            <span
              className={`w-2 h-2 rounded-full ${
                serverOnline ? "bg-emerald-400" : "bg-amber-400"
              }`}
            />
            <span className="font-medium text-zinc-300">
              {serverOnline ? "Device Connected" : "Connecting..."}
            </span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#13151A] border border-white/[0.07] text-xs text-zinc-400">
            <ShieldCheck className="w-3.5 h-3.5 text-zinc-400" />
            <span>Official Guide</span>
          </div>

          <button
            onClick={onReset}
            className="flex items-center gap-1 px-2 py-1 rounded-md text-zinc-400 hover:text-white hover:bg-white/[0.05] transition-colors text-xs"
            title="Reset Console"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Reset</span>
          </button>
        </div>

        {/* Mobile Drawer Toggle (Rule 5) */}
        <div className="flex items-center gap-2 lg:hidden">
          <button
            onClick={onToggleMobileSim}
            className="flex items-center gap-1.5 px-3 py-1.5 min-h-[38px] rounded-lg bg-[#1E56FF] hover:bg-[#2F68FD] text-white text-xs font-medium active:scale-95 transition-all"
            aria-label="Toggle Samsung Galaxy Simulator"
          >
            <Smartphone className="w-3.5 h-3.5" />
            <span>{isMobileSimOpen ? "Hide Phone" : "Show Phone"}</span>
          </button>
        </div>

      </div>
    </header>
  );
};
