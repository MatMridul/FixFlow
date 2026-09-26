import React, { useState } from "react";
import { motion } from "framer-motion";
import { ExternalLink, CheckCircle, Cpu, Wrench, AlertTriangle, Copy, Check } from "lucide-react";
import type { ActionPayload, GoalPayload, SimulatedDeviceState } from "../types/engine";
import { itemVariants } from "../theme/motion";

interface ActionCardStreamProps {
  goal: GoalPayload | null;
  deviceState: SimulatedDeviceState;
  onTriggerDeeplink: (deeplink: string, targetScreen: "display" | "battery" | "settings") => void;
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

  return (
    <div className="w-full space-y-4">
      {/* Plan Header & Calibrated Confidence */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-1">
        <div>
          <span className="text-[11px] font-bold text-samsung-blue uppercase tracking-wider block">
            Guided Plan ({goal.actions.length} {goal.actions.length === 1 ? "Action" : "Actions"})
          </span>
          <h3 className="text-base sm:text-lg font-bold text-white tracking-tight break-words">
            {goal.title}
          </h3>
        </div>

        <div className="flex items-center gap-2 bg-slate-900/80 border border-white/10 px-3 py-1.5 rounded-xl text-xs font-mono">
          <span className="text-slate-400">Confidence:</span>
          <span className="text-emerald-400 font-bold">{(goal.score * 100).toFixed(0)}% Calibrated</span>
        </div>
      </div>

      {/* Stack of Action Cards */}
      <div className="space-y-3.5">
        {goal.actions.map((action: ActionPayload, actionIdx: number) => {
          const category = action.category || "manual";
          const isAuto = category === "auto";
          const isManual = category === "manual";
          const isCritical = category === "critical";

          // Novelty N4 State Check: Is setting already active in simulated device?
          const hasValidation = action.stepGroups.some((sg) => sg.validationDeeplink);
          const isAdaptiveBrightnessActive = deviceState.adaptiveBrightness && action.actionName.toLowerCase().includes("brightness");
          const isPowerSavingActive = deviceState.powerSaving && action.actionName.toLowerCase().includes("power saving");
          const isAutoSkipped = hasValidation && (isAdaptiveBrightnessActive || isPowerSavingActive);

          return (
            <motion.div
              key={`${action.actionName}-${actionIdx}`}
              variants={itemVariants}
              initial="hidden"
              animate="visible"
              className={`glass-panel rounded-2xl p-4 sm:p-5 border transition-all ${
                isAutoSkipped
                  ? "border-emerald-500/30 bg-emerald-950/20"
                  : isCritical
                  ? "border-amber-500/20 hover:border-amber-500/40"
                  : "border-white/10 hover:border-white/20"
              }`}
            >
              {/* Card Header */}
              <div className="flex items-start justify-between gap-3 mb-2.5">
                <div className="flex items-center gap-2.5">
                  <span className="w-6 h-6 rounded-lg bg-white/10 text-white font-mono text-xs font-bold flex items-center justify-center">
                    0{actionIdx + 1}
                  </span>
                  <div>
                    <h4 className="font-bold text-white text-sm sm:text-base tracking-tight break-words">
                      {action.actionName}
                    </h4>
                    <p className="text-xs text-slate-300 italic">
                      {action.description}
                    </p>
                  </div>
                </div>

                {/* Category Badge */}
                <div className="flex-shrink-0">
                  {isAuto && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-[10px] font-bold uppercase tracking-wider">
                      <Cpu className="w-3 h-3" />
                      Auto
                    </span>
                  )}
                  {isManual && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-blue-500/15 border border-blue-500/30 text-blue-400 text-[10px] font-bold uppercase tracking-wider">
                      <Wrench className="w-3 h-3" />
                      Manual
                    </span>
                  )}
                  {isCritical && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-400 text-[10px] font-bold uppercase tracking-wider">
                      <AlertTriangle className="w-3 h-3" />
                      Critical
                    </span>
                  )}
                </div>
              </div>

              {/* Novelty N4 Auto-Skip Ribbon */}
              {isAutoSkipped && (
                <div className="my-2.5 px-3 py-2 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center gap-2 text-xs text-emerald-300">
                  <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <span className="font-semibold">
                    Novelty N4 Auto-Skip: Device state confirms setting is already active!
                  </span>
                </div>
              )}

              {/* Sub-Steps with Checkbox Interactivity */}
              <div className="space-y-2 mt-3 pt-2.5 border-t border-white/5">
                {action.stepGroups.map((sg, sgIdx) => (
                  <div key={sgIdx} className="space-y-2">
                    {sg.steps.map((stepText, stepIdx) => {
                      const stepKey = `${actionIdx}-${sgIdx}-${stepIdx}`;
                      const isDone = !!completedSteps[stepKey];

                      return (
                        <div
                          key={stepIdx}
                          onClick={() => toggleStep(stepKey)}
                          className={`flex items-start gap-2.5 p-2 rounded-lg cursor-pointer transition-colors text-xs sm:text-sm select-none ${
                            isDone ? "bg-white/5 text-slate-400 line-through" : "hover:bg-white/5 text-slate-200"
                          }`}
                        >
                          <div
                            className={`w-4 h-4 mt-0.5 rounded border flex items-center justify-center flex-shrink-0 transition-colors ${
                              isDone ? "bg-samsung-blue border-samsung-blue text-white" : "border-slate-500 bg-slate-900"
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

                    {/* Actionable Deeplink Hero Trigger */}
                    {sg.actionableDeeplink && (
                      <div className="pt-2 flex flex-wrap items-center gap-2">
                        <button
                          onClick={() => {
                            const target = action.actionName.toLowerCase().includes("battery") ? "battery" : "display";
                            onTriggerDeeplink(sg.actionableDeeplink!.deeplink, target);
                          }}
                          className="flex items-center gap-2 px-4 py-2.5 min-h-[44px] rounded-xl bg-samsung-blue hover:bg-blue-600 text-white font-semibold text-xs transition-all active:scale-95 shadow-blue-glow"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          <span>{sg.actionableDeeplink.message || "Open Device Settings"}</span>
                        </button>

                        <button
                          onClick={() => handleCopy(sg.actionableDeeplink!.deeplink)}
                          className="p-2.5 min-h-[44px] rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-white/10 transition-all text-xs flex items-center gap-1.5"
                          title="Copy Bixby Deeplink URI"
                        >
                          {copiedLink === sg.actionableDeeplink.deeplink ? (
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                          <span className="font-mono text-[10px] hidden sm:inline truncate max-w-[120px]">
                            {sg.actionableDeeplink.deeplink}
                          </span>
                        </button>
                      </div>
                    )}
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
