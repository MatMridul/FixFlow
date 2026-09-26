import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Wifi,
  Battery,
  BatteryCharging,
  Sun,
  Moon,
  Zap,
  ArrowLeft,
  Sliders,
  Check,
  Power,
  ChevronRight,
  RefreshCw,
  Trash2,
  Phone,
  MessageSquare,
  Camera,
  Image,
  Flame,
  Volume2,
  Search,
} from "lucide-react";
import type { SimulatedDeviceState, OneUIScreen } from "../types/engine";

interface PhoneSimulatorProps {
  deviceState: SimulatedDeviceState;
  setDeviceState: React.Dispatch<React.SetStateAction<SimulatedDeviceState>>;
  onCloseMobile?: () => void;
}

const screenTransition = { duration: 0.18, ease: [0.16, 1, 0.3, 1] as const };

export const PhoneSimulator: React.FC<PhoneSimulatorProps> = ({
  deviceState,
  setDeviceState,
  onCloseMobile,
}) => {
  const [volumeLevel, setVolumeLevel] = useState<number | null>(null);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [deviceCareScore, setDeviceCareScore] = useState(94);

  const navigateTo = (screen: OneUIScreen) => {
    setDeviceState((prev) => ({ ...prev, screen, quickPanelOpen: false }));
  };

  const toggleAdaptiveBrightness = () => {
    setDeviceState((prev) => ({
      ...prev,
      adaptiveBrightness: !prev.adaptiveBrightness,
    }));
  };

  const toggleDarkMode = (mode: boolean) => {
    setDeviceState((prev) => ({
      ...prev,
      darkMode: mode,
    }));
  };

  const togglePowerSaving = () => {
    setDeviceState((prev) => ({
      ...prev,
      powerSaving: !prev.powerSaving,
    }));
  };

  const toggleProtectBattery = () => {
    setDeviceState((prev) => ({
      ...prev,
      protectBattery: !prev.protectBattery,
    }));
  };

  const handleClearCache = () => {
    setDeviceState((prev) => ({
      ...prev,
      cacheSizeMb: 0,
      lastActionNotice: "184 MB Cache cleared & freed",
    }));
  };

  const handleOptimizeNow = () => {
    setIsOptimizing(true);
    setTimeout(() => {
      setIsOptimizing(false);
      setDeviceCareScore(100);
      setDeviceState((prev) => ({
        ...prev,
        cacheSizeMb: 0,
        lastActionNotice: "Device fully optimized (100%)",
      }));
    }, 1000);
  };

  const handleVolumeKey = (change: number) => {
    setVolumeLevel((prev) => {
      const current = prev ?? 65;
      return Math.min(100, Math.max(0, current + change));
    });
    setTimeout(() => setVolumeLevel(null), 1800);
  };

  const handlePowerButton = () => {
    setDeviceState((prev) => ({
      ...prev,
      isLocked: !prev.isLocked,
      quickPanelOpen: false,
    }));
  };

  const handleRebootSafeMode = () => {
    setDeviceState((prev) => ({
      ...prev,
      screen: "safe_mode",
      isSafeMode: true,
      quickPanelOpen: false,
    }));
    setTimeout(() => {
      setDeviceState((prev) => ({
        ...prev,
        screen: "home",
      }));
    }, 2000);
  };

  const toggleQuickPanel = () => {
    setDeviceState((prev) => ({
      ...prev,
      quickPanelOpen: !prev.quickPanelOpen,
    }));
  };

  const screenBrightnessFilter = `brightness(${0.45 + (deviceState.brightness / 100) * 0.65})`;

  return (
    <div className="w-full flex flex-col items-center select-none">
      {/* Mobile Drawer Header */}
      {onCloseMobile && (
        <div className="w-full flex items-center justify-between pb-3 lg:hidden">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span className="text-xs font-semibold text-zinc-200">
              Galaxy S24 Ultra (One UI 6.1)
            </span>
          </div>
          <button
            onClick={onCloseMobile}
            className="px-2.5 py-1 rounded-md bg-[#191C23] hover:bg-[#20242D] text-xs font-medium text-white transition-colors"
          >
            Close
          </button>
        </div>
      )}

      {/* Galaxy Device Outer Frame: Titanium Chassis */}
      <div className="relative w-full max-w-[310px] h-[590px] bg-[#16181D] rounded-[42px] p-2 border-[4px] border-[#2A2D35] shadow-[0_20px_50px_rgba(0,0,0,0.8)] flex flex-col overflow-hidden ring-1 ring-white/[0.08]">
        
        {/* Hardware Side Buttons */}
        <button
          onClick={() => handleVolumeKey(10)}
          className="absolute -left-[8px] top-28 w-1.5 h-10 bg-[#353942] rounded-l active:bg-[#1E56FF] transition-colors cursor-pointer"
          title="Volume Up"
          aria-label="Volume Up"
        />
        <button
          onClick={() => handleVolumeKey(-10)}
          className="absolute -left-[8px] top-40 w-1.5 h-10 bg-[#353942] rounded-l active:bg-[#1E56FF] transition-colors cursor-pointer"
          title="Volume Down"
          aria-label="Volume Down"
        />
        <button
          onClick={handlePowerButton}
          className="absolute -right-[8px] top-32 w-1.5 h-12 bg-[#353942] rounded-r active:bg-rose-500 transition-colors cursor-pointer"
          title="Power / Lock Screen"
          aria-label="Power Button"
        />

        {/* Punch Hole Infinity-O Camera */}
        <div className="absolute top-4 left-1/2 -translate-x-1/2 w-3.5 h-3.5 rounded-full bg-black z-40 flex items-center justify-center pointer-events-none">
          <div className="w-1.5 h-1.5 rounded-full bg-[#0E1117] border border-blue-900/40" />
        </div>

        {/* Volume Pill Overlay */}
        <AnimatePresence>
          {volumeLevel !== null && (
            <motion.div
              initial={{ opacity: 0, x: -16 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -16 }}
              className="absolute left-5 top-32 z-50 bg-[#13151A]/95 border border-white/10 rounded-xl p-2 backdrop-blur-md shadow-xl flex flex-col items-center gap-1.5"
            >
              <Volume2 className="w-3.5 h-3.5 text-[#1E56FF]" />
              <div className="w-1 h-14 bg-zinc-800 rounded-full overflow-hidden flex flex-col justify-end">
                <div
                  className="w-full bg-[#1E56FF] rounded-full transition-all"
                  style={{ height: `${volumeLevel}%` }}
                />
              </div>
              <span className="text-[8px] font-mono text-zinc-300">{volumeLevel}%</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Inner AMOLED Display Surface */}
        <div
          style={{ filter: screenBrightnessFilter }}
          className={`relative w-full h-full rounded-[34px] overflow-hidden flex flex-col transition-colors duration-200 ${
            deviceState.isLocked
              ? "bg-black"
              : deviceState.darkMode
              ? "bg-[#090A0D] text-zinc-100"
              : "bg-[#F4F5F8] text-zinc-900"
          }`}
        >
          {deviceState.isLocked ? (
            <div
              onClick={() => setDeviceState((prev) => ({ ...prev, isLocked: false }))}
              className="h-full flex flex-col justify-between py-12 px-6 items-center text-center cursor-pointer"
            >
              <div className="space-y-1">
                <span className="text-4xl font-light text-zinc-100 block">12:45</span>
                <span className="text-xs text-zinc-400">Mon, Sep 26</span>
              </div>
              <div className="p-3 rounded-full bg-white/5 border border-white/10">
                <Power className="w-4 h-4 text-[#1E56FF]" />
              </div>
              <span className="text-[11px] text-zinc-500">Tap to unlock</span>
            </div>
          ) : (
            <>
              {/* One UI Status Bar */}
              <div
                onClick={toggleQuickPanel}
                className={`w-full px-5 pt-2 pb-1 flex items-center justify-between text-[11px] font-medium select-none z-30 cursor-pointer transition-colors ${
                  deviceState.darkMode ? "text-zinc-300 hover:bg-white/5" : "text-zinc-700 hover:bg-black/5"
                }`}
                title="Tap to toggle Quick Panel"
              >
                <span className="font-mono text-[10px]">12:45</span>
                <div className="flex items-center gap-1.5">
                  <Wifi className="w-3 h-3" />
                  <span className="text-[9px] font-mono font-semibold">5G</span>
                  {deviceState.powerSaving ? (
                    <div className="flex items-center text-amber-500 font-mono text-[10px]">
                      <BatteryCharging className="w-3 h-3" />
                      <span>78%</span>
                    </div>
                  ) : (
                    <div className="flex items-center text-emerald-500 font-mono text-[10px]">
                      <Battery className="w-3 h-3" />
                      <span>85%</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Dynamic Action Capsule Notification */}
              <AnimatePresence>
                {deviceState.lastActionNotice && (
                  <motion.div
                    initial={{ opacity: 0, y: -6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    transition={{ duration: 0.15 }}
                    className="mx-3 my-1 px-2.5 py-1.5 rounded-lg bg-[#1E56FF] text-white flex items-center gap-2 shadow-md z-30"
                  >
                    <div className="w-4 h-4 rounded-full bg-white text-[#1E56FF] flex items-center justify-center font-bold shrink-0">
                      <Check className="w-3 h-3 stroke-[3]" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <span className="text-[8px] uppercase font-bold tracking-wider block text-blue-100">
                        Galaxy Action Executed
                      </span>
                      <span className="text-[10px] font-medium block truncate">
                        {deviceState.lastActionNotice}
                      </span>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Quick Settings Panel */}
              <AnimatePresence>
                {deviceState.quickPanelOpen && (
                  <motion.div
                    initial={{ y: "-100%" }}
                    animate={{ y: 0 }}
                    exit={{ y: "-100%" }}
                    transition={{ duration: 0.2 }}
                    className="absolute inset-0 z-40 bg-[#0E1013]/95 backdrop-blur-md p-4 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between pb-2 border-b border-white/10">
                        <span className="text-xs font-semibold text-white">Quick Settings</span>
                        <button
                          onClick={toggleQuickPanel}
                          className="text-[11px] text-[#1E56FF] hover:underline font-medium"
                        >
                          Done
                        </button>
                      </div>

                      {/* Wi-Fi / Bluetooth */}
                      <div className="grid grid-cols-2 gap-2 mt-3">
                        <div className="p-2 rounded-lg bg-[#1E56FF]/20 border border-[#1E56FF]/40 flex items-center gap-2">
                          <Wifi className="w-3.5 h-3.5 text-[#1E56FF]" />
                          <div>
                            <span className="text-[10px] font-medium block text-white">Galaxy_5G</span>
                            <span className="text-[8px] text-blue-200">Connected</span>
                          </div>
                        </div>
                        <div className="p-2 rounded-lg bg-white/5 border border-white/10 flex items-center gap-2">
                          <Zap className="w-3.5 h-3.5 text-zinc-400" />
                          <div>
                            <span className="text-[10px] font-medium block text-white">Bluetooth</span>
                            <span className="text-[8px] text-zinc-400">Galaxy Buds</span>
                          </div>
                        </div>
                      </div>

                      {/* Quick Grid Toggles */}
                      <div className="grid grid-cols-4 gap-1.5 mt-2.5 text-center">
                        <button
                          onClick={() => toggleDarkMode(!deviceState.darkMode)}
                          className={`p-2 rounded-lg border flex flex-col items-center gap-1 transition-all ${
                            deviceState.darkMode
                              ? "bg-[#1E56FF]/20 border-[#1E56FF]/50 text-blue-300"
                              : "bg-white/5 border-white/10 text-zinc-300"
                          }`}
                        >
                          <Moon className="w-3.5 h-3.5" />
                          <span className="text-[8px]">Dark</span>
                        </button>

                        <button
                          onClick={togglePowerSaving}
                          className={`p-2 rounded-lg border flex flex-col items-center gap-1 transition-all ${
                            deviceState.powerSaving
                              ? "bg-amber-500/20 border-amber-500/50 text-amber-300"
                              : "bg-white/5 border-white/10 text-zinc-300"
                          }`}
                        >
                          <Battery className="w-3.5 h-3.5" />
                          <span className="text-[8px]">Power</span>
                        </button>

                        <button
                          onClick={toggleAdaptiveBrightness}
                          className={`p-2 rounded-lg border flex flex-col items-center gap-1 transition-all ${
                            deviceState.adaptiveBrightness
                              ? "bg-emerald-500/20 border-emerald-500/50 text-emerald-300"
                              : "bg-white/5 border-white/10 text-zinc-300"
                          }`}
                        >
                          <Sun className="w-3.5 h-3.5" />
                          <span className="text-[8px]">Adaptive</span>
                        </button>

                        <button
                          onClick={handleRebootSafeMode}
                          className="p-2 rounded-lg border border-white/10 bg-white/5 hover:bg-rose-500/20 text-zinc-300 flex flex-col items-center gap-1 transition-all"
                        >
                          <Power className="w-3.5 h-3.5 text-rose-400" />
                          <span className="text-[8px]">Safe</span>
                        </button>
                      </div>

                      {/* Brightness Slider */}
                      <div className="mt-3 p-2.5 rounded-lg bg-white/5 border border-white/10 space-y-1">
                        <div className="flex items-center justify-between text-[10px] text-zinc-400">
                          <span className="flex items-center gap-1">
                            <Sun className="w-3 h-3 text-amber-400" />
                            Brightness
                          </span>
                          <span className="font-mono text-zinc-200">{deviceState.brightness}%</span>
                        </div>
                        <input
                          type="range"
                          min={20}
                          max={100}
                          value={deviceState.brightness}
                          onChange={(e) =>
                            setDeviceState((prev) => ({
                              ...prev,
                              brightness: Number(e.target.value),
                            }))
                          }
                          className="w-full accent-[#1E56FF] cursor-pointer h-1.5 rounded-lg bg-zinc-800"
                        />
                      </div>
                    </div>

                    <div className="text-center pt-2">
                      <button
                        onClick={() => navigateTo("settings")}
                        className="w-full py-1.5 rounded-md bg-[#1E56FF] hover:bg-[#2F68FD] text-white text-xs font-medium transition-all"
                      >
                        All Settings
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Main Dynamic Screen Content Area */}
              <div className="flex-1 overflow-y-auto px-3.5 py-2 relative scrollbar-none">
                <AnimatePresence mode="popLayout" initial={false}>
                  {/* SCREEN 1: GALAXY HOME SCREEN */}
                  {deviceState.screen === "home" && (
                    <motion.div
                      key="home"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={screenTransition}
                      className="h-full flex flex-col justify-between py-2"
                    >
                      {/* Clock & Weather Widget */}
                      <div className={`p-3.5 rounded-2xl border text-center transition-colors ${
                        deviceState.darkMode ? "bg-white/[0.04] border-white/10 text-white" : "bg-black/[0.03] border-black/10 text-zinc-900"
                      }`}>
                        <span className="text-3xl font-light tracking-tight block">12:45</span>
                        <span className="text-[10px] text-zinc-400 block mt-0.5">Mon, September 26</span>
                        <div className="flex items-center justify-center gap-1 text-[10px] text-zinc-400 mt-1.5">
                          <Sun className="w-3 h-3 text-amber-500" />
                          <span>24°C Sunny · Seoul</span>
                        </div>
                      </div>

                      {/* Google Search Pill */}
                      <div className={`px-3 py-1.5 rounded-full border flex items-center justify-between text-xs text-zinc-400 ${
                        deviceState.darkMode ? "bg-white/[0.04] border-white/10" : "bg-black/[0.03] border-black/10"
                      }`}>
                        <span className="text-[10px]">Search Galaxy...</span>
                        <Search className="w-3 h-3 text-zinc-400" />
                      </div>

                      {/* Authentic Galaxy App Grid */}
                      <div className="grid grid-cols-4 gap-2.5 py-1">
                        <div className="flex flex-col items-center gap-1">
                          <div className="w-10 h-10 rounded-xl bg-emerald-500 flex items-center justify-center text-white">
                            <Phone className="w-4 h-4 fill-white" />
                          </div>
                          <span className="text-[9px] text-zinc-400">Phone</span>
                        </div>

                        <div className="flex flex-col items-center gap-1">
                          <div className="w-10 h-10 rounded-xl bg-blue-500 flex items-center justify-center text-white">
                            <MessageSquare className="w-4 h-4 fill-white" />
                          </div>
                          <span className="text-[9px] text-zinc-400">Messages</span>
                        </div>

                        <div className="flex flex-col items-center gap-1">
                          <div className="w-10 h-10 rounded-xl bg-rose-500 flex items-center justify-center text-white">
                            <Camera className="w-4 h-4" />
                          </div>
                          <span className="text-[9px] text-zinc-400">Camera</span>
                        </div>

                        <div className="flex flex-col items-center gap-1">
                          <div className="w-10 h-10 rounded-xl bg-pink-500 flex items-center justify-center text-white">
                            <Image className="w-4 h-4" />
                          </div>
                          <span className="text-[9px] text-zinc-400">Gallery</span>
                        </div>

                        <button
                          onClick={() => navigateTo("settings")}
                          className="flex flex-col items-center gap-1 group"
                        >
                          <div className="w-10 h-10 rounded-xl bg-zinc-700 group-hover:bg-zinc-600 flex items-center justify-center text-zinc-200 transition-colors">
                            <Sliders className="w-4 h-4" />
                          </div>
                          <span className="text-[9px] text-zinc-400 group-hover:text-white">Settings</span>
                        </button>

                        <button
                          onClick={() => navigateTo("battery")}
                          className="flex flex-col items-center gap-1 group"
                        >
                          <div className="w-10 h-10 rounded-xl bg-[#1E56FF] group-hover:bg-[#2F68FD] flex items-center justify-center text-white transition-colors">
                            <Zap className="w-4 h-4 fill-white" />
                          </div>
                          <span className="text-[9px] text-zinc-400 group-hover:text-white">Battery</span>
                        </button>

                        <button
                          onClick={() => navigateTo("display")}
                          className="flex flex-col items-center gap-1 group"
                        >
                          <div className="w-10 h-10 rounded-xl bg-amber-500 flex items-center justify-center text-white transition-colors">
                            <Sun className="w-4 h-4 fill-white" />
                          </div>
                          <span className="text-[9px] text-zinc-400 group-hover:text-white">Display</span>
                        </button>

                        <button
                          onClick={() => navigateTo("storage")}
                          className="flex flex-col items-center gap-1 group"
                        >
                          <div className="w-10 h-10 rounded-xl bg-purple-600 flex items-center justify-center text-white transition-colors">
                            <Trash2 className="w-4 h-4" />
                          </div>
                          <span className="text-[9px] text-zinc-400 group-hover:text-white">Storage</span>
                        </button>
                      </div>

                      <button
                        onClick={() => navigateTo("settings")}
                        className="w-full py-2 rounded-lg bg-[#1E56FF]/15 hover:bg-[#1E56FF]/25 border border-[#1E56FF]/30 text-[#1E56FF] text-xs font-medium flex items-center justify-center gap-1.5 transition-colors"
                      >
                        <Sliders className="w-3.5 h-3.5" />
                        <span>Open Settings</span>
                      </button>
                    </motion.div>
                  )}

                  {/* SCREEN 2: SETTINGS ROOT MENU */}
                  {deviceState.screen === "settings" && (
                    <motion.div
                      key="settings"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={screenTransition}
                      className="space-y-2.5 pb-4"
                    >
                      <div className="pt-1 pb-0.5">
                        <span className={`text-lg font-semibold block ${deviceState.darkMode ? "text-white" : "text-zinc-900"}`}>
                          Settings
                        </span>
                        <span className="text-[10px] text-zinc-400">One UI 6.1</span>
                      </div>

                      <div className={`p-2.5 rounded-xl border flex items-center gap-2.5 ${
                        deviceState.darkMode ? "bg-white/[0.04] border-white/10" : "bg-black/[0.03] border-black/10"
                      }`}>
                        <div className="w-8 h-8 rounded-full bg-[#1E56FF] flex items-center justify-center font-bold text-white text-xs">
                          S
                        </div>
                        <div className="flex-1 min-w-0">
                          <span className="text-xs font-medium block truncate">Samsung Account</span>
                          <span className="text-[9px] text-zinc-400 truncate block">galaxy.user@samsung.com</span>
                        </div>
                      </div>

                      <div className="space-y-1">
                        <button
                          onClick={() => navigateTo("display")}
                          className={`w-full p-2.5 rounded-xl border flex items-center justify-between text-left transition-colors ${
                            deviceState.darkMode ? "bg-white/[0.03] hover:bg-white/[0.06] border-white/10" : "bg-black/[0.02] hover:bg-black/[0.05] border-black/10"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <div className="p-1.5 rounded-lg bg-amber-500/20 text-amber-500">
                              <Sun className="w-3.5 h-3.5" />
                            </div>
                            <div>
                              <span className="text-xs font-medium block">Display</span>
                              <span className="text-[9px] text-zinc-400">Brightness, Dark mode</span>
                            </div>
                          </div>
                          <ChevronRight className="w-3.5 h-3.5 text-zinc-400" />
                        </button>

                        <button
                          onClick={() => navigateTo("battery")}
                          className={`w-full p-2.5 rounded-xl border flex items-center justify-between text-left transition-colors ${
                            deviceState.darkMode ? "bg-white/[0.03] hover:bg-white/[0.06] border-white/10" : "bg-black/[0.02] hover:bg-black/[0.05] border-black/10"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <div className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-500">
                              <Zap className="w-3.5 h-3.5" />
                            </div>
                            <div>
                              <span className="text-xs font-medium block">Battery &amp; Device care</span>
                              <span className="text-[9px] text-zinc-400">Optimization, Power saving</span>
                            </div>
                          </div>
                          <ChevronRight className="w-3.5 h-3.5 text-zinc-400" />
                        </button>

                        <button
                          onClick={() => navigateTo("storage")}
                          className={`w-full p-2.5 rounded-xl border flex items-center justify-between text-left transition-colors ${
                            deviceState.darkMode ? "bg-white/[0.03] hover:bg-white/[0.06] border-white/10" : "bg-black/[0.02] hover:bg-black/[0.05] border-black/10"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <div className="p-1.5 rounded-lg bg-purple-500/20 text-purple-500">
                              <Trash2 className="w-3.5 h-3.5" />
                            </div>
                            <div>
                              <span className="text-xs font-medium block">App Storage</span>
                              <span className="text-[9px] text-zinc-400">Clear cache &amp; manage data</span>
                            </div>
                          </div>
                          <ChevronRight className="w-3.5 h-3.5 text-zinc-400" />
                        </button>
                      </div>
                    </motion.div>
                  )}

                  {/* SCREEN 3: DISPLAY SETTINGS */}
                  {deviceState.screen === "display" && (
                    <motion.div
                      key="display"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={screenTransition}
                      className="space-y-3 pb-4"
                    >
                      <div className="flex items-center gap-2 pt-1">
                        <button
                          onClick={() => navigateTo("settings")}
                          className="p-1 rounded-md hover:bg-white/10 text-zinc-400 transition-colors"
                        >
                          <ArrowLeft className="w-3.5 h-3.5" />
                        </button>
                        <span className={`text-sm font-semibold ${deviceState.darkMode ? "text-white" : "text-zinc-900"}`}>
                          Display
                        </span>
                      </div>

                      {/* Dark / Light Mode Switcher */}
                      <div className="grid grid-cols-2 gap-2">
                        <button
                          onClick={() => toggleDarkMode(false)}
                          className={`p-2.5 rounded-xl border text-center transition-all ${
                            !deviceState.darkMode
                              ? "bg-white border-[#1E56FF] ring-1 ring-[#1E56FF] text-zinc-900 shadow-sm"
                              : "bg-white/[0.04] border-white/10 text-zinc-400"
                          }`}
                        >
                          <Sun className="w-4 h-4 mx-auto mb-1 text-amber-500" />
                          <span className="text-xs font-medium block">Light</span>
                        </button>

                        <button
                          onClick={() => toggleDarkMode(true)}
                          className={`p-2.5 rounded-xl border text-center transition-all ${
                            deviceState.darkMode
                              ? "bg-[#1E56FF]/20 border-[#1E56FF] ring-1 ring-[#1E56FF] text-white shadow-sm"
                              : "bg-white/[0.04] border-white/10 text-zinc-400"
                          }`}
                        >
                          <Moon className="w-4 h-4 mx-auto mb-1 text-blue-400" />
                          <span className="text-xs font-medium block">Dark</span>
                        </button>
                      </div>

                      {/* Brightness Slider */}
                      <div className={`p-3 rounded-xl border space-y-1.5 ${
                        deviceState.darkMode ? "bg-white/[0.04] border-white/10" : "bg-black/[0.03] border-black/10"
                      }`}>
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-medium">Brightness</span>
                          <span className="font-mono text-[10px] text-zinc-400">{deviceState.brightness}%</span>
                        </div>
                        <input
                          type="range"
                          min={10}
                          max={100}
                          value={deviceState.brightness}
                          onChange={(e) =>
                            setDeviceState((prev) => ({
                              ...prev,
                              brightness: Number(e.target.value),
                            }))
                          }
                          className="w-full accent-[#1E56FF] cursor-pointer h-1.5 rounded-lg bg-zinc-700"
                        />
                      </div>

                      {/* Adaptive Brightness Toggle */}
                      <div
                        onClick={toggleAdaptiveBrightness}
                        className={`p-2.5 rounded-xl border flex items-center justify-between cursor-pointer ${
                          deviceState.darkMode ? "bg-white/[0.04] border-white/10" : "bg-black/[0.03] border-black/10"
                        }`}
                      >
                        <div>
                          <span className="text-xs font-medium block">Adaptive brightness</span>
                          <span className="text-[9px] text-zinc-400">Optimize for lighting</span>
                        </div>
                        <div
                          className={`w-9 h-5 rounded-full transition-colors p-0.5 flex items-center ${
                            deviceState.adaptiveBrightness ? "bg-[#1E56FF] justify-end" : "bg-zinc-600 justify-start"
                          }`}
                        >
                          <div className="w-4 h-4 rounded-full bg-white shadow-sm" />
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* SCREEN 4: BATTERY & DEVICE CARE */}
                  {deviceState.screen === "battery" && (
                    <motion.div
                      key="battery"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={screenTransition}
                      className="space-y-3 pb-4"
                    >
                      <div className="flex items-center gap-2 pt-1">
                        <button
                          onClick={() => navigateTo("settings")}
                          className="p-1 rounded-md hover:bg-white/10 text-zinc-400 transition-colors"
                        >
                          <ArrowLeft className="w-3.5 h-3.5" />
                        </button>
                        <span className={`text-sm font-semibold ${deviceState.darkMode ? "text-white" : "text-zinc-900"}`}>
                          Device Care
                        </span>
                      </div>

                      {/* Circular Score Meter */}
                      <div className={`p-4 rounded-xl border text-center flex flex-col items-center ${
                        deviceState.darkMode ? "bg-white/[0.04] border-white/10" : "bg-black/[0.03] border-black/10"
                      }`}>
                        <div className="relative w-20 h-20 flex items-center justify-center">
                          <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                            <path
                              className="text-zinc-700"
                              strokeWidth="3.5"
                              stroke="currentColor"
                              fill="none"
                              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            />
                            <path
                              className="text-emerald-500 transition-all duration-700"
                              strokeDasharray={`${deviceCareScore}, 100`}
                              strokeWidth="3.5"
                              strokeLinecap="round"
                              stroke="currentColor"
                              fill="none"
                              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            />
                          </svg>
                          <div className="absolute flex flex-col items-center">
                            <span className="text-xl font-bold font-mono">{deviceCareScore}</span>
                            <span className="text-[8px] text-zinc-400 uppercase font-semibold">Score</span>
                          </div>
                        </div>

                        <span className="text-xs font-semibold mt-2 block">
                          {deviceCareScore === 100 ? "Great condition" : "Good condition"}
                        </span>
                        <span className="text-[9px] text-zinc-400 mt-0.5">
                          {deviceCareScore === 100 ? "No issues detected" : "1 app consuming background power"}
                        </span>

                        <button
                          onClick={handleOptimizeNow}
                          disabled={isOptimizing || deviceCareScore === 100}
                          className={`mt-3 w-full py-2 rounded-lg text-xs font-medium transition-all ${
                            deviceCareScore === 100
                              ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                              : "bg-[#1E56FF] hover:bg-[#2F68FD] text-white active:scale-95 shadow-sm"
                          }`}
                        >
                          {isOptimizing ? "Optimizing..." : deviceCareScore === 100 ? "Optimized" : "Optimize Now"}
                        </button>
                      </div>

                      {/* Power Saving Switch */}
                      <div
                        onClick={togglePowerSaving}
                        className={`p-2.5 rounded-xl border flex items-center justify-between cursor-pointer ${
                          deviceState.darkMode ? "bg-white/[0.04] border-white/10" : "bg-black/[0.03] border-black/10"
                        }`}
                      >
                        <div>
                          <span className="text-xs font-medium block">Power saving</span>
                          <span className="text-[9px] text-zinc-400">Limit CPU speed &amp; background sync</span>
                        </div>
                        <div
                          className={`w-9 h-5 rounded-full transition-colors p-0.5 flex items-center ${
                            deviceState.powerSaving ? "bg-[#1E56FF] justify-end" : "bg-zinc-600 justify-start"
                          }`}
                        >
                          <div className="w-4 h-4 rounded-full bg-white shadow-sm" />
                        </div>
                      </div>

                      {/* Protect Battery Switch */}
                      <div
                        onClick={toggleProtectBattery}
                        className={`p-2.5 rounded-xl border flex items-center justify-between cursor-pointer ${
                          deviceState.darkMode ? "bg-white/[0.04] border-white/10" : "bg-black/[0.03] border-black/10"
                        }`}
                      >
                        <div>
                          <span className="text-xs font-medium block">Protect battery</span>
                          <span className="text-[9px] text-zinc-400">Cap max charge at 80%</span>
                        </div>
                        <div
                          className={`w-9 h-5 rounded-full transition-colors p-0.5 flex items-center ${
                            deviceState.protectBattery ? "bg-emerald-500 justify-end" : "bg-zinc-600 justify-start"
                          }`}
                        >
                          <div className="w-4 h-4 rounded-full bg-white shadow-sm" />
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* SCREEN 5: APP STORAGE & CACHE CLEANUP */}
                  {deviceState.screen === "storage" && (
                    <motion.div
                      key="storage"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={screenTransition}
                      className="space-y-3 pb-4"
                    >
                      <div className="flex items-center gap-2 pt-1">
                        <button
                          onClick={() => navigateTo("settings")}
                          className="p-1 rounded-md hover:bg-white/10 text-zinc-400 transition-colors"
                        >
                          <ArrowLeft className="w-3.5 h-3.5" />
                        </button>
                        <span className={`text-sm font-semibold ${deviceState.darkMode ? "text-white" : "text-zinc-900"}`}>
                          App Storage
                        </span>
                      </div>

                      <div className={`p-2.5 rounded-xl border flex items-center gap-2.5 ${
                        deviceState.darkMode ? "bg-white/[0.04] border-white/10" : "bg-black/[0.03] border-black/10"
                      }`}>
                        <div className="w-8 h-8 rounded-lg bg-rose-500/20 text-rose-500 flex items-center justify-center font-bold text-xs">
                          <Flame className="w-4 h-4" />
                        </div>
                        <div>
                          <span className="text-xs font-medium block">Gmail / Email App</span>
                          <span className="text-[9px] text-zinc-400">System App</span>
                        </div>
                      </div>

                      <div className={`p-3 rounded-xl border space-y-1.5 ${
                        deviceState.darkMode ? "bg-white/[0.04] border-white/10" : "bg-black/[0.03] border-black/10"
                      }`}>
                        <span className="text-xs font-medium block">Space Used</span>
                        <div className="flex justify-between text-[10px] text-zinc-400">
                          <span>App Binary:</span>
                          <span className="font-mono">48.2 MB</span>
                        </div>
                        <div className="flex justify-between text-[10px] text-zinc-400">
                          <span>User Data:</span>
                          <span className="font-mono">112.4 MB</span>
                        </div>
                        <div className="flex justify-between text-[10px] font-semibold text-[#1E56FF] pt-1 border-t border-white/10">
                          <span>Cached Files:</span>
                          <span className="font-mono">
                            {deviceState.cacheSizeMb > 0 ? `${deviceState.cacheSizeMb}.0 MB` : "0.0 MB (Cleared)"}
                          </span>
                        </div>
                      </div>

                      <button
                        onClick={handleClearCache}
                        disabled={deviceState.cacheSizeMb === 0}
                        className={`w-full py-2.5 rounded-lg border text-xs font-medium flex items-center justify-center gap-1.5 transition-all ${
                          deviceState.cacheSizeMb > 0
                            ? "bg-[#1E56FF] hover:bg-[#2F68FD] border-[#1E56FF] text-white active:scale-95 shadow-sm"
                            : "bg-emerald-500/15 border-emerald-500/30 text-emerald-400 cursor-default"
                        }`}
                      >
                        {deviceState.cacheSizeMb > 0 ? (
                          <>
                            <Trash2 className="w-3.5 h-3.5" />
                            <span>Clear Cache</span>
                          </>
                        ) : (
                          <>
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                            <span>Cache Cleared</span>
                          </>
                        )}
                      </button>
                    </motion.div>
                  )}

                  {/* SCREEN 6: SAFE MODE REBOOT */}
                  {deviceState.screen === "safe_mode" && (
                    <motion.div
                      key="safe_mode"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="h-full flex flex-col items-center justify-center text-center space-y-2"
                    >
                      <RefreshCw className="w-7 h-7 text-[#1E56FF] animate-spin" />
                      <span className="text-xs font-semibold text-white block">Samsung Galaxy</span>
                      <span className="text-[10px] text-zinc-400 font-mono">Rebooting in Safe Mode...</span>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {deviceState.isSafeMode && (
                <div className="absolute bottom-5 left-3 z-30 px-1.5 py-0.5 rounded bg-black/90 border border-zinc-700 text-[8px] font-mono text-amber-400 pointer-events-none">
                  Safe mode
                </div>
              )}

              {/* Bottom Navigation Pill */}
              <div className="w-full py-1 flex justify-center z-30">
                <button
                  onClick={() => navigateTo("home")}
                  className="w-20 h-1 rounded-full bg-zinc-500/50 hover:bg-zinc-400 active:scale-95 transition-all cursor-pointer"
                  title="One UI Home Bar"
                  aria-label="One UI Home Bar"
                />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
