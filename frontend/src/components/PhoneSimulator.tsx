import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Wifi, Battery, Sun, Moon, Zap, ArrowLeft, Sliders } from "lucide-react";
import type { SimulatedDeviceState } from "../types/engine";
import { MOTION_TOKENS } from "../theme/motion";

interface PhoneSimulatorProps {
  deviceState: SimulatedDeviceState;
  setDeviceState: React.Dispatch<React.SetStateAction<SimulatedDeviceState>>;
  onCloseMobile?: () => void;
}

export const PhoneSimulator: React.FC<PhoneSimulatorProps> = ({
  deviceState,
  setDeviceState,
  onCloseMobile,
}) => {
  const toggleAdaptiveBrightness = () => {
    setDeviceState((prev) => ({
      ...prev,
      adaptiveBrightness: !prev.adaptiveBrightness,
    }));
  };

  const toggleDarkMode = () => {
    setDeviceState((prev) => ({
      ...prev,
      darkMode: !prev.darkMode,
    }));
  };

  const togglePowerSaving = () => {
    setDeviceState((prev) => ({
      ...prev,
      powerSaving: !prev.powerSaving,
    }));
  };

  const navigateTo = (screen: SimulatedDeviceState["screen"]) => {
    setDeviceState((prev) => ({ ...prev, screen }));
  };

  return (
    <div className="w-full flex flex-col items-center">
      {/* Mobile Drawer Header */}
      {onCloseMobile && (
        <div className="w-full flex items-center justify-between pb-3 lg:hidden">
          <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Simulated Galaxy S24 (One UI)
          </span>
          <button
            onClick={onCloseMobile}
            className="px-3 py-1.5 rounded-lg bg-slate-800 text-xs text-white"
          >
            Close
          </button>
        </div>
      )}

      {/* Galaxy Device Outer Frame */}
      <div className="relative w-full max-w-[310px] h-[580px] bg-slate-950 rounded-[44px] p-3 border-[6px] border-slate-800 shadow-2xl shadow-black flex flex-col overflow-hidden">
        
        {/* Hardware Bezel & Punch Hole Camera */}
        <div className="absolute top-4 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-black z-30 flex items-center justify-center">
          <div className="w-1.5 h-1.5 rounded-full bg-slate-900 border border-slate-700/50" />
        </div>

        {/* Screen Display Area */}
        <div className={`relative w-full h-full rounded-[34px] overflow-hidden flex flex-col transition-colors duration-300 ${
          deviceState.darkMode ? "bg-black text-white" : "bg-slate-900 text-white"
        }`}>

          {/* Status Bar */}
          <div className="w-full px-6 pt-2 pb-1 flex items-center justify-between text-[11px] font-semibold select-none z-20">
            <span>12:45</span>
            <div className="flex items-center gap-1.5">
              <Wifi className="w-3 h-3 text-white" />
              <span className="text-[10px] font-mono">5G</span>
              <Battery className="w-3.5 h-3.5 text-white" />
            </div>
          </div>

          {/* Dynamic Content Screen Router */}
          <div className="flex-1 overflow-y-auto px-4 py-2 relative">
            <AnimatePresence mode="wait">

              {/* 1. HOME SCREEN */}
              {deviceState.screen === "home" && (
                <motion.div
                  key="home"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  transition={MOTION_TOKENS.springSnappy}
                  className="h-full flex flex-col justify-between py-6 text-center"
                >
                  <div className="space-y-1">
                    <span className="text-4xl font-light tracking-tight block">12:45</span>
                    <span className="text-xs text-slate-400 block">Mon, September 26</span>
                  </div>

                  <div className="space-y-3">
                    <button
                      onClick={() => navigateTo("settings")}
                      className="w-full py-3 px-4 rounded-2xl bg-white/10 hover:bg-white/20 active:scale-95 transition-all text-xs font-semibold flex items-center justify-center gap-2"
                    >
                      <Sliders className="w-4 h-4 text-samsung-blue" />
                      <span>Open Settings</span>
                    </button>
                    <p className="text-[10px] text-slate-400">
                      Tap above or click a card deeplink to navigate
                    </p>
                  </div>
                </motion.div>
              )}

              {/* 2. SETTINGS ROOT MENU */}
              {deviceState.screen === "settings" && (
                <motion.div
                  key="settings"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={MOTION_TOKENS.springSnappy}
                  className="space-y-3 pt-2"
                >
                  <div className="flex items-center gap-2 mb-3">
                    <button onClick={() => navigateTo("home")} className="p-1 rounded-full hover:bg-white/10">
                      <ArrowLeft className="w-4 h-4" />
                    </button>
                    <span className="font-bold text-base">Settings</span>
                  </div>

                  <div className="space-y-1.5 text-xs">
                    <button
                      onClick={() => navigateTo("display")}
                      className="w-full p-3 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-between text-left transition-colors"
                    >
                      <div className="flex items-center gap-2.5">
                        <Sun className="w-4 h-4 text-amber-400" />
                        <div>
                          <span className="font-medium block">Display</span>
                          <span className="text-[10px] text-slate-400">Brightness, Eye comfort, Dark mode</span>
                        </div>
                      </div>
                      <span className="text-slate-500">›</span>
                    </button>

                    <button
                      onClick={() => navigateTo("battery")}
                      className="w-full p-3 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-between text-left transition-colors"
                    >
                      <div className="flex items-center gap-2.5">
                        <Zap className="w-4 h-4 text-emerald-400" />
                        <div>
                          <span className="font-medium block">Battery</span>
                          <span className="text-[10px] text-slate-400">Power saving, Background limits</span>
                        </div>
                      </div>
                      <span className="text-slate-500">›</span>
                    </button>
                  </div>
                </motion.div>
              )}

              {/* 3. DISPLAY SUB-SCREEN */}
              {deviceState.screen === "display" && (
                <motion.div
                  key="display"
                  initial={{ opacity: 0, x: 30 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -30 }}
                  transition={MOTION_TOKENS.springSnappy}
                  className="space-y-4 pt-1"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <button onClick={() => navigateTo("settings")} className="p-1 rounded-full hover:bg-white/10">
                      <ArrowLeft className="w-4 h-4" />
                    </button>
                    <span className="font-bold text-sm">Display Settings</span>
                  </div>

                  {/* Brightness Section */}
                  <div className="p-3 rounded-2xl bg-white/5 space-y-3 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Adaptive Brightness</span>
                      <button
                        onClick={toggleAdaptiveBrightness}
                        className={`w-11 h-6 rounded-full transition-colors relative flex items-center px-0.5 ${
                          deviceState.adaptiveBrightness ? "bg-samsung-blue" : "bg-slate-700"
                        }`}
                      >
                        <div className={`w-5 h-5 rounded-full bg-white transition-transform ${
                          deviceState.adaptiveBrightness ? "translate-x-5" : "translate-x-0"
                        }`} />
                      </button>
                    </div>

                    <div className="space-y-1">
                      <span className="text-[10px] text-slate-400 block">Brightness Slider</span>
                      <input
                        type="range"
                        defaultValue={65}
                        className="w-full accent-samsung-blue"
                      />
                    </div>
                  </div>

                  {/* Dark Mode Toggle */}
                  <div className="p-3 rounded-2xl bg-white/5 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <Moon className="w-4 h-4 text-blue-300" />
                      <span className="font-medium">Dark Mode</span>
                    </div>
                    <button
                      onClick={toggleDarkMode}
                      className={`w-11 h-6 rounded-full transition-colors relative flex items-center px-0.5 ${
                        deviceState.darkMode ? "bg-samsung-blue" : "bg-slate-700"
                      }`}
                    >
                      <div className={`w-5 h-5 rounded-full bg-white transition-transform ${
                        deviceState.darkMode ? "translate-x-5" : "translate-x-0"
                      }`} />
                    </button>
                  </div>
                </motion.div>
              )}

              {/* 4. BATTERY SUB-SCREEN */}
              {deviceState.screen === "battery" && (
                <motion.div
                  key="battery"
                  initial={{ opacity: 0, x: 30 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -30 }}
                  transition={MOTION_TOKENS.springSnappy}
                  className="space-y-4 pt-1"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <button onClick={() => navigateTo("settings")} className="p-1 rounded-full hover:bg-white/10">
                      <ArrowLeft className="w-4 h-4" />
                    </button>
                    <span className="font-bold text-sm">Battery Settings</span>
                  </div>

                  <div className="p-3 rounded-2xl bg-white/5 space-y-3 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">Power Saving Mode</span>
                      <button
                        onClick={togglePowerSaving}
                        className={`w-11 h-6 rounded-full transition-colors relative flex items-center px-0.5 ${
                          deviceState.powerSaving ? "bg-samsung-blue" : "bg-slate-700"
                        }`}
                      >
                        <div className={`w-5 h-5 rounded-full bg-white transition-transform ${
                          deviceState.powerSaving ? "translate-x-5" : "translate-x-0"
                        }`} />
                      </button>
                    </div>
                    <p className="text-[10px] text-slate-400">
                      Limits background network usage, syncing, and reduces brightness.
                    </p>
                  </div>
                </motion.div>
              )}

            </AnimatePresence>
          </div>

          {/* Interactive Hardware State Controls Banner */}
          <div className="p-2.5 bg-slate-950/80 border-t border-white/10 text-center">
            <span className="text-[10px] text-slate-400 block font-mono">
              Live Mock Hardware State
            </span>
          </div>

        </div>
      </div>
    </div>
  );
};
