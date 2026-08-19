import { motion, useScroll, useSpring } from 'framer-motion'

/**
 * Hairline bar pinned to the top of the viewport that tracks read progress.
 * `useSpring` smooths the raw scroll value so the bar glides instead of jitters.
 */
export function ScrollProgress() {
  const { scrollYProgress } = useScroll()
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 120,
    damping: 30,
    restDelta: 0.001,
  })

  return (
    <motion.div
      style={{ scaleX }}
      className="fixed inset-x-0 top-0 z-50 h-0.5 origin-left bg-gradient-to-r from-accent to-accent-warm"
      aria-hidden
    />
  )
}
