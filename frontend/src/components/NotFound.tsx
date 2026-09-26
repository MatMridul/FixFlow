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
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={springs.responsive}
        className="max-w-md w-full bg-[#13151A] border border-white/[0.07] rounded-xl p-6 sm:p-8 text-center"
      >
        <div className="w-12 h-12 rounded-lg bg-rose-500/10 border border-rose-500/20 flex items-center justify-center mx-auto mb-4">
          <AlertCircle className="w-6 h-6 text-rose-400" />
        </div>

        <span className="text-[11px] font-mono tracking-wider text-rose-400 uppercase bg-rose-500/10 px-2.5 py-0.5 rounded border border-rose-500/20">
          Error 404
        </span>

        <h2 className="text-xl font-semibold text-white tracking-tight mt-3">
          Troubleshooting Guide Not Found
        </h2>

        <p className="text-xs text-zinc-400 mt-2 leading-relaxed">
          The requested Galaxy support topic does not exist or may have been updated.
          Return to the main diagnostic console to search for your symptom.
        </p>

        <div className="mt-6 flex flex-col sm:flex-row gap-2.5">
          <button
            type="button"
            onClick={onReturnHome}
            className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg bg-[#1E56FF] hover:bg-[#2F68FD] text-white text-xs font-medium transition-all"
          >
            <Home className="w-3.5 h-3.5" />
            <span>Return to Support</span>
          </button>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg bg-[#191C23] border border-white/[0.07] text-zinc-300 hover:bg-[#20242D] text-xs font-medium transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reload</span>
          </button>
        </div>
      </motion.div>
    </div>
  );
};
