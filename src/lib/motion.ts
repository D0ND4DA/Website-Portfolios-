import type { Transition, Variants } from 'framer-motion'

/**
 * Shared motion vocabulary. Components import from here instead of inventing
 * their own timings, so every animation on the site feels like one system.
 */

/** Springy but settled — the default for anything that moves into place. */
export const ease: Transition = {
  type: 'spring',
  stiffness: 260,
  damping: 30,
  mass: 0.8,
}

/** Short, linear-ish transition for hover/tap affordances. */
export const snap: Transition = {
  type: 'spring',
  stiffness: 500,
  damping: 32,
}

/** Parent that releases its children one after another. */
export const stagger = (staggerChildren = 0.08, delayChildren = 0): Variants => ({
  hidden: {},
  visible: {
    transition: { staggerChildren, delayChildren },
  },
})

/** The workhorse child variant: fade up into place. */
export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: ease },
}

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.5 } },
}

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.94 },
  visible: { opacity: 1, scale: 1, transition: ease },
}

/** Per-character/word entrance, used by <AnimatedText />. */
export const textChild: Variants = {
  hidden: { opacity: 0, y: '0.6em' },
  visible: { opacity: 1, y: '0em', transition: { ...ease, damping: 24 } },
}

/**
 * Variants that collapse to a no-op. Swapped in when the user has asked for
 * reduced motion, so elements appear instantly instead of sliding.
 */
export const still: Variants = {
  hidden: { opacity: 1 },
  visible: { opacity: 1 },
}
