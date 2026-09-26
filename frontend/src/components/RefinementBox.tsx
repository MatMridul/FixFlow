import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, HelpCircle, ArrowRight, RefreshCw, ThumbsUp, ThumbsDown, Sparkles } from 'lucide-react';
import confetti from 'canvas-confetti';
import { springs } from '../theme/motion';
import { useToast } from '../hooks/useToast';

interface RefinementBoxProps {
  onRefine: (refinedText: string) => void;
  isProcessing?: boolean;
}

export const RefinementBox: React.FC<RefinementBoxProps> = ({ onRefine, isProcessing = false }) => {
  const [inputText, setInputText] = useState('');
  const [resolvedStatus, setResolvedStatus] = useState<'idle' | 'resolved' | 'unresolved'>('idle');
  const { addToast } = useToast();

  const handleResolved = () => {
    setResolvedStatus('resolved');
    addToast({
      type: 'success',
      title: 'Issue Resolved!',
      message: 'Great! Galaxy device settings have been successfully calibrated.',
      duration: 5000,
    });

    // Trigger sophisticated multi-burst celebration confetti
    const duration = 2.5 * 1000;
    const animationEnd = Date.now() + duration;
    const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 1000 };

    const interval: ReturnType<typeof setInterval> = setInterval(() => {
      const timeLeft = animationEnd - Date.now();
      if (timeLeft <= 0) {
        return clearInterval(interval);
      }
      const particleCount = 40 * (timeLeft / duration);
      confetti({
        ...defaults,
        particleCount,
        origin: { x: 0.3, y: 0.7 },
        colors: ['#2563EB', '#38BDF8', '#10B981', '#6366F1'],
      });
      confetti({
        ...defaults,
        particleCount,
        origin: { x: 0.7, y: 0.7 },
        colors: ['#2563EB', '#38BDF8', '#10B981', '#6366F1'],
      });
    }, 250);
  };

  const handleUnresolved = () => {
    setResolvedStatus('unresolved');
    addToast({
      type: 'warning',
      title: 'Additional Diagnostics Needed',
      message: 'Select a follow-up symptom below or describe your condition for deeper analysis.',
      duration: 5000,
    });
  };

  const handleQuickFollowup = (text: string) => {
    setInputText(text);
    onRefine(text);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isProcessing) return;
    onRefine(inputText.trim());
    setInputText('');
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5 backdrop-blur-xl shadow-lg mt-6">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-sky-400" />
          <h3 className="text-sm font-semibold text-slate-100 tracking-wide">
            Feedback &amp; Multi-Turn Refinement
          </h3>
        </div>
        <span className="text-[11px] text-slate-400 font-mono">Interactive Loop</span>
      </div>

      <div className="mt-4">
        {resolvedStatus === 'idle' && (
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800/60">
            <div>
              <p className="text-xs font-medium text-slate-200">Did these steps resolve your issue?</p>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Confirming helps FixFlow tune safe diagnostic weights for Galaxy devices.
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={handleResolved}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20 text-xs font-medium transition-all"
              >
                <ThumbsUp className="w-3.5 h-3.5" />
                <span>Yes, fixed!</span>
              </button>
              <button
                type="button"
                onClick={handleUnresolved}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-slate-300 hover:bg-slate-800 text-xs font-medium transition-all"
              >
                <ThumbsDown className="w-3.5 h-3.5" />
                <span>Still having issues</span>
              </button>
            </div>
          </div>
        )}

        <AnimatePresence>
          {resolvedStatus === 'resolved' && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={springs.responsive}
              className="p-4 rounded-xl bg-emerald-950/30 border border-emerald-500/40 text-emerald-200 flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400">
                  <Check className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-emerald-300">Resolution Verified</h4>
                  <p className="text-[11px] text-emerald-400/80 mt-0.5">
                    Troubleshooting plan confirmed effective. All telemetry metrics verified.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setResolvedStatus('idle')}
                className="text-xs text-slate-400 hover:text-slate-200 underline font-mono ml-4"
              >
                Reset
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {resolvedStatus === 'unresolved' && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={springs.responsive}
            className="mt-3 space-y-3"
          >
            <div className="p-3 rounded-xl bg-amber-950/20 border border-amber-500/30 text-amber-200 text-xs flex items-center gap-2">
              <HelpCircle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>
                Let's narrow down the root cause. Select a symptom modifier below:
              </span>
            </div>

            <div className="flex flex-wrap gap-2">
              {[
                'Still overheating only while charging',
                'Screen freezes even in Safe Mode',
                'Bluetooth disconnects specifically in car audio',
                'Camera still lags in low light conditions',
                'Battery drains overnight with Always On Display off',
              ].map((chip) => (
                <button
                  key={chip}
                  type="button"
                  onClick={() => handleQuickFollowup(chip)}
                  className="text-xs px-2.5 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-slate-300 hover:text-sky-300 hover:border-sky-500/50 hover:bg-sky-500/10 transition-all text-left"
                >
                  + {chip}
                </button>
              ))}
            </div>
          </motion.div>
        )}

        {/* Freeform follow-up input */}
        <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Clarify symptoms (e.g., 'Only happens when 5G is active')..."
            disabled={isProcessing}
            className="flex-1 bg-slate-950/70 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500/60 focus:ring-1 focus:ring-sky-500/30 transition-all"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isProcessing}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 disabled:opacity-50 disabled:pointer-events-none text-white text-xs font-semibold shadow-md shadow-sky-500/20 transition-all shrink-0"
          >
            {isProcessing ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <>
                <span>Refine</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
