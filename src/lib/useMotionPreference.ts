import { useReducedMotion } from 'framer-motion'
import type { Variants } from 'framer-motion'
import { still } from './motion'

/**
 * Returns the given variants, or an inert set when the user prefers reduced
 * motion. Call this rather than reading `useReducedMotion` at every call site.
 */
export function useVariants(variants: Variants): Variants {
  const shouldReduce = useReducedMotion()
  return shouldReduce ? still : variants
}

export { useReducedMotion }
