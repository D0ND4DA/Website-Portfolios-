import { motion } from 'framer-motion'
import { Reveal, StaggerGroup } from './Reveal'
import { fadeUp } from '../lib/motion'
import { useVariants } from '../lib/useMotionPreference'

const stats = [
  { value: '9', label: 'Years shipping' },
  { value: '40+', label: 'Projects delivered' },
  { value: '12', label: 'Teams supported' },
  { value: '3', label: 'Design systems built' },
]

const skills = [
  'React & TypeScript',
  'Framer Motion',
  'Design systems',
  'Accessibility',
  'Prototyping',
  'Front-end architecture',
]

export function About() {
  const item = useVariants(fadeUp)

  return (
    <section id="about" className="scroll-mt-24 border-y border-white/5 bg-ink-soft/40">
      <div className="mx-auto max-w-5xl px-6 py-28">
        <Reveal>
          <p className="text-xs uppercase tracking-[0.2em] text-white/40">About</p>
          <h2 className="mt-3 max-w-2xl text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
            I work at the seam between design and engineering, where most of the
            interesting problems live.
          </h2>
          <p className="mt-6 max-w-2xl leading-relaxed text-white/60">
            My background is half studio, half product team. That means I can take a
            rough idea to a working prototype without a handoff, and I can argue for
            the animation budget in a performance review — with numbers.
          </p>
        </Reveal>

        <StaggerGroup className="mt-14 grid grid-cols-2 gap-6 sm:grid-cols-4">
          {stats.map((stat) => (
            <motion.div key={stat.label} variants={item}>
              <div className="text-3xl font-semibold tracking-tight text-accent">
                {stat.value}
              </div>
              <div className="mt-1 text-sm text-white/50">{stat.label}</div>
            </motion.div>
          ))}
        </StaggerGroup>

        <StaggerGroup as="ul" className="mt-14 flex flex-wrap gap-2" gap={0.05}>
          {skills.map((skill) => (
            <motion.li
              key={skill}
              variants={item}
              whileHover={{ y: -3 }}
              className="rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-white/70"
            >
              {skill}
            </motion.li>
          ))}
        </StaggerGroup>
      </div>
    </section>
  )
}
