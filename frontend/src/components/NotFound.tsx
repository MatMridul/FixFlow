import React from 'react';
import { motion } from 'framer-motion';
import { AlertCircle, Home, RotateCcw } from 'lucide-react';
import { springs } from '../theme/motion';

interface NotFoundProps {
  onReturnHome: () => void;
}

export const NotFound: React.FC<NotFoundProps> = ({ onReturnHome }) => {
  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4 bg-black">
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={springs.responsive}
        className="max-w-md w-full bg-[#0D0D0D] border border-white/[0.1] rounded-xl p-6 sm:p-8 text-center"
      >
        <div className="w-12 h-12 rounded bg-white/10 border border-white/20 flex items-center justify-center mx-auto mb-4">
          <AlertCircle className="w-6 h-6 text-white" />
        </div>

        <span className="text-[11px] font-mono tracking-wider text-neutral-400 uppercase bg-[#161616] px-2.5 py-0.5 rounded border border-white/[0.1]">
          Error 404
        </span>

        <h2 className="text-xl font-semibold text-white tracking-tight mt-3">
          Troubleshooting Guide Not Found
        </h2>

        <p className="text-xs text-neutral-400 mt-2 leading-relaxed">
          The requested Galaxy support topic does not exist or may have been updated.
          Return to the main diagnostic console to search for your symptom.
        </p>

        <div className="mt-6 flex flex-col sm:flex-row gap-2.5">
          <button
            type="button"
            onClick={onReturnHome}
            className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2 rounded bg-white hover:bg-neutral-200 text-black text-xs font-semibold transition-all cursor-pointer"
          >
            <Home className="w-3.5 h-3.5" />
            <span>Return to Support</span>
          </button>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="flex items-center justify-center gap-1.5 px-4 py-2 rounded bg-[#161616] border border-white/[0.1] text-white hover:bg-[#222222] text-xs font-medium transition-all cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reload</span>
          </button>
        </div>
      </motion.div>
    </div>
  );
};
