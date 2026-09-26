/**
 * FixFlow Motion Design Tokens & Physics Curves
 * Precision-tuned spring physics and choreographed transitions
 * Inspired by Samsung One UI 6.1 fluid dynamics and Linear luxury motion.
 */

import type { Transition, Variants } from "framer-motion";

export const EASE_DECISIVE = [0.16, 1, 0.3, 1] as const;
export const EASE_OUT_EXPO = [0.19, 1, 0.22, 1] as const;

export const MOTION_TOKENS = {
  easeDecisive: EASE_DECISIVE,
  easeOutExpo: EASE_OUT_EXPO,

  // Snappy spring for cards, buttons, dialogs
  springSnappy: {
    type: "spring" as const,
    stiffness: 420,
    damping: 32,
    mass: 0.8,
  },

  // Smooth fluid spring for phone screen navigation and sliding drawers
  springFluid: {
    type: "spring" as const,
    stiffness: 280,
    damping: 28,
    mass: 0.9,
  },

  // Subtle spring for layout pills and sliding indicator chips
  springPill: {
    type: "spring" as const,
    stiffness: 500,
    damping: 35,
  },

  staggerDelay: 0.045,
  delayChildren: 0.05,
};

export const springs = {
  snappy: MOTION_TOKENS.springSnappy,
  fluid: MOTION_TOKENS.springFluid,
  pill: MOTION_TOKENS.springPill,
  responsive: MOTION_TOKENS.springSnappy,
  slide: MOTION_TOKENS.springFluid,
};

export const transitions = {
  fadeSlide: {
    duration: 0.24,
    ease: EASE_DECISIVE,
  } satisfies Transition,
  screenSlide: {
    duration: 0.22,
    ease: EASE_DECISIVE,
  } satisfies Transition,
};

// Container stagger variants for list of action cards
export const listContainerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: MOTION_TOKENS.staggerDelay,
      delayChildren: MOTION_TOKENS.delayChildren,
    },
  },
};

// Cascading card item entry
export const cardItemVariants: Variants = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: springs.snappy,
  },
};

// Interactive button micro-states
export const microInteractions = {
  tap: { scale: 0.97 },
  hoverCard: { y: -1, transition: { duration: 0.15 } },
  hoverButton: { scale: 1.015, transition: { duration: 0.12 } },
};
