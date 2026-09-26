/**
 * FixFlow TypeScript Contracts — 1:1 parity with schema.py & api/models.py
 */

export type ActionCategory = "auto" | "manual" | "critical";

export interface DeeplinkPayload {
  deeplink: string;
  description: string;
  message?: string;
  classes?: Record<string, string> | null;
  originalType?: string | null;
}

export interface ValidationDeeplinkPayload {
  deeplink: string;
  key: string;
  resultType?: "boolean" | "integer" | "str" | "float" | null;
  condition?: "greater" | "equal" | "less" | null;
  value?: string | null;
  inferred?: boolean;
}

export interface StepGroupPayload {
  steps: string[];
  actionableDeeplink?: DeeplinkPayload | null;
  validationDeeplink?: ValidationDeeplinkPayload | null;
}

export interface ActionPayload {
  actionName: string;
  description: string;
  stepGroups: StepGroupPayload[];
  category?: ActionCategory;
}

export interface GoalPayload {
  goal: string;
  title: string;
  actions: ActionPayload[];
  score: number;
}

export interface ContextDeeplinkResponsePayload {
  contexts: GoalPayload[];
}

export interface MetaPayload {
  latency_ms: number;
  cache_hit: boolean;
  model: string;
  cost_usd: number;
  fallback?: "no_siis_context" | "no_match" | null;
}

export interface TroubleshootResponsePayload {
  query: string;
  response: ContextDeeplinkResponsePayload;
  meta: MetaPayload;
}

export type OneUIScreen = "home" | "settings" | "display" | "battery" | "storage" | "safe_mode";

export interface SimulatedDeviceState {
  screen: OneUIScreen;
  adaptiveBrightness: boolean;
  brightness: number;
  darkMode: boolean;
  powerSaving: boolean;
  protectBattery: boolean;
  cacheSizeMb: number;
  quickPanelOpen: boolean;
  isLocked: boolean;
  isSafeMode: boolean;
  lastDeeplinkTriggered: string | null;
  lastActionNotice?: string | null;
  targetHighlight?: string | null;
  isSimulating?: boolean;
}

