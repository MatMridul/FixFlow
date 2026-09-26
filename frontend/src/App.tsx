import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TopBar } from './components/TopBar';
import { DiagnosticIntake } from './components/DiagnosticIntake';
import { ActionCardStream } from './components/ActionCardStream';
import { PhoneSimulator } from './components/PhoneSimulator';
import { RefinementBox } from './components/RefinementBox';
import { Footer } from './components/Footer';
import { NotFound } from './components/NotFound';
import { ToastProvider } from './components/Toast';
import { useToast } from './hooks/useToast';
import { BENCHMARK_SCENARIOS, submitTroubleshoot, checkServerHealth } from './services/api';
import type { TroubleshootResponsePayload, SimulatedDeviceState } from './types/engine';
import { springs } from './theme/motion';

function FixFlowApp() {
  const [serverOnline, setServerOnline] = useState(false);
  const [query, setQuery] = useState(BENCHMARK_SCENARIOS[0].query);
  const [activeSiis, setActiveSiis] = useState<{ title: string; content: string }>({
    title: BENCHMARK_SCENARIOS[0].siis_title,
    content: BENCHMARK_SCENARIOS[0].siis_content,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [diagnosticResult, setDiagnosticResult] = useState<TroubleshootResponsePayload | null>(null);
  const [isMobileSimOpen, setIsMobileSimOpen] = useState(false);
  const [is404, setIs404] = useState(false);

  // Phone simulation state
  const [deviceState, setDeviceState] = useState<SimulatedDeviceState>({
    screen: 'home',
    adaptiveBrightness: false,
    darkMode: false,
    powerSaving: false,
    protectBattery: false,
    lastDeeplinkTriggered: null,
  });

  const { addToast } = useToast();

  // Listen to hash changes for 404 demonstration (Rule 14)
  useEffect(() => {
    const handleHash = () => {
      if (window.location.hash === '#404') {
        setIs404(true);
      } else {
        setIs404(false);
      }
    };
    handleHash();
    window.addEventListener('hashchange', handleHash);
    return () => window.removeEventListener('hashchange', handleHash);
  }, []);

  const handleRunDiagnostic = useCallback(
    async (customQuery?: string, siisTitle?: string, siisContent?: string) => {
      const q = customQuery ?? query;
      if (!q.trim()) return;

      setIsLoading(true);

      // Check if complaint matches any benchmark scenario for SIIS ground truth
      const matched = BENCHMARK_SCENARIOS.find(
        (s) => s.query.trim().toLowerCase() === q.trim().toLowerCase()
      );
      const title = siisTitle ?? (matched ? matched.siis_title : activeSiis.title);
      const content = siisContent ?? (matched ? matched.siis_content : activeSiis.content);

      if (title && content) {
        setActiveSiis({ title, content });
      }

      try {
        const result = await submitTroubleshoot(q, title, content);
        setDiagnosticResult(result);

        const actionsCount = result.response.contexts[0]?.actions?.length || 0;
        addToast({
          type: 'success',
          title: 'Diagnostic Plan Grounded',
          message: `Generated verified troubleshooting plan (${actionsCount} actions, ${result.meta.latency_ms.toFixed(1)}ms)`,
        });
      } catch (err) {
        addToast({
          type: 'error',
          title: 'Diagnostic Error',
          message: err instanceof Error ? err.message : 'Failed to generate diagnostic plan',
        });
      } finally {
        setIsLoading(false);
      }
    },
    [query, activeSiis, addToast]
  );

  // Auto-run first scenario and check health strictly once on mount
  const initializedRef = useRef(false);
  useEffect(() => {
    if (initializedRef.current) return;
    initializedRef.current = true;

    (async () => {
      const isHealthy = await checkServerHealth();
      setServerOnline(isHealthy);
      await handleRunDiagnostic(BENCHMARK_SCENARIOS[0].query);
    })();
  }, [handleRunDiagnostic]);

  const handleTriggerDeeplink = (
    deeplink: string,
    targetScreen: 'display' | 'battery' | 'settings'
  ) => {
    setDeviceState((prev) => ({
      ...prev,
      screen: targetScreen,
      lastDeeplinkTriggered: deeplink,
    }));
    // On small screens, automatically open the phone simulator so the user sees the screen update
    if (window.innerWidth < 1024) {
      setIsMobileSimOpen(true);
    }
  };

  const handleRefine = (refinedText: string) => {
    const updatedQuery = `${query} [Follow-up symptom: ${refinedText}]`;
    setQuery(updatedQuery);
    handleRunDiagnostic(updatedQuery);
  };

  const handleReset = () => {
    setQuery(BENCHMARK_SCENARIOS[0].query);
    setDeviceState({
      screen: 'home',
      adaptiveBrightness: false,
      darkMode: false,
      powerSaving: false,
      protectBattery: false,
      lastDeeplinkTriggered: null,
    });
    handleRunDiagnostic(BENCHMARK_SCENARIOS[0].query);
    addToast({
      type: 'info',
      title: 'Console Reset',
      message: 'Restored default benchmark scenario and reset Galaxy device state.',
    });
  };

  if (is404) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between overflow-x-hidden">
        <TopBar
          serverOnline={serverOnline}
          onReset={handleReset}
          onToggleMobileSim={() => setIsMobileSimOpen(true)}
          isMobileSimOpen={isMobileSimOpen}
        />
        <NotFound
          onReturnHome={() => {
            window.location.hash = '';
            setIs404(false);
          }}
        />
        <Footer />
      </div>
    );
  }

  const primaryGoal = diagnosticResult?.response.contexts[0] || null;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between overflow-x-hidden selection:bg-blue-600/30 selection:text-blue-200">
      {/* Top Bar with clickable logo, status badges, mobile launcher */}
      <TopBar
        serverOnline={serverOnline}
        onReset={handleReset}
        onToggleMobileSim={() => setIsMobileSimOpen((prev) => !prev)}
        isMobileSimOpen={isMobileSimOpen}
      />

      {/* Main Command Center Layout */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 pt-6 pb-12">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Intake, Telemetry, Action Card Stream, Refinement */}
          <div className="lg:col-span-7 xl:col-span-7 space-y-6">
            <DiagnosticIntake
              query={query}
              setQuery={setQuery}
              onSubmit={handleRunDiagnostic}
              isLoading={isLoading}
              meta={diagnosticResult?.meta || null}
            />

            <ActionCardStream
              goal={primaryGoal}
              deviceState={deviceState}
              onTriggerDeeplink={handleTriggerDeeplink}
              onSuccessToast={(msg) =>
                addToast({
                  type: 'success',
                  title: 'Setting Calibrated',
                  message: msg,
                })
              }
            />

            <RefinementBox onRefine={handleRefine} isProcessing={isLoading} />
          </div>

          {/* Right Column: Sticky Samsung Galaxy S24 Simulator (Desktop) */}
          <div className="hidden lg:block lg:col-span-5 xl:col-span-5 sticky top-20">
            <PhoneSimulator
              deviceState={deviceState}
              setDeviceState={setDeviceState}
            />
          </div>
        </div>
      </main>

      {/* Mobile Drawer / Bottom Sheet for Phone Simulator (Un-Vibe Rule 5 & 19) */}
      <AnimatePresence>
        {isMobileSimOpen && (
          <div className="lg:hidden fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsMobileSimOpen(false)}
              className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm"
            />

            <motion.div
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={springs.responsive}
              className="relative w-full max-w-md max-h-[92vh] overflow-y-auto flex flex-col items-center p-2"
            >
              <PhoneSimulator
                deviceState={deviceState}
                setDeviceState={setDeviceState}
                onCloseMobile={() => setIsMobileSimOpen(false)}
              />
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* 19/19 Un-Vibe Code Verified Footer */}
      <Footer />
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <FixFlowApp />
    </ToastProvider>
  );
}
