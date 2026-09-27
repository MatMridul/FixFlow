import React, { useState, useEffect } from "react";
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
import { springs, transitions } from "../theme/motion";

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
  const [volumeLevel, setVolumeLevel] = useState<number | null>(null);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [deviceCareScore, setDeviceCareScore] = useState(94);
  const [touchPulse, setTouchPulse] = useState(false);

  // Trigger touch pulse cursor when a fix action notice is received
  useEffect(() => {
    if (deviceState.lastActionNotice) {
      const showTimer = setTimeout(() => setTouchPulse(true), 10);
      const hideTimer = setTimeout(() => setTouchPulse(false), 700);
      return () => {
        clearTimeout(showTimer);
        clearTimeout(hideTimer);
      };
    }
  }, [deviceState.lastActionNotice]);

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
    setTimeout(() => setDeviceCareScore(96), 200);
    setTimeout(() => setDeviceCareScore(98), 400);
    setTimeout(() => {
      setIsOptimizing(false);
      setDeviceCareScore(100);
      setDeviceState((prev) => ({
        ...prev,
        cacheSizeMb: 0,
        lastActionNotice: "Device fully optimized (100%)",
      }));
    }, 700);
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
            <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
            <span className="text-xs font-semibold text-white">
              Galaxy S24 Ultra (One UI 6.1)
            </span>
          </div>
          <button
            onClick={onCloseMobile}
            className="px-2.5 py-1 rounded bg-[#181818] hover:bg-[#222222] text-xs font-medium text-white transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      )}

      {/* Galaxy Device Outer Frame: Titanium Chassis */}
      <div className="relative w-full max-w-[310px] h-[590px] bg-[#0A0A0A] rounded-[42px] p-2 border-[4px] border-[#222222] shadow-[0_20px_50px_rgba(0,0,0,0.9)] flex flex-col overflow-hidden ring-1 ring-white/[0.08]">
        
        {/* Hardware Side Buttons */}
        <button
          onClick={() => handleVolumeKey(10)}
          className="absolute -left-[8px] top-28 w-1.5 h-10 bg-[#333333] rounded-l active:bg-white transition-colors cursor-pointer"
          title="Volume Up"
          aria-label="Volume Up"
        />
        <button
          onClick={() => handleVolumeKey(-10)}
          className="absolute -left-[8px] top-40 w-1.5 h-10 bg-[#333333] rounded-l active:bg-white transition-colors cursor-pointer"
          title="Volume Down"
          aria-label="Volume Down"
        />
        <button
          onClick={handlePowerButton}
          className="absolute -right-[8px] top-32 w-1.5 h-12 bg-[#333333] rounded-r active:bg-white transition-colors cursor-pointer"
          title="Power / Lock Screen"
          aria-label="Power Button"
        />

        {/* Punch Hole Infinity-O Camera */}
        <div className="absolute top-3.5 left-1/2 -translate-x-1/2 w-3.5 h-3.5 rounded-full bg-black z-40 flex items-center justify-center pointer-events-none">
          <div className="w-1.5 h-1.5 rounded-full bg-[#111111] border border-white/20" />
        </div>

        {/* Simulated Touch Pulse Cursor (Monochrome White) */}
        <AnimatePresence>
          {touchPulse && (
            <motion.div
              initial={{ scale: 0.4, opacity: 0.9 }}
              animate={{ scale: 2.2, opacity: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.65, ease: "easeOut" }}
              className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 rounded-full border-2 border-white bg-white/20 pointer-events-none z-50 shadow-[0_0_20px_rgba(255,255,255,0.6)]"
            />
          )}
        </AnimatePresence>

        {/* Volume Pill Overlay */}
        <AnimatePresence>
          {volumeLevel !== null && (
            <motion.div
              initial={{ opacity: 0, x: -16 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -16 }}
              transition={springs.pill}
              className="absolute left-4 top-28 z-50 bg-[#111111] border border-white/20 rounded-xl p-2 shadow-2xl flex flex-col items-center gap-1.5"
            >
              <Volume2 className="w-3.5 h-3.5 text-white" />
              <div className="w-1 h-14 bg-[#222222] rounded-full overflow-hidden flex flex-col justify-end">
                <motion.div
                  className="w-full bg-white rounded-full"
                  animate={{ height: `${volumeLevel}%` }}
                  transition={{ type: "spring", stiffness: 400, damping: 30 }}
                />
              </div>
              <span className="text-[8px] font-mono text-white">{volumeLevel}%</span>
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
              ? "bg-black text-white"
              : "bg-white text-black"
          }`}
        >
          {deviceState.isLocked ? (
            <div
              onClick={() => setDeviceState((prev) => ({ ...prev, isLocked: false }))}
              className="h-full flex flex-col justify-between py-12 px-6 items-center text-center cursor-pointer"
            >
              <div className="space-y-1">
                <span className="text-4xl font-light text-white block">12:45</span>
                <span className="text-xs text-neutral-400">Mon, Sep 26</span>
              </div>
              <motion.div
                animate={{ scale: [1, 1.08, 1] }}
                transition={{ repeat: Infinity, duration: 2 }}
                className="p-3 rounded-full bg-white/10 border border-white/20"
              >
                <Power className="w-4 h-4 text-white" />
              </motion.div>
              <span className="text-[11px] text-neutral-400">Tap to unlock</span>
            </div>
          ) : (
            <>
              {/* One UI Status Bar */}
              <div
                onClick={toggleQuickPanel}
                className={`w-full px-5 pt-2 pb-1 flex items-center justify-between text-[11px] font-medium select-none z-30 cursor-pointer transition-colors ${
                  deviceState.darkMode ? "text-neutral-300 hover:bg-white/5" : "text-neutral-700 hover:bg-black/5"
                }`}
                title="Tap to toggle Quick Panel"
              >
                <span className="font-mono text-[10px]">12:45</span>
                <div className="flex items-center gap-1.5">
                  <Wifi className="w-3 h-3" />
                  <span className="text-[9px] font-mono font-semibold">5G</span>
                  {deviceState.powerSaving ? (
                    <div className="flex items-center text-neutral-400 font-mono text-[10px]">
                      <BatteryCharging className="w-3 h-3" />
                      <span>78%</span>
                    </div>
                  ) : (
                    <div className="flex items-center text-white font-mono text-[10px]">
                      <Battery className="w-3 h-3" />
                      <span>85%</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Dynamic Action Capsule Notification (Monochrome White) */}
              <AnimatePresence>
                {deviceState.lastActionNotice && (
                  <motion.div
                    initial={{ opacity: 0, y: -12, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -8, scale: 0.95 }}
                    transition={springs.pill}
                    className="mx-3 my-1 px-2.5 py-1.5 rounded bg-white text-black flex items-center gap-2 shadow-md z-30"
                  >
                    <div className="w-4 h-4 rounded-full bg-black text-white flex items-center justify-center font-bold shrink-0">
                      <Check className="w-3 h-3 stroke-[3]" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <span className="text-[8px] uppercase font-bold tracking-wider block text-neutral-600">
                        Galaxy Action Executed
                      </span>
                      <span className="text-[10px] font-bold block truncate text-black">
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
                    transition={springs.slide}
                    className="absolute inset-0 z-40 bg-black/95 backdrop-blur-md p-4 flex flex-col justify-between text-white"
                  >
                    <div>
                      <div className="flex items-center justify-between pb-2 border-b border-white/10">
                        <span className="text-xs font-semibold text-white">Quick Settings</span>
                        <button
                          onClick={toggleQuickPanel}
                          className="text-[11px] text-white hover:underline font-semibold cursor-pointer"
                        >
                          Done
                        </button>
                      </div>

                      {/* Wi-Fi / Bluetooth */}
                      <div className="grid grid-cols-2 gap-2 mt-3">
                        <div className="p-2 rounded bg-white/10 border border-white/20 flex items-center gap-2">
                          <Wifi className="w-3.5 h-3.5 text-white" />
                          <div>
                            <span className="text-[10px] font-medium block text-white">Galaxy_5G</span>
                            <span className="text-[8px] text-neutral-400">Connected</span>
                          </div>
                        </div>
                        <div className="p-2 rounded bg-white/5 border border-white/10 flex items-center gap-2">
                          <Zap className="w-3.5 h-3.5 text-neutral-400" />
                          <div>
                            <span className="text-[10px] font-medium block text-white">Bluetooth</span>
                            <span className="text-[8px] text-neutral-400">Galaxy Buds</span>
                          </div>
                        </div>
                      </div>

                      {/* Quick Grid Toggles */}
                      <div className="grid grid-cols-4 gap-1.5 mt-2.5 text-center">
                        <motion.button
                          whileTap={{ scale: 0.95 }}
                          onClick={() => toggleDarkMode(!deviceState.darkMode)}
                          className={`p-2 rounded border flex flex-col items-center gap-1 transition-colors cursor-pointer ${
                            deviceState.darkMode
                              ? "bg-white text-black border-white"
                              : "bg-white/5 border-white/10 text-neutral-300"
                          }`}
                        >
                          <Moon className="w-3.5 h-3.5" />
                          <span className="text-[8px]">Dark</span>
                        </motion.button>

                        <motion.button
                          whileTap={{ scale: 0.95 }}
                          onClick={togglePowerSaving}
                          className={`p-2 rounded border flex flex-col items-center gap-1 transition-colors cursor-pointer ${
                            deviceState.powerSaving
                              ? "bg-white text-black border-white"
                              : "bg-white/5 border-white/10 text-neutral-300"
                          }`}
                        >
                          <Battery className="w-3.5 h-3.5" />
                          <span className="text-[8px]">Power</span>
                        </motion.button>

                        <motion.button
                          whileTap={{ scale: 0.95 }}
                          onClick={toggleAdaptiveBrightness}
                          className={`p-2 rounded border flex flex-col items-center gap-1 transition-colors cursor-pointer ${
                            deviceState.adaptiveBrightness
                              ? "bg-white text-black border-white"
                              : "bg-white/5 border-white/10 text-neutral-300"
                          }`}
                        >
                          <Sun className="w-3.5 h-3.5" />
                          <span className="text-[8px]">Adaptive</span>
                        </motion.button>

                        <motion.button
                          whileTap={{ scale: 0.95 }}
                          onClick={handleRebootSafeMode}
                          className="p-2 rounded border border-white/10 bg-white/5 hover:bg-white/20 text-neutral-300 flex flex-col items-center gap-1 transition-colors cursor-pointer"
                        >
                          <Power className="w-3.5 h-3.5 text-white" />
                          <span className="text-[8px]">Safe</span>
                        </motion.button>
                      </div>

                      {/* Brightness Slider */}
                      <div className="mt-3 p-2.5 rounded bg-white/5 border border-white/10 space-y-1">
                        <div className="flex items-center justify-between text-[10px] text-neutral-400">
                          <span className="flex items-center gap-1 text-white">
                            <Sun className="w-3 h-3 text-white" />
                            Brightness
                          </span>
                          <span className="font-mono text-white font-semibold">{deviceState.brightness}%</span>
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
                          className="w-full accent-white cursor-pointer h-1.5 rounded bg-neutral-800"
                        />
                      </div>
                    </div>

                    <div className="text-center pt-2">
                      <button
                        onClick={() => navigateTo("settings")}
                        className="w-full py-1.5 rounded bg-white hover:bg-neutral-200 text-black text-xs font-semibold transition-colors cursor-pointer"
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
                      initial={{ opacity: 0, x: 18 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -18 }}
                      transition={transitions.screenSlide}
                      className="h-full flex flex-col justify-between py-2"
                    >
                      {/* Clock & Weather Widget */}
                      <div className={`p-3.5 rounded-2xl border text-center transition-colors ${
                        deviceState.darkMode ? "bg-white/[0.04] border-white/10 text-white" : "bg-black/[0.04] border-black/10 text-black"
                      }`}>
                        <span className="text-3xl font-light tracking-tight block">12:45</span>
                        <span className="text-[10px] text-neutral-400 block mt-0.5">Mon, September 26</span>
                        <div className="flex items-center justify-center gap-1 text-[10px] text-neutral-400 mt-1.5">
                          <Sun className="w-3 h-3 text-neutral-300" />
                          <span>24°C Sunny · Seoul</span>
                        </div>
                      </div>

                      {/* Google Search Pill */}
                      <div className={`px-3 py-1.5 rounded-full border flex items-center justify-between text-xs text-neutral-400 ${
                        deviceState.darkMode ? "bg-white/[0.04] border-white/10" : "bg-black/[0.04] border-black/10"
                      }`}>
                        <span className="text-[10px]">Search Galaxy...</span>
                        <Search className="w-3.5 h-3.5 text-neutral-400" />
                      </div>

                      {/* Authentic Galaxy App Grid (Monochrome) */}
                      <div className="grid grid-cols-4 gap-2.5 py-1">
                        <motion.div whileTap={{ scale: 0.92 }} className="flex flex-col items-center gap-1 cursor-pointer">
                          <div className="w-10 h-10 rounded-xl bg-white text-black flex items-center justify-center shadow-sm">
                            <Phone className="w-4 h-4 fill-black" />
                          </div>
                          <span className="text-[9px] text-neutral-400">Phone</span>
                        </motion.div>

                        <motion.div whileTap={{ scale: 0.92 }} className="flex flex-col items-center gap-1 cursor-pointer">
                          <div className="w-10 h-10 rounded-xl bg-neutral-200 text-black flex items-center justify-center shadow-sm">
                            <MessageSquare className="w-4 h-4 fill-black" />
                          </div>
                          <span className="text-[9px] text-neutral-400">Messages</span>
                        </motion.div>

                        <motion.div whileTap={{ scale: 0.92 }} className="flex flex-col items-center gap-1 cursor-pointer">
                          <div className="w-10 h-10 rounded-xl bg-neutral-300 text-black flex items-center justify-center shadow-sm">
                            <Camera className="w-4 h-4" />
                          </div>
                          <span className="text-[9px] text-neutral-400">Camera</span>
                        </motion.div>

                        <motion.div whileTap={{ scale: 0.92 }} className="flex flex-col items-center gap-1 cursor-pointer">
                          <div className="w-10 h-10 rounded-xl bg-neutral-400 text-black flex items-center justify-center shadow-sm">
                            <Image className="w-4 h-4" />
                          </div>
                          <span className="text-[9px] text-neutral-400">Gallery</span>
                        </motion.div>

                        <motion.button
                          whileTap={{ scale: 0.92 }}
                          onClick={() => navigateTo("settings")}
                          className="flex flex-col items-center gap-1 group cursor-pointer"
                        >
                          <div className="w-10 h-10 rounded-xl bg-neutral-800 group-hover:bg-neutral-700 flex items-center justify-center text-white transition-colors shadow-sm border border-white/10">
                            <Sliders className="w-4 h-4" />
                          </div>
                          <span className="text-[9px] text-neutral-400 group-hover:text-white">Settings</span>
                        </motion.button>

                        <motion.button
                          whileTap={{ scale: 0.92 }}
                          onClick={() => navigateTo("battery")}
                          className="flex flex-col items-center gap-1 group cursor-pointer"
                        >
                          <div className="w-10 h-10 rounded-xl bg-white group-hover:bg-neutral-200 flex items-center justify-center text-black transition-colors shadow-sm">
                            <Zap className="w-4 h-4 fill-black" />
                          </div>
                          <span className="text-[9px] text-neutral-400 group-hover:text-white">Battery</span>
                        </motion.button>

                        <motion.button
                          whileTap={{ scale: 0.92 }}
                          onClick={() => navigateTo("display")}
                          className="flex flex-col items-center gap-1 group cursor-pointer"
                        >
                          <div className="w-10 h-10 rounded-xl bg-neutral-200 flex items-center justify-center text-black transition-colors shadow-sm">
                            <Sun className="w-4 h-4 fill-black" />
                          </div>
                          <span className="text-[9px] text-neutral-400 group-hover:text-white">Display</span>
                        </motion.button>

                        <motion.button
                          whileTap={{ scale: 0.92 }}
                          onClick={() => navigateTo("storage")}
                          className="flex flex-col items-center gap-1 group cursor-pointer"
                        >
                          <div className="w-10 h-10 rounded-xl bg-neutral-800 flex items-center justify-center text-white transition-colors shadow-sm border border-white/10">
                            <Trash2 className="w-4 h-4" />
                          </div>
                          <span className="text-[9px] text-neutral-400 group-hover:text-white">Storage</span>
                        </motion.button>
                      </div>

                      <motion.button
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => navigateTo("settings")}
                        className="w-full py-2 rounded bg-white text-black text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors cursor-pointer hover:bg-neutral-200"
                      >
                        <Sliders className="w-3.5 h-3.5" />
                        <span>Open Settings</span>
                      </motion.button>
                    </motion.div>
                  )}

                  {/* SCREEN 2: SETTINGS ROOT MENU */}
                  {deviceState.screen === "settings" && (
                    <motion.div
                      key="settings"
                      initial={{ opacity: 0, x: 18 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -18 }}
                      transition={transitions.screenSlide}
                      className="space-y-2.5 pb-4"
                    >
                      <div className="pt-1 pb-0.5">
                        <span className={`text-lg font-semibold block ${deviceState.darkMode ? "text-white" : "text-black"}`}>
                          Settings
                        </span>
                        <span className="text-[10px] text-neutral-400">One UI 6.1</span>
                      </div>

                      <div className={`p-2.5 rounded-xl border flex items-center gap-2.5 ${
                        deviceState.darkMode ? "bg-white/[0.04] border-white/10" : "bg-black/[0.04] border-black/10"
                      }`}>
                        <div className="w-8 h-8 rounded-full bg-white text-black flex items-center justify-center font-bold text-xs">
                          S
                        </div>
                        <div className="flex-1 min-w-0">
                          <span className="text-xs font-semibold block truncate">Samsung Account</span>
                          <span className="text-[9px] text-neutral-400 truncate block">galaxy.user@samsung.com</span>
                        </div>
                      </div>

                      <div className="space-y-1">
                        <motion.button
                          whileTap={{ scale: 0.98 }}
                          onClick={() => navigateTo("display")}
                          className={`w-full p-2.5 rounded-xl border flex items-center justify-between text-left transition-colors cursor-pointer ${
                            deviceState.darkMode ? "bg-white/[0.03] hover:bg-white/[0.06] border-white/10" : "bg-black/[0.02] hover:bg-black/[0.05] border-black/10"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <div className="p-1.5 rounded-lg bg-white/10 text-white">
                              <Sun className="w-3.5 h-3.5" />
                            </div>
                            <div>
                              <span className="text-xs font-medium block">Display</span>
                              <span className="text-[9px] text-neutral-400">Brightness, Dark mode</span>
                            </div>
                          </div>
                          <ChevronRight className="w-3.5 h-3.5 text-neutral-400" />
                        </motion.button>

                        <motion.button
                          whileTap={{ scale: 0.98 }}
                          onClick={() => navigateTo("battery")}
                          className={`w-full p-2.5 rounded-xl border flex items-center justify-between text-left transition-colors cursor-pointer ${
                            deviceState.darkMode ? "bg-white/[0.03] hover:bg-white/[0.06] border-white/10" : "bg-black/[0.02] hover:bg-black/[0.05] border-black/10"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <div className="p-1.5 rounded-lg bg-white/10 text-white">
                              <Zap className="w-3.5 h-3.5" />
                            </div>
                            <div>
                              <span className="text-xs font-medium block">Battery &amp; Device care</span>
                              <span className="text-[9px] text-neutral-400">Optimization, Power saving</span>
                            </div>
                          </div>
                          <ChevronRight className="w-3.5 h-3.5 text-neutral-400" />
                        </motion.button>

                        <motion.button
                          whileTap={{ scale: 0.98 }}
                          onClick={() => navigateTo("storage")}
                          className={`w-full p-2.5 rounded-xl border flex items-center justify-between text-left transition-colors cursor-pointer ${
                            deviceState.darkMode ? "bg-white/[0.03] hover:bg-white/[0.06] border-white/10" : "bg-black/[0.02] hover:bg-black/[0.05] border-black/10"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <div className="p-1.5 rounded-lg bg-white/10 text-white">
                              <Trash2 className="w-3.5 h-3.5" />
                            </div>
                            <div>
                              <span className="text-xs font-medium block">App Storage</span>
                              <span className="text-[9px] text-neutral-400">Clear cache &amp; manage data</span>
                            </div>
                          </div>
                          <ChevronRight className="w-3.5 h-3.5 text-neutral-400" />
                        </motion.button>
                      </div>
                    </motion.div>
                  )}

                  {/* SCREEN 3: DISPLAY SETTINGS */}
                  {deviceState.screen === "display" && (
                    <motion.div
                      key="display"
                      initial={{ opacity: 0, x: 18 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -18 }}
                      transition={transitions.screenSlide}
                      className="space-y-3 pb-4"
                    >
                      <div className="flex items-center gap-2 pt-1">
                        <button
                          onClick={() => navigateTo("settings")}
                          className="p-1 rounded hover:bg-white/10 text-neutral-400 transition-colors cursor-pointer"
                        >
                          <ArrowLeft className="w-3.5 h-3.5" />
                        </button>
                        <span className={`text-sm font-semibold ${deviceState.darkMode ? "text-white" : "text-black"}`}>
                          Display
                        </span>
                      </div>

                      {/* Dark / Light Mode Switcher with shared sliding pill */}
                      <div className="grid grid-cols-2 gap-2 relative">
                        <button
                          onClick={() => toggleDarkMode(false)}
                          className={`relative p-2.5 rounded-xl border text-center transition-colors cursor-pointer ${
                            !deviceState.darkMode
                              ? "border-black text-black font-semibold"
                              : "border-white/10 text-neutral-400 bg-white/[0.04]"
                          }`}
                        >
                          {!deviceState.darkMode && (
                            <motion.div
                              layoutId="themePill"
                              className="absolute inset-0 bg-white rounded-xl shadow-sm"
                              transition={springs.pill}
                            />
                          )}
                          <span className="relative z-10 flex flex-col items-center">
                            <Sun className="w-4 h-4 mx-auto mb-1 text-black" />
                            <span className="text-xs font-semibold block">Light</span>
                          </span>
                        </button>

                        <button
                          onClick={() => toggleDarkMode(true)}
                          className={`relative p-2.5 rounded-xl border text-center transition-colors cursor-pointer ${
                            deviceState.darkMode
                              ? "border-white text-white font-semibold"
                              : "border-black/10 text-neutral-600 bg-black/[0.04]"
                          }`}
                        >
                          {deviceState.darkMode && (
                            <motion.div
                              layoutId="themePill"
                              className="absolute inset-0 bg-white text-black rounded-xl shadow-sm"
                              transition={springs.pill}
                            />
                          )}
                          <span className="relative z-10 flex flex-col items-center">
                            <Moon className={`w-4 h-4 mx-auto mb-1 ${deviceState.darkMode ? "text-black" : "text-white"}`} />
                            <span className={`text-xs font-semibold block ${deviceState.darkMode ? "text-black" : "text-white"}`}>Dark</span>
                          </span>
                        </button>
                      </div>

                      {/* Brightness Slider */}
                      <div className={`p-3 rounded-xl border space-y-1.5 ${
                        deviceState.darkMode ? "bg-white/[0.04] border-white/10" : "bg-black/[0.04] border-black/10"
                      }`}>
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-medium">Brightness</span>
                          <span className="font-mono text-[10px]">{deviceState.brightness}%</span>
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
                          className="w-full accent-white cursor-pointer h-1.5 rounded bg-neutral-800"
                        />
                      </div>

                      {/* Adaptive Brightness Toggle */}
                      <div
                        onClick={toggleAdaptiveBrightness}
                        className={`p-2.5 rounded-xl border flex items-center justify-between cursor-pointer transition-colors ${
                          deviceState.darkMode ? "bg-white/[0.04] border-white/10" : "bg-black/[0.04] border-black/10"
                        }`}
                      >
                        <div>
                          <span className="text-xs font-medium block">Adaptive brightness</span>
                          <span className="text-[9px] text-neutral-400">Optimize for lighting</span>
                        </div>
                        <div
                          className={`w-9 h-5 rounded-full transition-colors p-0.5 flex items-center ${
                            deviceState.adaptiveBrightness ? "bg-white justify-end" : "bg-neutral-700 justify-start"
                          }`}
                        >
                          <motion.div layout className={`w-4 h-4 rounded-full shadow-sm ${deviceState.adaptiveBrightness ? "bg-black" : "bg-white"}`} />
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* SCREEN 4: BATTERY & DEVICE CARE */}
                  {deviceState.screen === "battery" && (
                    <motion.div
                      key="battery"
                      initial={{ opacity: 0, x: 18 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -18 }}
                      transition={transitions.screenSlide}
                      className="space-y-3 pb-4"
                    >
                      <div className="flex items-center gap-2 pt-1">
                        <button
                          onClick={() => navigateTo("settings")}
                          className="p-1 rounded hover:bg-white/10 text-neutral-400 transition-colors cursor-pointer"
                        >
                          <ArrowLeft className="w-3.5 h-3.5" />
                        </button>
                        <span className={`text-sm font-semibold ${deviceState.darkMode ? "text-white" : "text-black"}`}>
                          Device Care
                        </span>
                      </div>

                      {/* Circular Score Meter */}
                      <div className={`p-4 rounded-xl border text-center flex flex-col items-center relative overflow-hidden ${
                        deviceState.darkMode ? "bg-white/[0.04] border-white/10" : "bg-black/[0.04] border-black/10"
                      }`}>
                        <div className="relative w-20 h-20 flex items-center justify-center">
                          <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                            <path
                              className="text-neutral-800"
                              strokeWidth="3.5"
                              stroke="currentColor"
                              fill="none"
                              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            />
                            <path
                              className="text-white transition-all duration-500"
                              strokeDasharray={`${deviceCareScore}, 100`}
                              strokeWidth="3.5"
                              strokeLinecap="round"
                              stroke="currentColor"
                              fill="none"
                              d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                            />
                          </svg>
                          <div className="absolute flex flex-col items-center">
                            <motion.span
                              key={deviceCareScore}
                              initial={{ scale: 0.8 }}
                              animate={{ scale: 1 }}
                              className="text-xl font-bold font-mono text-white"
                            >
                              {deviceCareScore}
                            </motion.span>
                            <span className="text-[8px] text-neutral-400 uppercase font-semibold">Score</span>
                          </div>
                        </div>

                        <span className="text-xs font-semibold mt-2 block text-white">
                          {deviceCareScore === 100 ? "Great condition" : "Good condition"}
                        </span>
                        <span className="text-[9px] text-neutral-400 mt-0.5">
                          {deviceCareScore === 100 ? "No issues detected" : "1 app consuming background power"}
                        </span>

                        <motion.button
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.96 }}
                          onClick={handleOptimizeNow}
                          disabled={isOptimizing || deviceCareScore === 100}
                          className={`mt-3 w-full py-2 rounded text-xs font-semibold transition-colors cursor-pointer ${
                            deviceCareScore === 100
                              ? "bg-white/10 text-white border border-white/20"
                              : "bg-white hover:bg-neutral-200 text-black active:scale-95 shadow-sm"
                          }`}
                        >
                          {isOptimizing ? "Optimizing..." : deviceCareScore === 100 ? "Optimized" : "Optimize Now"}
                        </motion.button>
                      </div>

                      {/* Power Saving Switch */}
                      <div
                        onClick={togglePowerSaving}
                        className={`p-2.5 rounded-xl border flex items-center justify-between cursor-pointer transition-colors ${
                          deviceState.darkMode ? "bg-white/[0.04] border-white/10" : "bg-black/[0.04] border-black/10"
                        }`}
                      >
                        <div>
                          <span className="text-xs font-medium block">Power saving</span>
                          <span className="text-[9px] text-neutral-400">Limit CPU speed &amp; background sync</span>
                        </div>
                        <div
                          className={`w-9 h-5 rounded-full transition-colors p-0.5 flex items-center ${
                            deviceState.powerSaving ? "bg-white justify-end" : "bg-neutral-700 justify-start"
                          }`}
                        >
                          <motion.div layout className={`w-4 h-4 rounded-full shadow-sm ${deviceState.powerSaving ? "bg-black" : "bg-white"}`} />
                        </div>
                      </div>

                      {/* Protect Battery Switch */}
                      <div
                        onClick={toggleProtectBattery}
                        className={`p-2.5 rounded-xl border flex items-center justify-between cursor-pointer transition-colors ${
                          deviceState.darkMode ? "bg-white/[0.04] border-white/10" : "bg-black/[0.04] border-black/10"
                        }`}
                      >
                        <div>
                          <span className="text-xs font-medium block">Protect battery</span>
                          <span className="text-[9px] text-neutral-400">Cap max charge at 80%</span>
                        </div>
                        <div
                          className={`w-9 h-5 rounded-full transition-colors p-0.5 flex items-center ${
                            deviceState.protectBattery ? "bg-white justify-end" : "bg-neutral-700 justify-start"
                          }`}
                        >
                          <motion.div layout className={`w-4 h-4 rounded-full shadow-sm ${deviceState.protectBattery ? "bg-black" : "bg-white"}`} />
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* SCREEN 5: APP STORAGE & CACHE CLEANUP */}
                  {deviceState.screen === "storage" && (
                    <motion.div
                      key="storage"
                      initial={{ opacity: 0, x: 18 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -18 }}
                      transition={transitions.screenSlide}
                      className="space-y-3 pb-4"
                    >
                      <div className="flex items-center gap-2 pt-1">
                        <button
                          onClick={() => navigateTo("settings")}
                          className="p-1 rounded hover:bg-white/10 text-neutral-400 transition-colors cursor-pointer"
                        >
                          <ArrowLeft className="w-3.5 h-3.5" />
                        </button>
                        <span className={`text-sm font-semibold ${deviceState.darkMode ? "text-white" : "text-black"}`}>
                          App Storage
                        </span>
                      </div>

                      <div className={`p-2.5 rounded-xl border flex items-center gap-2.5 ${
                        deviceState.darkMode ? "bg-white/[0.04] border-white/10" : "bg-black/[0.04] border-black/10"
                      }`}>
                        <div className="w-8 h-8 rounded-lg bg-white/10 text-white flex items-center justify-center font-bold text-xs">
                          <Flame className="w-4 h-4" />
                        </div>
                        <div>
                          <span className="text-xs font-semibold block">Gmail / Email App</span>
                          <span className="text-[9px] text-neutral-400">System App</span>
                        </div>
                      </div>

                      <div className={`p-3 rounded-xl border space-y-1.5 ${
                        deviceState.darkMode ? "bg-white/[0.04] border-white/10" : "bg-black/[0.04] border-black/10"
                      }`}>
                        <span className="text-xs font-medium block">Space Used</span>
                        <div className="flex justify-between text-[10px] text-neutral-400">
                          <span>App Binary:</span>
                          <span className="font-mono text-white">48.2 MB</span>
                        </div>
                        <div className="flex justify-between text-[10px] text-neutral-400">
                          <span>User Data:</span>
                          <span className="font-mono text-white">112.4 MB</span>
                        </div>
                        <div className="flex justify-between text-[10px] font-semibold text-white pt-1 border-t border-white/10">
                          <span>Cached Files:</span>
                          <motion.span
                            key={deviceState.cacheSizeMb}
                            initial={{ scale: 1.15 }}
                            animate={{ scale: 1 }}
                            className="font-mono text-white"
                          >
                            {deviceState.cacheSizeMb > 0 ? `${deviceState.cacheSizeMb}.0 MB` : "0.0 MB (Cleared)"}
                          </motion.span>
                        </div>
                      </div>

                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.96 }}
                        onClick={handleClearCache}
                        disabled={deviceState.cacheSizeMb === 0}
                        className={`w-full py-2.5 rounded text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors cursor-pointer ${
                          deviceState.cacheSizeMb > 0
                            ? "bg-white hover:bg-neutral-200 text-black active:scale-95 shadow-sm"
                            : "bg-white/10 border border-white/20 text-white cursor-default"
                        }`}
                      >
                        {deviceState.cacheSizeMb > 0 ? (
                          <>
                            <Trash2 className="w-3.5 h-3.5" />
                            <span>Clear Cache</span>
                          </>
                        ) : (
                          <>
                            <Check className="w-3.5 h-3.5 text-white" />
                            <span>Cache Cleared</span>
                          </>
                        )}
                      </motion.button>
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
                      className="h-full flex flex-col items-center justify-center text-center space-y-2 text-white"
                    >
                      <RefreshCw className="w-7 h-7 text-white animate-spin" />
                      <span className="text-xs font-semibold text-white block">Samsung Galaxy</span>
                      <span className="text-[10px] text-neutral-400 font-mono">Rebooting in Safe Mode...</span>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {deviceState.isSafeMode && (
                <div className="absolute bottom-5 left-3 z-30 px-1.5 py-0.5 rounded bg-black/90 border border-white/20 text-[8px] font-mono text-white pointer-events-none">
                  Safe mode
                </div>
              )}

              {/* Bottom Navigation Pill */}
              <div className="w-full py-1 flex justify-center z-30">
                <button
                  onClick={() => navigateTo("home")}
                  className="w-20 h-1 rounded-full bg-white/40 hover:bg-white/70 active:scale-95 transition-all cursor-pointer"
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
