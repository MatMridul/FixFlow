import React, { useState } from "react";
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
    <div className="w-full space-y-3">
      {/* Plan Header */}
      <div className="p-4 rounded-xl bg-[#13151A] border border-white/[0.07] space-y-2.5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#1E56FF]" />
              <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider block">
                Guided Plan ({goal.actions.length} {goal.actions.length === 1 ? "Action" : "Actions"})
              </span>
            </div>
            <h3 className="text-sm sm:text-base font-semibold text-white tracking-tight mt-0.5">
              {goal.title}
            </h3>
          </div>

          <div className="flex items-center gap-1.5 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-md text-xs text-emerald-400 font-medium">
            <CheckCircle className="w-3.5 h-3.5" />
            <span>Verified Resolution</span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-1 pt-2 border-t border-white/[0.05]">
          <div className="flex justify-between text-[11px] text-zinc-400">
            <span>Troubleshooting Progress</span>
            <span className="font-mono text-zinc-200">{progressPercent}% Completed</span>
          </div>
          <div className="w-full h-1 rounded-full bg-[#0E1013] overflow-hidden">
            <div
              className="h-full bg-[#1E56FF] rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Action Cards Stream */}
      <div className="space-y-2.5">
        {goal.actions.map((action, actionIdx) => {
          const targetScreen = inferTargetScreen(action);
          const isCurrentScreen = deviceState.screen === targetScreen;
          const isAutoSkipped = action.actionName.toLowerCase().includes("brightness") && deviceState.adaptiveBrightness;

          return (
            <div
              key={actionIdx}
              className={`p-4 rounded-xl border transition-all ${
                isCurrentScreen
                  ? "bg-[#13151A] border-[#1E56FF]/40 shadow-sm"
                  : "bg-[#13151A] border-white/[0.07] hover:border-white/[0.12]"
              }`}
            >
              {/* Card Header */}
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div
                    className={`w-6 h-6 rounded-md flex items-center justify-center font-mono text-xs font-semibold shrink-0 mt-0.5 ${
                      isCurrentScreen
                        ? "bg-[#1E56FF] text-white"
                        : "bg-[#191C23] text-zinc-400 border border-white/[0.06]"
                    }`}
                  >
                    {String(actionIdx + 1).padStart(2, "0")}
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-white tracking-tight">
                      {action.actionName}
                    </h4>
                    <p className="text-xs text-zinc-400 mt-0.5 leading-relaxed">
                      {action.description}
                    </p>
                  </div>
                </div>

                <div className="text-[11px] font-mono text-zinc-400 bg-[#191C23] px-2 py-0.5 rounded border border-white/[0.05] shrink-0">
                  Step {actionIdx + 1}
                </div>
              </div>

              {/* Already Active Notice */}
              {isAutoSkipped && (
                <div className="my-2.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center gap-2 text-xs text-emerald-400">
                  <CheckCircle className="w-3.5 h-3.5 shrink-0" />
                  <span>Already Configured: Setting is active on your device.</span>
                </div>
              )}

              {/* Sub-Steps */}
              <div className="space-y-1.5 mt-3 pt-2.5 border-t border-white/[0.05]">
                {action.stepGroups.map((sg, sgIdx) => (
                  <div key={sgIdx} className="space-y-2">
                    {sg.steps.map((stepText, stepIdx) => {
                      const stepKey = `${actionIdx}-${sgIdx}-${stepIdx}`;
                      const isDone = !!completedSteps[stepKey];

                      return (
                        <div
                          key={stepIdx}
                          onClick={() => toggleStep(stepKey)}
                          className={`flex items-start gap-2 p-1.5 rounded-md cursor-pointer transition-colors text-xs select-none ${
                            isDone
                              ? "text-zinc-500 line-through bg-transparent"
                              : "hover:bg-[#191C23] text-zinc-300"
                          }`}
                        >
                          <div className="mt-0.5 shrink-0 text-zinc-400">
                            {isDone ? (
                              <CheckSquare className="w-3.5 h-3.5 text-emerald-400" />
                            ) : (
                              <Square className="w-3.5 h-3.5 text-zinc-500" />
                            )}
                          </div>
                          <span className="leading-relaxed">{stepText}</span>
                        </div>
                      );
                    })}

                    {/* Interactive "Simulate on Galaxy S24" and Deeplink Actions */}
                    <div className="pt-1.5 flex flex-wrap items-center gap-2">
                      <button
                        onClick={() => {
                          const deeplink = sg.actionableDeeplink?.deeplink || `settings://${targetScreen}`;
                          onTriggerDeeplink(deeplink, targetScreen, action.actionName);
                          onSuccessToast(`Applied "${action.actionName}" on your Galaxy`);
                        }}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#1E56FF] hover:bg-[#2F68FD] text-white font-medium text-xs transition-all active:scale-95 shadow-sm"
                      >
                        <Play className="w-3 h-3 fill-current" />
                        <span>Simulate on Galaxy S24</span>
                      </button>

                      {sg.actionableDeeplink && (
                        <>
                          <button
                            onClick={() => {
                              onTriggerDeeplink(sg.actionableDeeplink!.deeplink, targetScreen, action.actionName);
                            }}
                            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-[#191C23] hover:bg-[#20242D] text-zinc-300 text-xs border border-white/[0.07] transition-all"
                          >
                            <ExternalLink className="w-3 h-3 text-zinc-400" />
                            <span>{sg.actionableDeeplink.message || "Open in Settings"}</span>
                          </button>

                          <button
                            onClick={() => handleCopy(sg.actionableDeeplink!.deeplink)}
                            className="px-2 py-1.5 rounded-lg bg-[#191C23] hover:bg-[#20242D] text-zinc-400 hover:text-white border border-white/[0.07] transition-all text-xs flex items-center gap-1"
                            title="Copy Direct Settings Link"
                          >
                            {copiedLink === sg.actionableDeeplink.deeplink ? (
                              <>
                                <Check className="w-3 h-3 text-emerald-400" />
                                <span className="text-[11px] text-emerald-400">Copied</span>
                              </>
                            ) : (
                              <>
                                <Copy className="w-3 h-3" />
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
            </div>
          );
        })}
      </div>
    </div>
  );
};
