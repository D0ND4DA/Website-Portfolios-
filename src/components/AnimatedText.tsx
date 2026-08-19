import { motion } from 'framer-motion'
import { stagger, textChild } from '../lib/motion'
import { useReducedMotion } from '../lib/useMotionPreference'

type AnimatedTextProps = {
  text: string
  className?: string
  /** Delay before the first word lands, in seconds. */
  delay?: number
}

/**
 * Splits a line into words and lifts each one into place. The whole string
 * stays in the accessibility tree via aria-label; the spans are hidden from it.
 */
export function AnimatedText({ text, className, delay = 0 }: AnimatedTextProps) {
  const shouldReduce = useReducedMotion()
  const words = text.split(' ')

  if (shouldReduce) {
    return <span className={className}>{text}</span>
  }

  return (
    <motion.span
      className={className}
      variants={stagger(0.06, delay)}
      initial="hidden"
      animate="visible"
      aria-label={text}
    >
      {words.map((word, i) => (
        <span
          key={`${word}-${i}`}
          className="inline-block overflow-hidden align-bottom"
          aria-hidden
        >
          <motion.span className="inline-block" variants={textChild}>
            {word}
            {i < words.length - 1 ? ' ' : ''}
          </motion.span>
        </span>
      ))}
    </motion.span>
  )
}
