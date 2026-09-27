import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ExternalLink,
  CheckCircle,
  Copy,
  Check,
  Play,
  CheckSquare,
  Square,
} from "lucide-react";
import type { ActionPayload, GoalPayload, SimulatedDeviceState, OneUIScreen } from "../types/engine";
import {
  listContainerVariants,
  cardItemVariants,
  springs,
  microInteractions,
} from "../theme/motion";

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
    onSuccessToast("Settings shortcut copied to clipboard");
    setTimeout(() => setCopiedLink(null), 2000);
  };

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
    <div className="w-full space-y-3">
      {/* Plan Header */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={springs.snappy}
        className="p-4 rounded-xl bg-[#080808] border border-white/[0.08] space-y-2.5"
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-white shadow-[0_0_6px_rgba(255,255,255,0.8)]" />
              <span className="text-[11px] font-semibold text-neutral-300 uppercase tracking-wider block">
                Guided Plan ({goal.actions.length} {goal.actions.length === 1 ? "Action" : "Actions"})
              </span>
            </div>
            <h3 className="text-sm sm:text-base font-semibold text-white tracking-tight mt-0.5">
              {goal.title}
            </h3>
          </div>

          <div className="flex items-center gap-1.5 bg-[#141414] border border-white/[0.12] px-2.5 py-1 rounded text-xs text-white font-medium">
            <CheckCircle className="w-3.5 h-3.5 text-white" />
            <span>Verified Resolution</span>
          </div>
        </div>

        {/* Animated Progress Bar */}
        <div className="space-y-1 pt-2 border-t border-white/[0.06]">
          <div className="flex justify-between text-[11px] text-neutral-400">
            <span>Troubleshooting Progress</span>
            <span className="font-mono text-white font-semibold">{progressPercent}% Completed</span>
          </div>
          <div className="w-full h-1.5 rounded-full bg-black border border-white/[0.06] overflow-hidden">
            <motion.div
              className="h-full bg-white rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progressPercent}%` }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
            />
          </div>
        </div>
      </motion.div>

      {/* Cascading Action Cards Stream with Stagger */}
      <motion.div
        variants={listContainerVariants}
        initial="hidden"
        animate="visible"
        key={goal.title}
        className="space-y-2.5"
      >
        {goal.actions.map((action, actionIdx) => {
          const targetScreen = inferTargetScreen(action);
          const isCurrentScreen = deviceState.screen === targetScreen;
          const isAutoSkipped = action.actionName.toLowerCase().includes("brightness") && deviceState.adaptiveBrightness;

          return (
            <motion.div
              key={actionIdx}
              variants={cardItemVariants}
              className={`p-4 rounded-xl border transition-all ${
                isCurrentScreen
                  ? "bg-[#0E0E0E] border-white ring-1 ring-white/20 shadow-[0_0_20px_-8px_rgba(255,255,255,0.2)]"
                  : "bg-[#080808] border-white/[0.08] hover:border-white/[0.18]"
              }`}
            >
              {/* Card Header */}
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div
                    className={`w-6 h-6 rounded flex items-center justify-center font-mono text-xs font-bold shrink-0 mt-0.5 transition-colors ${
                      isCurrentScreen
                        ? "bg-white text-black shadow-sm"
                        : "bg-[#181818] text-white border border-white/[0.08]"
                    }`}
                  >
                    {String(actionIdx + 1).padStart(2, "0")}
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-white tracking-tight">
                      {action.actionName}
                    </h4>
                    <p className="text-xs text-neutral-400 mt-0.5 leading-relaxed">
                      {action.description}
                    </p>
                  </div>
                </div>

                <div className="text-[11px] font-mono text-neutral-300 bg-[#121212] px-2 py-0.5 rounded border border-white/[0.08] shrink-0">
                  Step {actionIdx + 1}
                </div>
              </div>

              {/* Already Active Notice */}
              <AnimatePresence>
                {isAutoSkipped && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="my-2.5 px-3 py-1.5 rounded bg-[#141414] border border-white/[0.15] flex items-center gap-2 text-xs text-white">
                      <CheckCircle className="w-3.5 h-3.5 shrink-0 text-white" />
                      <span>Already Configured: Setting is active on your device.</span>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Sub-Steps */}
              <div className="space-y-1.5 mt-3 pt-2.5 border-t border-white/[0.06]">
                {action.stepGroups.map((sg, sgIdx) => (
                  <div key={sgIdx} className="space-y-2">
                    {sg.steps.map((stepText, stepIdx) => {
                      const stepKey = `${actionIdx}-${sgIdx}-${stepIdx}`;
                      const isDone = !!completedSteps[stepKey];

                      return (
                        <motion.div
                          key={stepIdx}
                          whileHover={{ x: 2 }}
                          onClick={() => toggleStep(stepKey)}
                          className={`flex items-start gap-2 p-1.5 rounded cursor-pointer transition-colors text-xs select-none ${
                            isDone
                              ? "text-neutral-500 line-through bg-transparent"
                              : "hover:bg-[#141414] text-neutral-200"
                          }`}
                        >
                          <div className="mt-0.5 shrink-0 text-neutral-400 transition-transform">
                            {isDone ? (
                              <CheckSquare className="w-3.5 h-3.5 text-white" />
                            ) : (
                              <Square className="w-3.5 h-3.5 text-neutral-600" />
                            )}
                          </div>
                          <span className="leading-relaxed">{stepText}</span>
                        </motion.div>
                      );
                    })}

                    {/* Interactive "Simulate on Galaxy S24" and Deeplink Actions */}
                    <div className="pt-1.5 flex flex-wrap items-center gap-2">
                      <motion.button
                        whileHover={microInteractions.hoverButton}
                        whileTap={microInteractions.tap}
                        onClick={() => {
                          const deeplink = sg.actionableDeeplink?.deeplink || `settings://${targetScreen}`;
                          onTriggerDeeplink(deeplink, targetScreen, action.actionName);
                          onSuccessToast(`Applied "${action.actionName}" on your Galaxy`);
                        }}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-white hover:bg-neutral-200 text-black font-semibold text-xs transition-colors active:scale-95 shadow-sm cursor-pointer"
                      >
                        <Play className="w-3 h-3 fill-current" />
                        <span>Simulate on Galaxy S24</span>
                      </motion.button>

                      {sg.actionableDeeplink && (
                        <>
                          <motion.button
                            whileHover={microInteractions.hoverButton}
                            whileTap={microInteractions.tap}
                            onClick={() => {
                              onTriggerDeeplink(sg.actionableDeeplink!.deeplink, targetScreen, action.actionName);
                            }}
                            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded bg-[#141414] hover:bg-[#1E1E1E] text-white text-xs border border-white/[0.1] transition-colors cursor-pointer"
                          >
                            <ExternalLink className="w-3 h-3 text-neutral-400" />
                            <span>{sg.actionableDeeplink.message || "Open in Settings"}</span>
                          </motion.button>

                          <motion.button
                            whileHover={microInteractions.hoverButton}
                            whileTap={microInteractions.tap}
                            onClick={() => handleCopy(sg.actionableDeeplink!.deeplink)}
                            className="px-2 py-1.5 rounded bg-[#141414] hover:bg-[#1E1E1E] text-neutral-400 hover:text-white border border-white/[0.1] transition-colors text-xs flex items-center gap-1 cursor-pointer"
                            title="Copy Direct Settings Link"
                          >
                            {copiedLink === sg.actionableDeeplink.deeplink ? (
                              <>
                                <Check className="w-3 h-3 text-white" />
                                <span className="text-[11px] text-white font-medium">Copied</span>
                              </>
                            ) : (
                              <>
                                <Copy className="w-3 h-3" />
                                <span className="text-[11px]">Copy Link</span>
                              </>
                            )}
                          </motion.button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
};
