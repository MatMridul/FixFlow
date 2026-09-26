import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, HelpCircle, ArrowRight, RefreshCw, ThumbsUp, ThumbsDown } from 'lucide-react';
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
      title: 'Issue Resolved',
      message: 'Galaxy device settings have been successfully calibrated.',
      duration: 5000,
    });

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
        colors: ['#1E56FF', '#2F68FD', '#10B981', '#3B82F6'],
      });
      confetti({
        ...defaults,
        particleCount,
        origin: { x: 0.7, y: 0.7 },
        colors: ['#1E56FF', '#2F68FD', '#10B981', '#3B82F6'],
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
    <div className="bg-[#13151A] border border-white/[0.07] rounded-xl p-4 sm:p-5 mt-4 space-y-3">
      <div className="flex items-center justify-between pb-2.5 border-b border-white/[0.05]">
        <h3 className="text-xs font-semibold text-zinc-200 tracking-wide uppercase">
          Resolution Verification
        </h3>
        <span className="text-[11px] text-zinc-400 font-mono">One UI Self-Care</span>
      </div>

      <div>
        {resolvedStatus === 'idle' && (
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-3.5 rounded-lg bg-[#0E1013] border border-white/[0.05]">
            <div>
              <p className="text-xs font-medium text-zinc-200">Did these steps resolve your issue?</p>
              <p className="text-[11px] text-zinc-400 mt-0.5">
                Confirm whether your Galaxy device is working normally.
              </p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={handleResolved}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/25 text-xs font-medium transition-all"
              >
                <ThumbsUp className="w-3.5 h-3.5" />
                <span>Yes, fixed!</span>
              </button>
              <button
                type="button"
                onClick={handleUnresolved}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#191C23] border border-white/[0.07] text-zinc-300 hover:bg-[#20242D] text-xs font-medium transition-all"
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
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={springs.responsive}
              className="p-3.5 rounded-lg bg-emerald-950/20 border border-emerald-500/30 text-emerald-200 flex items-center justify-between"
            >
              <div className="flex items-center gap-2.5">
                <div className="p-1.5 rounded-md bg-emerald-500/20 text-emerald-400">
                  <Check className="w-4 h-4" />
                </div>
                <div>
                  <h4 className="text-xs font-semibold text-emerald-300">Issue Resolved</h4>
                  <p className="text-[11px] text-emerald-400/80 mt-0.5">
                    Your Galaxy device settings are now restored to optimal condition.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setResolvedStatus('idle')}
                className="text-xs text-zinc-400 hover:text-zinc-200 underline font-mono ml-4"
              >
                Reset
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {resolvedStatus === 'unresolved' && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={springs.responsive}
            className="mt-2.5 space-y-2.5"
          >
            <div className="p-2.5 rounded-lg bg-amber-950/20 border border-amber-500/30 text-amber-200 text-xs flex items-center gap-2">
              <HelpCircle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
              <span>Select a follow-up symptom below or describe your condition:</span>
            </div>

            <div className="flex flex-wrap gap-1.5">
              {[
                'Overheating only while charging',
                'Screen freezes even in Safe Mode',
                'Bluetooth disconnects in car audio',
                'Camera lags in low light',
                'Battery drains overnight with AOD off',
              ].map((chip) => (
                <button
                  key={chip}
                  type="button"
                  onClick={() => handleQuickFollowup(chip)}
                  className="text-xs px-2.5 py-1 rounded-md bg-[#191C23] border border-white/[0.06] text-zinc-300 hover:text-white hover:border-white/[0.12] hover:bg-[#20242D] transition-all text-left"
                >
                  + {chip}
                </button>
              ))}
            </div>
          </motion.div>
        )}

        {/* Freeform follow-up input */}
        <form onSubmit={handleSubmit} className="mt-3 flex gap-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Clarify symptoms (e.g., 'Only happens when 5G is active')..."
            disabled={isProcessing}
            className="flex-1 bg-[#0E1013] border border-white/[0.08] rounded-lg px-3 py-2 text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none focus:border-[#1E56FF] transition-all"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isProcessing}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-[#1E56FF] hover:bg-[#2F68FD] disabled:opacity-40 disabled:pointer-events-none text-white text-xs font-medium transition-all shrink-0"
          >
            {isProcessing ? (
              <RefreshCw className="w-3 h-3 animate-spin" />
            ) : (
              <>
                <span>Refine</span>
                <ArrowRight className="w-3 h-3" />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
