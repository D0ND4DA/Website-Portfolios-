import { motion, useScroll, useTransform } from 'framer-motion'
import { useRef } from 'react'
import { AnimatedText } from './AnimatedText'
import { fadeUp, stagger } from '../lib/motion'
import { useReducedMotion, useVariants } from '../lib/useMotionPreference'

export function Hero() {
  const ref = useRef<HTMLElement>(null)
  const shouldReduce = useReducedMotion()
  const group = useVariants(stagger(0.1, 0.5))
  const item = useVariants(fadeUp)

  // Parallax: the copy drifts up and fades as the section scrolls away.
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ['start start', 'end start'],
  })
  const y = useTransform(scrollYProgress, [0, 1], ['0%', '32%'])
  const opacity = useTransform(scrollYProgress, [0, 0.7], [1, 0])
  const blobY = useTransform(scrollYProgress, [0, 1], ['0%', '-24%'])

  return (
    <section
      ref={ref}
      id="top"
      className="relative flex min-h-[92svh] items-center overflow-hidden px-6"
    >
      {/* Ambient gradient that drifts at a different rate to the text. */}
      <motion.div
        style={shouldReduce ? undefined : { y: blobY }}
        aria-hidden
        className="pointer-events-none absolute -top-40 left-1/2 h-[38rem] w-[38rem] -translate-x-1/2 rounded-full bg-[radial-gradient(circle,rgba(167,139,250,0.22),transparent_65%)] blur-2xl"
      />

      <motion.div
        style={shouldReduce ? undefined : { y, opacity }}
        className="relative mx-auto w-full max-w-5xl"
      >
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-white/60"
        >
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          Available for new work
        </motion.p>

        <h1 className="max-w-3xl text-5xl font-semibold leading-[1.05] tracking-tight sm:text-7xl">
          <AnimatedText text="I design and build" />
          <br />
          <AnimatedText
            text="interfaces that move well."
            delay={0.25}
            className="bg-gradient-to-r from-accent to-accent-warm bg-clip-text text-transparent"
          />
        </h1>

        <motion.div variants={group} initial="hidden" animate="visible">
          <motion.p variants={item} className="mt-8 max-w-xl text-lg text-white/60">
            Product designer and front-end engineer. I care about the half-second
            between a click and a result — the part most teams leave to chance.
          </motion.p>

          <motion.div variants={item} className="mt-10 flex flex-wrap gap-3">
            <motion.a
              href="#work"
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              className="rounded-full bg-white px-6 py-3 text-sm font-medium text-ink"
            >
              See the work
            </motion.a>
            <motion.a
              href="#contact"
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              className="rounded-full border border-white/15 px-6 py-3 text-sm font-medium text-white/80"
            >
              Get in touch
            </motion.a>
          </motion.div>
        </motion.div>
      </motion.div>

      {/* Scroll cue */}
      <motion.div
        aria-hidden
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.4 }}
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
      >
        <motion.div
          animate={shouldReduce ? undefined : { y: [0, 8, 0] }}
          transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
          className="h-8 w-px bg-gradient-to-b from-white/40 to-transparent"
        />
      </motion.div>
    </section>
  )
}
