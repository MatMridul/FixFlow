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
    <header className="sticky top-0 z-40 w-full bg-black/90 backdrop-blur-md border-b border-white/[0.08] px-4 sm:px-8 py-3 transition-colors">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Clickable Logo (Rule 13) */}
        <button
          onClick={onReset}
          className="flex items-center gap-2.5 text-left group focus:outline-none focus-visible:ring-1 focus-visible:ring-white rounded-lg p-1 -m-1 cursor-pointer"
          aria-label="FixFlow Home - Reset Diagnostic Console"
        >
          <div className="w-8 h-8 rounded bg-white text-black font-bold text-xs flex items-center justify-center tracking-tight shadow-sm group-hover:bg-neutral-200 transition-colors">
            FF
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-semibold text-sm tracking-tight text-white group-hover:text-neutral-300 transition-colors">
                FixFlow
              </span>
              <span className="text-[11px] text-neutral-600 font-normal">/</span>
              <span className="text-xs text-neutral-300 font-medium">Galaxy Care</span>
            </div>
            <p className="text-[10px] text-neutral-400 tracking-normal hidden sm:block">
              One UI 6.1 Diagnostic &amp; Resolution Engine
            </p>
          </div>
        </button>

        {/* Consumer Device & Care Status Badges */}
        <div className="hidden md:flex items-center gap-2">
          <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-[#0D0D0D] border border-white/[0.08] text-xs text-neutral-300 font-medium">
            <Smartphone className="w-3.5 h-3.5 text-neutral-400" />
            <span className="text-white">Galaxy S24 Ultra</span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#0D0D0D] border border-white/[0.08] text-xs text-neutral-300">
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                serverOnline ? "bg-white shadow-[0_0_8px_rgba(255,255,255,0.8)]" : "bg-neutral-500"
              }`}
            />
            <span className="font-medium text-white">
              {serverOnline ? "Device Connected" : "Connecting..."}
            </span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#0D0D0D] border border-white/[0.08] text-xs text-neutral-400">
            <ShieldCheck className="w-3.5 h-3.5 text-neutral-400" />
            <span>Official Guide</span>
          </div>

          <button
            onClick={onReset}
            className="flex items-center gap-1 px-2.5 py-1 rounded text-neutral-400 hover:text-white hover:bg-white/[0.06] transition-colors text-xs cursor-pointer"
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
            className="flex items-center gap-1.5 px-3 py-1.5 min-h-[38px] rounded bg-white text-black text-xs font-semibold hover:bg-neutral-200 active:scale-95 transition-all cursor-pointer"
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
