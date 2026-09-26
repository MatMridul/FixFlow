import React from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, Home, RotateCcw } from 'lucide-react';
import { springs } from '../theme/motion';

interface NotFoundProps {
  onReturnHome: () => void;
}

export const NotFound: React.FC<NotFoundProps> = ({ onReturnHome }) => {
  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={springs.responsive}
        className="max-w-md w-full bg-slate-900/80 border border-slate-800 rounded-3xl p-8 backdrop-blur-xl shadow-2xl text-center"
      >
        <div className="w-16 h-16 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center mx-auto mb-6">
          <AlertCircle className="w-8 h-8 text-rose-400" />
        </div>

        <span className="text-xs font-semibold tracking-wider text-rose-400 uppercase bg-rose-500/10 px-3 py-1 rounded-full border border-rose-500/20">
          Page Not Found · Error 404
        </span>

        <h2 className="text-2xl font-bold text-slate-100 tracking-tight mt-4">
          Troubleshooting Guide Not Found
        </h2>

        <p className="text-xs text-slate-400 mt-2 leading-relaxed">
          The requested Galaxy support topic or page does not exist or may have been moved.
          Try searching for your symptom from the main support assistant.
        </p>

        <div className="mt-8 flex flex-col sm:flex-row gap-3">
          <button
            type="button"
            onClick={onReturnHome}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-sky-500 hover:from-blue-500 hover:to-sky-400 text-white text-xs font-semibold shadow-lg shadow-blue-500/20 transition-all"
          >
            <Home className="w-4 h-4" />
            <span>Return to Support</span>
          </button>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700/80 text-slate-300 hover:bg-slate-800 text-xs font-medium transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reload</span>
          </button>
        </div>
      </motion.div>
    </div>
  );
};
