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
    ({ type, title, message, duration = 3000 }: Omit<ToastMessage, 'id'>) => {
      const id = Math.random().toString(36).substring(2, 9);
      setToasts((prev) => [...prev.slice(-1), { id, type, title, message, duration }]);

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
        className="fixed bottom-6 left-6 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none px-4 sm:px-0"
      >
        <AnimatePresence mode="popLayout">
          {toasts.map((toast) => {
            const icons = {
              success: <CheckCircle2 className="w-4 h-4 text-white shrink-0" />,
              error: <XCircle className="w-4 h-4 text-white shrink-0" />,
              warning: <AlertTriangle className="w-4 h-4 text-white shrink-0" />,
              info: <Info className="w-4 h-4 text-white shrink-0" />,
            };

            return (
              <motion.div
                key={toast.id}
                layout
                initial={{ opacity: 0, y: 16, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.15 } }}
                transition={springs.responsive}
                className="pointer-events-auto flex items-start gap-3 p-3.5 rounded-lg border border-white/20 bg-[#111111] text-white shadow-2xl backdrop-blur-md"
                role="alert"
              >
                <div className="mt-0.5">{icons[toast.type]}</div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-xs font-semibold tracking-wide uppercase text-white">{toast.title}</h4>
                  {toast.message && (
                    <p className="text-xs text-neutral-400 mt-0.5 leading-relaxed">{toast.message}</p>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => removeToast(toast.id)}
                  className="text-neutral-400 hover:text-white p-1 rounded transition-colors cursor-pointer"
                  aria-label="Dismiss notification"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
};
