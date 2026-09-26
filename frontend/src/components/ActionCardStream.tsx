import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  ExternalLink,
  CheckCircle,
  Cpu,
  Wrench,
  AlertTriangle,
  Copy,
  Check,
  Play,
} from "lucide-react";
import type { ActionPayload, GoalPayload, SimulatedDeviceState, OneUIScreen } from "../types/engine";
import { itemVariants } from "../theme/motion";

interface ActionCardStreamProps {
  goal: GoalPayload | null;
  deviceState: SimulatedDeviceState;
  onTriggerDeeplink: (deeplink: string, targetScreen: OneUIScreen, actionName?: string) => void;
  onSuccessToast: (msg: string) => void;
}

export const ActionCardStream: React.FC<ActionCardStreamProps> = ({
  goal,
  deviceState,
  onTriggerDeeplink,
  onSuccessToast,
}) => {
  const [completedSteps, setCompletedSteps] = useState<Record<string, boolean>>({});
  const [copiedLink, setCopiedLink] = useState<string | null>(null);

  if (!goal || !goal.actions || goal.actions.length === 0) {
    return null;
  }

  const toggleStep = (stepKey: string) => {
    setCompletedSteps((prev) => {
      const updated = { ...prev, [stepKey]: !prev[stepKey] };
      if (updated[stepKey]) {
        onSuccessToast("Step marked as completed");
      }
      return updated;
    });
  };

  const handleCopy = (deeplink: string) => {
    navigator.clipboard.writeText(deeplink);
    setCopiedLink(deeplink);
    onSuccessToast("Verbatim Bixby URI copied to clipboard");
    setTimeout(() => setCopiedLink(null), 2000);
  };

  // Determine target One UI screen from action name and steps
  const inferTargetScreen = (action: ActionPayload): OneUIScreen => {
    const text = `${action.actionName} ${action.description} ${action.stepGroups.flatMap((sg) => sg.steps).join(" ")}`.toLowerCase();
    if (text.includes("safe mode") || text.includes("reboot") || text.includes("restart")) return "safe_mode";
    if (text.includes("battery") || text.includes("power saving") || text.includes("device care")) return "battery";
    if (text.includes("display") || text.includes("brightness") || text.includes("dark mode") || text.includes("flicker")) return "display";
    if (text.includes("cache") || text.includes("storage") || text.includes("app data") || text.includes("gmail")) return "storage";
    return "settings";
  };

  const completedCount = Object.values(completedSteps).filter(Boolean).length;
  const totalStepsCount = goal.actions.reduce(
    (acc, a) => acc + a.stepGroups.reduce((sgAcc, sg) => sgAcc + sg.steps.length, 0),
    0
  );
  const progressPercent = totalStepsCount > 0 ? Math.round((completedCount / totalStepsCount) * 100) : 0;

  return (
    <div className="w-full space-y-4">
      {/* Plan Header with Progress Bar & Calibrated Confidence */}
      <div className="p-4 rounded-3xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl shadow-lg space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-sky-400" />
              <span className="text-[11px] font-bold text-sky-400 uppercase tracking-wider block">
                Guided Plan ({goal.actions.length} {goal.actions.length === 1 ? "Action" : "Actions"})
              </span>
            </div>
            <h3 className="text-base sm:text-lg font-bold text-white tracking-tight break-words mt-0.5">
              {goal.title}
            </h3>
          </div>

          <div className="flex items-center gap-1.5 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-xl text-xs text-emerald-300 font-medium">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
            <span>Verified Samsung Solution</span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-1.5 pt-1 border-t border-slate-800/60">
          <div className="flex justify-between text-[11px] text-slate-400">
            <span>Troubleshooting Progress</span>
            <span className="font-mono text-sky-300 font-semibold">{progressPercent}% Completed</span>
          </div>
          <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-sky-500 to-blue-600 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progressPercent}%` }}
              transition={{ duration: 0.4 }}
            />
          </div>
        </div>
      </div>

      {/* Action Cards Stream */}
      <div className="space-y-3.5">
        {goal.actions.map((action, actionIdx) => {
          const targetScreen = inferTargetScreen(action);
          const isCurrentScreen = deviceState.screen === targetScreen;
          const isCritical = action.category === "critical";
          const isManual = action.category === "manual";
          const isAutoSkipped = action.actionName.toLowerCase().includes("brightness") && deviceState.adaptiveBrightness;

          return (
            <motion.div
              key={actionIdx}
              variants={itemVariants}
              initial="hidden"
              animate="visible"
              className={`p-4 sm:p-5 rounded-3xl border backdrop-blur-xl transition-all shadow-lg ${
                isCurrentScreen
                  ? "bg-slate-900/90 border-sky-500/50 ring-1 ring-sky-500/20 shadow-sky-500/10"
                  : "bg-slate-900/60 border-slate-800/80 hover:border-slate-700/80"
              }`}
            >
              {/* Card Header */}
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div
                    className={`w-7 h-7 rounded-xl flex items-center justify-center font-bold text-xs shrink-0 mt-0.5 ${
                      isCurrentScreen
                        ? "bg-sky-500 text-white shadow-md shadow-sky-500/30"
                        : "bg-slate-800 text-slate-300 border border-white/5"
                    }`}
                  >
                    {String(actionIdx + 1).padStart(2, "0")}
                  </div>
                  <div>
                    <h4 className="text-sm sm:text-base font-bold text-white tracking-tight">
                      {action.actionName}
                    </h4>
                    <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">
                      {action.description}
                    </p>
                  </div>
                </div>

                {/* Badge Tag */}
                <div className="shrink-0">
                  {isManual ? (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300 text-[10px] font-bold uppercase tracking-wider">
                      <Wrench className="w-3 h-3 text-sky-400" />
                      Guided Step
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-sky-500/15 border border-sky-500/30 text-sky-300 text-[10px] font-bold uppercase tracking-wider">
                      <Cpu className="w-3 h-3 text-sky-400" />
                      1-Tap Setting
                    </span>
                  )}
                  {isCritical && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-400 text-[10px] font-bold uppercase tracking-wider ml-1.5">
                      <AlertTriangle className="w-3 h-3" />
                      Recommended
                    </span>
                  )}
                </div>
              </div>

              {/* Setting Already Active Ribbon */}
              {isAutoSkipped && (
                <div className="my-3 px-3 py-2 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center gap-2 text-xs text-emerald-300">
                  <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span className="font-semibold">
                    Already Active: Your Galaxy confirms this setting is already enabled.
                  </span>
                </div>
              )}

              {/* Sub-Steps with Checkbox Interactivity */}
              <div className="space-y-2 mt-3 pt-3 border-t border-slate-800/80">
                {action.stepGroups.map((sg, sgIdx) => (
                  <div key={sgIdx} className="space-y-2">
                    {sg.steps.map((stepText, stepIdx) => {
                      const stepKey = `${actionIdx}-${sgIdx}-${stepIdx}`;
                      const isDone = !!completedSteps[stepKey];

                      return (
                        <div
                          key={stepIdx}
                          onClick={() => toggleStep(stepKey)}
                          className={`flex items-start gap-2.5 p-2 rounded-xl cursor-pointer transition-colors text-xs sm:text-sm select-none ${
                            isDone
                              ? "bg-emerald-950/20 text-slate-400 line-through"
                              : "hover:bg-slate-800/50 text-slate-200"
                          }`}
                        >
                          <div
                            className={`w-4 h-4 mt-0.5 rounded-md border flex items-center justify-center shrink-0 transition-colors ${
                              isDone
                                ? "bg-emerald-500 border-emerald-500 text-white"
                                : "border-slate-600 bg-slate-900"
                            }`}
                          >
                            {isDone && <Check className="w-3 h-3" />}
                          </div>
                          <span className="break-words flex-1 leading-relaxed">
                            {stepText}
                          </span>
                        </div>
                      );
                    })}

                    {/* Interactive "Simulate on Galaxy S24" and Deeplink Actions */}
                    <div className="pt-2 flex flex-wrap items-center gap-2">
                      {/* Prominent Simulate on Device Button */}
                      <button
                        onClick={() => {
                          const deeplink = sg.actionableDeeplink?.deeplink || `settings://${targetScreen}`;
                          onTriggerDeeplink(deeplink, targetScreen, action.actionName);
                          onSuccessToast(`Applied "${action.actionName}" on your Galaxy`);
                        }}
                        className={`flex items-center gap-1.5 px-4 py-2 rounded-xl font-semibold text-xs transition-all active:scale-95 shadow-md ${
                          isCurrentScreen
                            ? "bg-gradient-to-r from-sky-400 to-blue-500 text-white shadow-sky-500/30"
                            : "bg-slate-800 hover:bg-slate-700 text-sky-300 border border-sky-400/30"
                        }`}
                      >
                        <Play className="w-3.5 h-3.5 fill-current" />
                        <span>Simulate on Galaxy S24</span>
                      </button>

                      {/* Deeplink Trigger Button */}
                      {sg.actionableDeeplink && (
                        <>
                          <button
                            onClick={() => {
                              onTriggerDeeplink(sg.actionableDeeplink!.deeplink, targetScreen, action.actionName);
                            }}
                            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs border border-white/10 transition-all"
                          >
                            <ExternalLink className="w-3 h-3 text-sky-400" />
                            <span>{sg.actionableDeeplink.message || "Open in Settings"}</span>
                          </button>

                          <button
                            onClick={() => handleCopy(sg.actionableDeeplink!.deeplink)}
                            className="px-2.5 py-2 rounded-xl bg-slate-900/80 hover:bg-slate-800 text-slate-400 hover:text-white border border-white/10 transition-all text-xs flex items-center gap-1.5"
                            title="Copy Direct Settings Link"
                          >
                            {copiedLink === sg.actionableDeeplink.deeplink ? (
                              <>
                                <Check className="w-3.5 h-3.5 text-emerald-400" />
                                <span className="text-[11px] text-emerald-300">Copied</span>
                              </>
                            ) : (
                              <>
                                <Copy className="w-3.5 h-3.5" />
                                <span className="text-[11px]">Copy Link</span>
                              </>
                            )}
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
