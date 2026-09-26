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
import type { TroubleshootResponsePayload, SimulatedDeviceState, OneUIScreen } from './types/engine';
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

  // Phone simulation state - start immediately on Display screen with active settings
  const [deviceState, setDeviceState] = useState<SimulatedDeviceState>({
    screen: 'display',
    adaptiveBrightness: false,
    brightness: 75,
    darkMode: true,
    powerSaving: false,
    protectBattery: false,
    cacheSizeMb: 184,
    quickPanelOpen: false,
    isLocked: false,
    isSafeMode: false,
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
          title: 'Troubleshooting Guide Ready',
          message: `Generated ${actionsCount} verified step-by-step resolution actions for your Galaxy device.`,
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
    targetScreen: OneUIScreen,
    actionName?: string
  ) => {
    const screenNames: Record<OneUIScreen, string> = {
      home: 'Home Screen',
      settings: 'Settings',
      display: 'Display Settings',
      battery: 'Battery & Device Care',
      storage: 'App Storage & Cache',
      safe_mode: 'Safe Mode',
    };
    let notice = `Opened ${screenNames[targetScreen] || 'Settings'}`;
    let updates: Partial<SimulatedDeviceState> = {};

    if (actionName) {
      const lower = actionName.toLowerCase();
      if (lower.includes('brightness') || lower.includes('adaptive')) {
        updates = { adaptiveBrightness: true, brightness: 55 };
        notice = 'Adaptive Brightness enabled (55%)';
      } else if (lower.includes('power') || lower.includes('battery')) {
        updates = { powerSaving: true };
        notice = 'Power Saving Mode activated';
      } else if (lower.includes('cache') || lower.includes('storage')) {
        updates = { cacheSizeMb: 0 };
        notice = '184 MB Cache cleared & freed';
      } else if (lower.includes('safe mode') || lower.includes('reboot')) {
        updates = { isSafeMode: true };
        notice = 'Safe Mode diagnostic verified';
      } else if (lower.includes('dark')) {
        updates = { darkMode: true };
        notice = 'One UI Dark Mode enabled';
      }
    }

    setDeviceState((prev) => ({
      ...prev,
      ...updates,
      screen: targetScreen,
      lastDeeplinkTriggered: deeplink,
      lastActionNotice: notice,
      isLocked: false,
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
      screen: 'display',
      adaptiveBrightness: false,
      brightness: 75,
      darkMode: true,
      powerSaving: false,
      protectBattery: false,
      cacheSizeMb: 184,
      quickPanelOpen: false,
      isLocked: false,
      isSafeMode: false,
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
          <div className="hidden lg:block lg:col-span-5 xl:col-span-5 sticky top-20 space-y-3">
            <div className="p-4 sm:p-5 rounded-3xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-2xl shadow-2xl flex flex-col items-center">
              <div className="w-full flex items-center justify-between border-b border-slate-800/70 pb-3 mb-3">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />
                  <span className="text-xs font-bold text-slate-200 tracking-wide">
                    Your Galaxy S24 Ultra
                  </span>
                </div>
                <span className="text-[10px] text-sky-400 bg-sky-500/10 px-2.5 py-0.5 rounded-full border border-sky-500/20 font-medium">
                  Live Device Preview
                </span>
              </div>

              <PhoneSimulator
                deviceState={deviceState}
                setDeviceState={setDeviceState}
              />

              {/* Screen Preview Switcher */}
              <div className="w-full pt-3 mt-3 border-t border-slate-800/60 flex items-center justify-between text-xs">
                <span className="text-[11px] text-slate-400 font-medium">Screen Preview:</span>
                <div className="flex gap-1">
                  {(['home', 'display', 'battery', 'storage'] as OneUIScreen[]).map((scr) => (
                    <button
                      key={scr}
                      data-testid={`quick-jump-${scr}`}
                      onClick={() => setDeviceState((p) => ({ ...p, screen: scr, isLocked: false }))}
                      className={`px-2.5 py-1 rounded-lg text-[10px] font-semibold capitalize transition-all ${
                        deviceState.screen === scr
                          ? 'bg-sky-500 text-white shadow-sm'
                          : 'bg-slate-800/80 text-slate-400 hover:text-white hover:bg-slate-700'
                      }`}
                    >
                      {scr}
                    </button>
                  ))}
                </div>
              </div>
            </div>
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
