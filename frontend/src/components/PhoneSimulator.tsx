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
  ShieldCheck,
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
import { springs } from "../theme/motion";

interface PhoneSimulatorProps {
  deviceState: SimulatedDeviceState;
  setDeviceState: React.Dispatch<React.SetStateAction<SimulatedDeviceState>>;
  onCloseMobile?: () => void;
}

const screenTransition = { duration: 0.2, ease: [0.16, 1, 0.3, 1] as const };

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
    }));
  };

  const handleOptimizeNow = () => {
    setIsOptimizing(true);
    setTimeout(() => {
      setIsOptimizing(false);
      setDeviceCareScore(100);
      setDeviceState((prev) => ({ ...prev, cacheSizeMb: 0 }));
    }, 1200);
  };

  const handleVolumeKey = (change: number) => {
    setVolumeLevel((prev) => {
      const current = prev ?? 65;
      const next = Math.min(100, Math.max(0, current + change));
      return next;
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
    }, 2200);
  };

  const toggleQuickPanel = () => {
    setDeviceState((prev) => ({
      ...prev,
      quickPanelOpen: !prev.quickPanelOpen,
    }));
  };

  // Brightness filter calculation
  const screenBrightnessFilter = `brightness(${0.4 + (deviceState.brightness / 100) * 0.7})`;

  return (
    <div className="w-full flex flex-col items-center select-none">
      {/* Mobile Drawer Header */}
      {onCloseMobile && (
        <div className="w-full flex items-center justify-between pb-3 lg:hidden">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              Galaxy S24 Ultra (One UI 6.1)
            </span>
          </div>
          <button
            onClick={onCloseMobile}
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition-colors"
          >
            Close
          </button>
        </div>
      )}

      {/* Galaxy Device Outer Frame with Hardware Bezel & Metallic Trim */}
      <div className="relative w-full max-w-[320px] h-[640px] bg-gradient-to-b from-slate-900 via-slate-950 to-black rounded-[48px] p-3 border-[6px] border-slate-700/80 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.85)] flex flex-col overflow-hidden ring-1 ring-white/15">
        {/* Hardware Bezel Glare Reflection */}
        <div className="absolute inset-0 rounded-[42px] pointer-events-none bg-gradient-to-tr from-white/[0.04] via-transparent to-white/[0.08]" />

        {/* Hardware Side Buttons */}
        {/* Volume Rocker (Left side) */}
        <button
          onClick={() => handleVolumeKey(10)}
          className="absolute -left-[9px] top-28 w-1.5 h-12 bg-slate-600 rounded-l-md active:bg-sky-400 transition-colors cursor-pointer"
          title="Volume Up"
          aria-label="Volume Up"
        />
        <button
          onClick={() => handleVolumeKey(-10)}
          className="absolute -left-[9px] top-42 w-1.5 h-12 bg-slate-600 rounded-l-md active:bg-sky-400 transition-colors cursor-pointer"
          title="Volume Down"
          aria-label="Volume Down"
        />
        {/* Power Key (Right side) */}
        <button
          onClick={handlePowerButton}
          className="absolute -right-[9px] top-32 w-1.5 h-14 bg-slate-600 rounded-r-md active:bg-rose-400 transition-colors cursor-pointer"
          title="Power / Lock Screen"
          aria-label="Power Button"
        />

        {/* Punch Hole Infinity-O Camera */}
        <div className="absolute top-4 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-black z-40 flex items-center justify-center shadow-inner pointer-events-none">
          <div className="w-1.5 h-1.5 rounded-full bg-slate-950 border border-blue-950/60" />
        </div>

        {/* Live Volume Pill Overlay */}
        <AnimatePresence>
          {volumeLevel !== null && (
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="absolute left-6 top-32 z-50 bg-slate-900/90 border border-white/20 rounded-2xl p-2.5 backdrop-blur-md shadow-2xl flex flex-col items-center gap-1.5"
            >
              <Volume2 className="w-4 h-4 text-sky-400" />
              <div className="w-1.5 h-16 bg-slate-800 rounded-full overflow-hidden flex flex-col justify-end">
                <div
                  className="w-full bg-sky-400 rounded-full transition-all"
                  style={{ height: `${volumeLevel}%` }}
                />
              </div>
              <span className="text-[9px] font-mono text-slate-300">{volumeLevel}%</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Inner AMOLED Display Surface */}
        <div
          style={{ filter: screenBrightnessFilter }}
          className={`relative w-full h-full rounded-[38px] overflow-hidden flex flex-col transition-colors duration-300 ${
            deviceState.isLocked
              ? "bg-black"
              : deviceState.darkMode
              ? "bg-slate-950 text-white"
              : "bg-slate-900 text-white"
          }`}
        >
          {/* Locked State Screen */}
          {deviceState.isLocked ? (
            <div
              onClick={() => setDeviceState((prev) => ({ ...prev, isLocked: false }))}
              className="h-full flex flex-col justify-between py-12 px-6 items-center text-center cursor-pointer"
            >
              <div className="space-y-1">
                <span className="text-5xl font-light text-slate-100 block">12:45</span>
                <span className="text-xs text-slate-400">Mon, Sep 26</span>
              </div>
              <div className="p-3 rounded-full bg-white/5 border border-white/10 animate-bounce">
                <Power className="w-5 h-5 text-sky-400" />
              </div>
              <span className="text-[11px] text-slate-500 font-medium">Swipe to unlock</span>
            </div>
          ) : (
            <>
              {/* One UI Status Bar (Tap to toggle Quick Settings) */}
              <div
                onClick={toggleQuickPanel}
                className="w-full px-5 pt-2.5 pb-1 flex items-center justify-between text-[11px] font-semibold select-none z-30 cursor-pointer hover:bg-white/5 transition-colors"
                title="Tap to toggle Samsung Quick Panel"
              >
                <span className="font-mono text-slate-300">12:45</span>
                <div className="flex items-center gap-1.5 text-slate-300">
                  <Wifi className="w-3 h-3" />
                  <span className="text-[10px] font-mono text-sky-400 font-bold">5G</span>
                  {deviceState.powerSaving ? (
                    <div className="flex items-center text-amber-400 font-mono text-[10px]">
                      <BatteryCharging className="w-3.5 h-3.5" />
                      <span>78%</span>
                    </div>
                  ) : (
                    <div className="flex items-center text-emerald-400 font-mono text-[10px]">
                      <Battery className="w-3.5 h-3.5" />
                      <span>85%</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Dynamic One UI Action Capsule Notification */}
              <AnimatePresence>
                {deviceState.lastActionNotice && (
                  <motion.div
                    initial={{ opacity: 0, y: -6, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -6, scale: 0.95 }}
                    transition={{ duration: 0.18 }}
                    className="mx-3 my-1.5 px-3 py-2 rounded-2xl bg-sky-500/25 border border-sky-400/50 backdrop-blur-xl flex items-center gap-2 text-white shadow-lg shadow-sky-500/10 z-30"
                  >
                    <div className="w-5 h-5 rounded-full bg-sky-400 flex items-center justify-center text-slate-950 font-bold shrink-0">
                      <Check className="w-3.5 h-3.5 stroke-[3]" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <span className="text-[9px] uppercase font-bold tracking-wider block text-sky-300">
                        Galaxy AI Applied Fix
                      </span>
                      <span className="text-[11px] font-semibold block text-white truncate">
                        {deviceState.lastActionNotice}
                      </span>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Quick Settings Panel (Overlay Drawer) */}
              <AnimatePresence>
                {deviceState.quickPanelOpen && (
                  <motion.div
                    initial={{ y: "-100%" }}
                    animate={{ y: 0 }}
                    exit={{ y: "-100%" }}
                    transition={springs.slide}
                    className="absolute inset-0 z-40 bg-slate-950/95 backdrop-blur-2xl p-4 flex flex-col justify-between"
                  >
                    <div>
                      {/* Quick Panel Header */}
                      <div className="flex items-center justify-between pb-3 border-b border-white/10">
                        <span className="text-xs font-bold text-white tracking-wide">
                          Quick Settings
                        </span>
                        <button
                          onClick={toggleQuickPanel}
                          className="text-[11px] text-sky-400 hover:text-sky-300 font-semibold"
                        >
                          Done
                        </button>
                      </div>

                      {/* Main Wi-Fi / Bluetooth Split Cards */}
                      <div className="grid grid-cols-2 gap-2 mt-3">
                        <div className="p-2.5 rounded-2xl bg-sky-500/20 border border-sky-500/40 flex items-center gap-2">
                          <Wifi className="w-4 h-4 text-sky-400" />
                          <div>
                            <span className="text-[11px] font-semibold block text-white">Galaxy_5G</span>
                            <span className="text-[9px] text-sky-300">Connected</span>
                          </div>
                        </div>
                        <div className="p-2.5 rounded-2xl bg-white/5 border border-white/10 flex items-center gap-2">
                          <Zap className="w-4 h-4 text-slate-400" />
                          <div>
                            <span className="text-[11px] font-semibold block text-white">Bluetooth</span>
                            <span className="text-[9px] text-slate-400">Galaxy Buds</span>
                          </div>
                        </div>
                      </div>

                      {/* Quick Grid Toggles */}
                      <div className="grid grid-cols-4 gap-2 mt-3 text-center">
                        {/* Dark Mode */}
                        <button
                          onClick={() => toggleDarkMode(!deviceState.darkMode)}
                          className={`p-2.5 rounded-2xl border flex flex-col items-center gap-1 transition-all ${
                            deviceState.darkMode
                              ? "bg-sky-500/25 border-sky-400/50 text-sky-300"
                              : "bg-white/5 border-white/10 text-slate-300"
                          }`}
                        >
                          <Moon className="w-4 h-4" />
                          <span className="text-[9px]">Dark</span>
                        </button>

                        {/* Power Saving */}
                        <button
                          onClick={togglePowerSaving}
                          className={`p-2.5 rounded-2xl border flex flex-col items-center gap-1 transition-all ${
                            deviceState.powerSaving
                              ? "bg-amber-500/25 border-amber-400/50 text-amber-300"
                              : "bg-white/5 border-white/10 text-slate-300"
                          }`}
                        >
                          <Battery className="w-4 h-4" />
                          <span className="text-[9px]">Power</span>
                        </button>

                        {/* Adaptive Brightness */}
                        <button
                          onClick={toggleAdaptiveBrightness}
                          className={`p-2.5 rounded-2xl border flex flex-col items-center gap-1 transition-all ${
                            deviceState.adaptiveBrightness
                              ? "bg-emerald-500/25 border-emerald-400/50 text-emerald-300"
                              : "bg-white/5 border-white/10 text-slate-300"
                          }`}
                        >
                          <Sun className="w-4 h-4" />
                          <span className="text-[9px]">Adaptive</span>
                        </button>

                        {/* Safe Mode */}
                        <button
                          onClick={handleRebootSafeMode}
                          className="p-2.5 rounded-2xl border border-white/10 bg-white/5 hover:bg-rose-500/20 text-slate-300 flex flex-col items-center gap-1 transition-all"
                        >
                          <Power className="w-4 h-4 text-rose-400" />
                          <span className="text-[9px]">Safe</span>
                        </button>
                      </div>

                      {/* Brightness Slider */}
                      <div className="mt-4 p-3 rounded-2xl bg-white/5 border border-white/10 space-y-1.5">
                        <div className="flex items-center justify-between text-[10px] text-slate-400">
                          <span className="flex items-center gap-1">
                            <Sun className="w-3.5 h-3.5 text-amber-400" />
                            Brightness
                          </span>
                          <span className="font-mono text-slate-200">{deviceState.brightness}%</span>
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
                          className="w-full accent-sky-400 cursor-pointer h-1.5 rounded-lg bg-slate-800"
                        />
                      </div>
                    </div>

                    <div className="text-center pt-2">
                      <button
                        onClick={() => navigateTo("settings")}
                        className="w-full py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-white text-xs font-semibold shadow-md shadow-sky-500/30 transition-all"
                      >
                        All Settings
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Main Dynamic Screen Content Area */}
              <div className="flex-1 overflow-y-auto px-4 py-2 relative scrollbar-none">
                <AnimatePresence mode="popLayout" initial={false}>
                  {/* SCREEN 1: GALAXY HOME SCREEN */}
                  {deviceState.screen === "home" && (
                    <motion.div
                      key="home"
                      initial={{ opacity: 0, scale: 0.98 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.98 }}
                      transition={screenTransition}
                      className="h-full flex flex-col justify-between py-3"
                    >
                      {/* One UI Clock & Weather Widget */}
                      <div className="p-4 rounded-3xl bg-gradient-to-br from-indigo-900/40 via-purple-950/30 to-slate-900/60 border border-white/10 shadow-lg text-center backdrop-blur-md">
                        <span className="text-4xl font-light tracking-tight block text-white">
                          12:45
                        </span>
                        <span className="text-[11px] text-slate-300 block mt-0.5">
                          Mon, September 26
                        </span>
                        <div className="flex items-center justify-center gap-1.5 text-[11px] text-sky-300 mt-2 font-medium">
                          <Sun className="w-3.5 h-3.5 text-amber-400" />
                          <span>24°C Sunny · Seoul</span>
                        </div>
                      </div>

                      {/* Google Search Pill */}
                      <div className="px-3 py-2 rounded-full bg-slate-800/80 border border-white/10 flex items-center justify-between text-xs text-slate-400 shadow-sm">
                        <span className="text-[11px] font-sans">Search Galaxy...</span>
                        <Search className="w-3.5 h-3.5 text-slate-400" />
                      </div>

                      {/* Authentic Galaxy App Grid */}
                      <div className="grid grid-cols-4 gap-3 py-2">
                        {/* Phone */}
                        <div className="flex flex-col items-center gap-1">
                          <div className="w-11 h-11 rounded-2xl bg-emerald-500 shadow-md flex items-center justify-center text-white">
                            <Phone className="w-5 h-5 fill-white" />
                          </div>
                          <span className="text-[10px] text-slate-300">Phone</span>
                        </div>

                        {/* Messages */}
                        <div className="flex flex-col items-center gap-1">
                          <div className="w-11 h-11 rounded-2xl bg-blue-500 shadow-md flex items-center justify-center text-white">
                            <MessageSquare className="w-5 h-5 fill-white" />
                          </div>
                          <span className="text-[10px] text-slate-300">Messages</span>
                        </div>

                        {/* Camera */}
                        <div className="flex flex-col items-center gap-1">
                          <div className="w-11 h-11 rounded-2xl bg-rose-500 shadow-md flex items-center justify-center text-white">
                            <Camera className="w-5 h-5" />
                          </div>
                          <span className="text-[10px] text-slate-300">Camera</span>
                        </div>

                        {/* Gallery */}
                        <div className="flex flex-col items-center gap-1">
                          <div className="w-11 h-11 rounded-2xl bg-pink-500 shadow-md flex items-center justify-center text-white">
                            <Image className="w-5 h-5" />
                          </div>
                          <span className="text-[10px] text-slate-300">Gallery</span>
                        </div>

                        {/* Settings App (Opens Settings) */}
                        <button
                          onClick={() => navigateTo("settings")}
                          className="flex flex-col items-center gap-1 group"
                        >
                          <div className="w-11 h-11 rounded-2xl bg-slate-700 group-hover:bg-slate-600 shadow-md flex items-center justify-center text-sky-400 border border-white/20 transition-all">
                            <Sliders className="w-5 h-5" />
                          </div>
                          <span className="text-[10px] text-slate-300 group-hover:text-white">Settings</span>
                        </button>

                        {/* Device Care App */}
                        <button
                          onClick={() => navigateTo("battery")}
                          className="flex flex-col items-center gap-1 group"
                        >
                          <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-blue-600 to-sky-400 group-hover:scale-105 shadow-md flex items-center justify-center text-white border border-white/20 transition-all">
                            <Zap className="w-5 h-5 fill-white" />
                          </div>
                          <span className="text-[10px] text-slate-300 group-hover:text-white">Device Care</span>
                        </button>

                        {/* Display App */}
                        <button
                          onClick={() => navigateTo("display")}
                          className="flex flex-col items-center gap-1 group"
                        >
                          <div className="w-11 h-11 rounded-2xl bg-amber-500 group-hover:scale-105 shadow-md flex items-center justify-center text-white border border-white/20 transition-all">
                            <Sun className="w-5 h-5 fill-white" />
                          </div>
                          <span className="text-[10px] text-slate-300 group-hover:text-white">Display</span>
                        </button>

                        {/* Storage App */}
                        <button
                          onClick={() => navigateTo("storage")}
                          className="flex flex-col items-center gap-1 group"
                        >
                          <div className="w-11 h-11 rounded-2xl bg-purple-600 group-hover:scale-105 shadow-md flex items-center justify-center text-white border border-white/20 transition-all">
                            <Trash2 className="w-5 h-5" />
                          </div>
                          <span className="text-[10px] text-slate-300 group-hover:text-white">Storage</span>
                        </button>
                      </div>

                      {/* Quick Interactive Prompt to open settings */}
                      <button
                        onClick={() => navigateTo("settings")}
                        className="w-full py-2.5 rounded-2xl bg-sky-500/20 hover:bg-sky-500/30 border border-sky-400/40 text-sky-300 text-xs font-semibold flex items-center justify-center gap-1.5 shadow-md transition-all"
                      >
                        <Sliders className="w-3.5 h-3.5" />
                        <span>Launch One UI Settings</span>
                      </button>
                    </motion.div>
                  )}

                  {/* SCREEN 2: SETTINGS ROOT MENU */}
                  {deviceState.screen === "settings" && (
                    <motion.div
                      key="settings"
                      initial={{ opacity: 0, x: 16 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -16 }}
                      transition={screenTransition}
                      className="space-y-3 pb-6"
                    >
                      {/* Header */}
                      <div className="pt-2 pb-1">
                        <span className="text-xl font-bold block text-white">Settings</span>
                        <span className="text-[11px] text-slate-400">Samsung Galaxy S24 Ultra</span>
                      </div>

                      {/* Profile Card */}
                      <div className="p-3 rounded-2xl bg-white/5 border border-white/10 flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-sky-400 to-blue-600 flex items-center justify-center font-bold text-white text-xs">
                          S
                        </div>
                        <div className="flex-1 min-w-0">
                          <span className="text-xs font-semibold block truncate">Samsung Account</span>
                          <span className="text-[10px] text-slate-400 truncate block">
                            galaxy.user@samsung.com
                          </span>
                        </div>
                      </div>

                      {/* Settings List */}
                      <div className="space-y-1.5">
                        <button
                          onClick={() => navigateTo("display")}
                          className="w-full p-3 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-between text-left transition-colors group"
                        >
                          <div className="flex items-center gap-2.5">
                            <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400">
                              <Sun className="w-4 h-4" />
                            </div>
                            <div>
                              <span className="text-xs font-semibold block text-white group-hover:text-sky-300">
                                Display
                              </span>
                              <span className="text-[10px] text-slate-400">
                                Brightness, Dark mode, Eye comfort
                              </span>
                            </div>
                          </div>
                          <ChevronRight className="w-4 h-4 text-slate-400" />
                        </button>

                        <button
                          onClick={() => navigateTo("battery")}
                          className="w-full p-3 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-between text-left transition-colors group"
                        >
                          <div className="flex items-center gap-2.5">
                            <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-400">
                              <Zap className="w-4 h-4" />
                            </div>
                            <div>
                              <span className="text-xs font-semibold block text-white group-hover:text-sky-300">
                                Battery &amp; Device care
                              </span>
                              <span className="text-[10px] text-slate-400">
                                Power saving, Protect battery, Storage
                              </span>
                            </div>
                          </div>
                          <ChevronRight className="w-4 h-4 text-slate-400" />
                        </button>

                        <button
                          onClick={() => navigateTo("storage")}
                          className="w-full p-3 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-between text-left transition-colors group"
                        >
                          <div className="flex items-center gap-2.5">
                            <div className="p-2 rounded-xl bg-purple-500/20 text-purple-400">
                              <Trash2 className="w-4 h-4" />
                            </div>
                            <div>
                              <span className="text-xs font-semibold block text-white group-hover:text-sky-300">
                                Apps &amp; Cache Storage
                              </span>
                              <span className="text-[10px] text-slate-400">
                                Clear cache, Memory cleanup
                              </span>
                            </div>
                          </div>
                          <ChevronRight className="w-4 h-4 text-slate-400" />
                        </button>
                      </div>
                    </motion.div>
                  )}

                  {/* SCREEN 3: DISPLAY SETTINGS */}
                  {deviceState.screen === "display" && (
                    <motion.div
                      key="display"
                      initial={{ opacity: 0, x: 16 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -16 }}
                      transition={screenTransition}
                      className="space-y-4 pb-6"
                    >
                      {/* Header with Back Arrow */}
                      <div className="flex items-center gap-2.5 pt-1">
                        <button
                          onClick={() => navigateTo("settings")}
                          className="p-1.5 rounded-xl hover:bg-white/10 text-slate-300 transition-colors"
                        >
                          <ArrowLeft className="w-4 h-4" />
                        </button>
                        <span className="text-base font-bold text-white">Display Settings</span>
                      </div>

                      {/* Light / Dark Mode Visual Switcher */}
                      <div className="p-3 rounded-2xl bg-white/5 border border-white/10 space-y-2">
                        <span className="text-xs font-semibold text-slate-200 block">Theme Mode</span>
                        <div className="grid grid-cols-2 gap-2">
                          <button
                            onClick={() => toggleDarkMode(false)}
                            className={`p-2 rounded-xl border flex flex-col items-center gap-1.5 transition-all ${
                              !deviceState.darkMode
                                ? "bg-sky-500/20 border-sky-400 text-sky-200"
                                : "bg-white/5 border-white/10 text-slate-400"
                            }`}
                          >
                            <Sun className="w-4 h-4 text-amber-400" />
                            <span className="text-[11px] font-semibold">Light</span>
                          </button>
                          <button
                            onClick={() => toggleDarkMode(true)}
                            className={`p-2 rounded-xl border flex flex-col items-center gap-1.5 transition-all ${
                              deviceState.darkMode
                                ? "bg-sky-500/20 border-sky-400 text-sky-200"
                                : "bg-white/5 border-white/10 text-slate-400"
                            }`}
                          >
                            <Moon className="w-4 h-4 text-sky-300" />
                            <span className="text-[11px] font-semibold">Dark</span>
                          </button>
                        </div>
                      </div>

                      {/* Brightness Slider */}
                      <div className="p-3 rounded-2xl bg-white/5 border border-white/10 space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-semibold text-slate-200">Brightness</span>
                          <span className="font-mono text-sky-300 font-bold">
                            {deviceState.brightness}%
                          </span>
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
                          className="w-full accent-sky-400 cursor-pointer h-2 rounded-lg bg-slate-800"
                        />
                      </div>

                      {/* Adaptive Brightness Toggle */}
                      <div
                        onClick={toggleAdaptiveBrightness}
                        className={`p-3 rounded-2xl border transition-all cursor-pointer flex items-center justify-between ${
                          deviceState.adaptiveBrightness
                            ? "bg-sky-500/15 border-sky-400/40"
                            : "bg-white/5 border-white/10"
                        }`}
                      >
                        <div>
                          <span className="text-xs font-semibold block text-slate-100">
                            Adaptive Brightness
                          </span>
                          <span className="text-[10px] text-slate-400">
                            Automatically adjusts to lighting
                          </span>
                        </div>
                        <div
                          className={`w-10 h-6 rounded-full transition-colors p-0.5 flex items-center ${
                            deviceState.adaptiveBrightness
                              ? "bg-sky-500 justify-end"
                              : "bg-slate-700 justify-start"
                          }`}
                        >
                          <motion.div
                            layout
                            className="w-5 h-5 rounded-full bg-white shadow-md"
                          />
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* SCREEN 4: BATTERY & DEVICE CARE */}
                  {deviceState.screen === "battery" && (
                    <motion.div
                      key="battery"
                      initial={{ opacity: 0, x: 16 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -16 }}
                      transition={screenTransition}
                      className="space-y-4 pb-6"
                    >
                      {/* Header with Back Arrow */}
                      <div className="flex items-center gap-2.5 pt-1">
                        <button
                          onClick={() => navigateTo("settings")}
                          className="p-1.5 rounded-xl hover:bg-white/10 text-slate-300 transition-colors"
                        >
                          <ArrowLeft className="w-4 h-4" />
                        </button>
                        <span className="text-base font-bold text-white">Device Care</span>
                      </div>

                      {/* Score Dial & Optimize Button */}
                      <div className="p-4 rounded-3xl bg-gradient-to-br from-blue-900/30 to-slate-900/60 border border-white/10 text-center space-y-3">
                        <div className="w-16 h-16 rounded-full border-4 border-sky-400/80 mx-auto flex items-center justify-center font-bold text-xl text-white shadow-lg shadow-sky-500/20">
                          {isOptimizing ? (
                            <RefreshCw className="w-6 h-6 animate-spin text-sky-400" />
                          ) : (
                            deviceCareScore
                          )}
                        </div>
                        <div>
                          <span className="text-xs font-bold text-white block">
                            {isOptimizing
                              ? "Optimizing Subsystems..."
                              : deviceCareScore === 100
                              ? "All Good · Perfect Condition"
                              : "Good · Optimization Available"}
                          </span>
                          <span className="text-[10px] text-slate-400">
                            Battery, storage, and memory status
                          </span>
                        </div>
                        <button
                          onClick={handleOptimizeNow}
                          disabled={isOptimizing}
                          className="w-full py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-white text-xs font-semibold shadow-md shadow-sky-500/30 transition-all flex items-center justify-center gap-1.5"
                        >
                          <ShieldCheck className="w-3.5 h-3.5" />
                          <span>{deviceCareScore === 100 ? "Re-Optimize" : "Optimize Now"}</span>
                        </button>
                      </div>

                      {/* Power Saving Mode Toggle */}
                      <div
                        onClick={togglePowerSaving}
                        className={`p-3 rounded-2xl border transition-all cursor-pointer flex items-center justify-between ${
                          deviceState.powerSaving
                            ? "bg-amber-500/15 border-amber-400/40"
                            : "bg-white/5 border-white/10"
                        }`}
                      >
                        <div className="flex items-center gap-2.5">
                          <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400">
                            <Zap className="w-4 h-4" />
                          </div>
                          <div>
                            <span className="text-xs font-semibold block text-slate-100">
                              Power Saving Mode
                            </span>
                            <span className="text-[10px] text-slate-400">
                              Limits background network &amp; CPU
                            </span>
                          </div>
                        </div>
                        <div
                          className={`w-10 h-6 rounded-full transition-colors p-0.5 flex items-center ${
                            deviceState.powerSaving
                              ? "bg-amber-500 justify-end"
                              : "bg-slate-700 justify-start"
                          }`}
                        >
                          <motion.div
                            layout
                            className="w-5 h-5 rounded-full bg-white shadow-md"
                          />
                        </div>
                      </div>

                      {/* Protect Battery Toggle */}
                      <div
                        onClick={toggleProtectBattery}
                        className={`p-3 rounded-2xl border transition-all cursor-pointer flex items-center justify-between ${
                          deviceState.protectBattery
                            ? "bg-emerald-500/15 border-emerald-400/40"
                            : "bg-white/5 border-white/10"
                        }`}
                      >
                        <div className="flex items-center gap-2.5">
                          <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-400">
                            <ShieldCheck className="w-4 h-4" />
                          </div>
                          <div>
                            <span className="text-xs font-semibold block text-slate-100">
                              Protect Battery (80% Cap)
                            </span>
                            <span className="text-[10px] text-slate-400">
                              Extends lithium lifespan
                            </span>
                          </div>
                        </div>
                        <div
                          className={`w-10 h-6 rounded-full transition-colors p-0.5 flex items-center ${
                            deviceState.protectBattery
                              ? "bg-emerald-500 justify-end"
                              : "bg-slate-700 justify-start"
                          }`}
                        >
                          <motion.div
                            layout
                            className="w-5 h-5 rounded-full bg-white shadow-md"
                          />
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* SCREEN 5: APP STORAGE & CACHE CLEANUP */}
                  {deviceState.screen === "storage" && (
                    <motion.div
                      key="storage"
                      initial={{ opacity: 0, x: 16 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -16 }}
                      transition={screenTransition}
                      className="space-y-4 pb-6"
                    >
                      {/* Header with Back Arrow */}
                      <div className="flex items-center gap-2.5 pt-1">
                        <button
                          onClick={() => navigateTo("settings")}
                          className="p-1.5 rounded-xl hover:bg-white/10 text-slate-300 transition-colors"
                        >
                          <ArrowLeft className="w-4 h-4" />
                        </button>
                        <span className="text-base font-bold text-white">App Storage</span>
                      </div>

                      {/* App Header */}
                      <div className="p-3 rounded-2xl bg-white/5 border border-white/10 flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center font-bold text-xs border border-rose-500/30">
                          <Flame className="w-5 h-5" />
                        </div>
                        <div>
                          <span className="text-xs font-bold text-white block">Gmail / Email App</span>
                          <span className="text-[10px] text-slate-400">Version 2026.09.2 · System App</span>
                        </div>
                      </div>

                      {/* Storage Breakdown */}
                      <div className="p-3.5 rounded-2xl bg-white/5 border border-white/10 space-y-2.5">
                        <span className="text-xs font-semibold text-slate-200 block">Space Used</span>
                        <div className="flex justify-between text-[11px] text-slate-300">
                          <span>App Binary:</span>
                          <span className="font-mono">48.2 MB</span>
                        </div>
                        <div className="flex justify-between text-[11px] text-slate-300">
                          <span>User Data:</span>
                          <span className="font-mono">112.4 MB</span>
                        </div>
                        <div className="flex justify-between text-[11px] font-semibold text-sky-300 pt-1 border-t border-white/10">
                          <span>Cached Files:</span>
                          <span className="font-mono font-bold">
                            {deviceState.cacheSizeMb > 0
                              ? `${deviceState.cacheSizeMb}.0 MB`
                              : "0.0 MB (Cleared)"}
                          </span>
                        </div>
                      </div>

                      {/* Clear Cache Action Button */}
                      <button
                        onClick={handleClearCache}
                        disabled={deviceState.cacheSizeMb === 0}
                        className={`w-full py-3 rounded-2xl border text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
                          deviceState.cacheSizeMb > 0
                            ? "bg-purple-600 hover:bg-purple-500 border-purple-400 text-white shadow-lg shadow-purple-500/25 active:scale-95"
                            : "bg-emerald-500/20 border-emerald-500/40 text-emerald-300 cursor-default"
                        }`}
                      >
                        {deviceState.cacheSizeMb > 0 ? (
                          <>
                            <Trash2 className="w-4 h-4" />
                            <span>Clear Cache (Free {deviceState.cacheSizeMb}MB)</span>
                          </>
                        ) : (
                          <>
                            <Check className="w-4 h-4 text-emerald-400" />
                            <span>Cache Successfully Cleared</span>
                          </>
                        )}
                      </button>
                    </motion.div>
                  )}

                  {/* SCREEN 6: SAFE MODE REBOOT ANIMATION */}
                  {deviceState.screen === "safe_mode" && (
                    <motion.div
                      key="safe_mode"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="h-full flex flex-col items-center justify-center text-center space-y-3"
                    >
                      <RefreshCw className="w-8 h-8 text-sky-400 animate-spin" />
                      <span className="text-sm font-bold text-white block">
                        Samsung Galaxy
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        Rebooting into Safe Mode...
                      </span>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Safe Mode Watermark Badge (when active) */}
              {deviceState.isSafeMode && (
                <div className="absolute bottom-6 left-4 z-30 px-2 py-0.5 rounded bg-black/80 border border-slate-700 text-[9px] font-mono text-amber-400 pointer-events-none">
                  Safe mode
                </div>
              )}

              {/* One UI Bottom Navigation Pill */}
              <div className="w-full py-1.5 flex justify-center z-30">
                <button
                  onClick={() => navigateTo("home")}
                  className="w-24 h-1 rounded-full bg-white/40 hover:bg-white/70 active:scale-95 transition-all cursor-pointer"
                  title="One UI Home Pill - Tap to go to Home Screen"
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
