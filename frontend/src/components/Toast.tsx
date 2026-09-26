import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertTriangle, XCircle, Info, X } from 'lucide-react';
import { springs } from '../theme/motion';
import { ToastContext } from '../context/ToastContextInstance';
import type { ToastMessage } from '../context/ToastContextInstance';

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(
    ({ type, title, message, duration = 4000 }: Omit<ToastMessage, 'id'>) => {
      const id = Math.random().toString(36).substring(2, 9);
      setToasts((prev) => [...prev, { id, type, title, message, duration }]);

      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }
    },
    [removeToast]
  );

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <div
        aria-live="polite"
        className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none px-4 sm:px-0"
      >
        <AnimatePresence mode="popLayout">
          {toasts.map((toast) => {
            const icons = {
              success: <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />,
              error: <XCircle className="w-5 h-5 text-rose-400 shrink-0" />,
              warning: <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />,
              info: <Info className="w-5 h-5 text-sky-400 shrink-0" />,
            };

            const borderColors = {
              success: 'border-emerald-500/30 bg-emerald-950/80 text-emerald-100',
              error: 'border-rose-500/30 bg-rose-950/80 text-rose-100',
              warning: 'border-amber-500/30 bg-amber-950/80 text-amber-100',
              info: 'border-sky-500/30 bg-sky-950/80 text-sky-100',
            };

            return (
              <motion.div
                key={toast.id}
                layout
                initial={{ opacity: 0, y: -20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.15 } }}
                transition={springs.responsive}
                className={`pointer-events-auto flex items-start gap-3 p-3.5 rounded-xl border shadow-xl backdrop-blur-md ${borderColors[toast.type]}`}
                role="alert"
              >
                <div className="mt-0.5">{icons[toast.type]}</div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-xs font-semibold tracking-wide uppercase">{toast.title}</h4>
                  {toast.message && (
                    <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">{toast.message}</p>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => removeToast(toast.id)}
                  className="text-slate-400 hover:text-white p-1 rounded-md transition-colors"
                  aria-label="Dismiss notification"
                >
                  <X className="w-4 h-4" />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
};
