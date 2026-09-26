/**
 * Synchronized Ecosystem Physics & Motion Tokens
 * Enforces a single global spring curve family and coordinated stagger timing.
 */

export const MOTION_TOKENS = {
  // Decisive Cubic-Bezier (smooth deceleration, zero rubber bounce)
  easeDecisive: [0.16, 1, 0.3, 1] as const,

  // Snappy Spring for layout transitions & card reveals
  springSnappy: {
    type: "spring" as const,
    stiffness: 420,
    damping: 34,
    mass: 0.8,
  },

  // Gentle Spring for phone simulator screen sliding
  springScreenSlide: {
    type: "spring" as const,
    stiffness: 300,
    damping: 30,
    mass: 1.0,
  },

  // Stagger intervals between cascading action cards
  staggerCardDelay: 0.04,

  // Micro-interaction durations (seconds)
  durationFast: 0.16,
  durationNormal: 0.28,
};

export const springs = {
  responsive: MOTION_TOKENS.springSnappy,
  slide: MOTION_TOKENS.springScreenSlide,
};

export const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: MOTION_TOKENS.staggerCardDelay,
      delayChildren: 0.05,
    },
  },
};

export const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: {
    opacity: 1,
    y: 0,
    transition: MOTION_TOKENS.springSnappy,
  },
};
