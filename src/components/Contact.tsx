import { motion } from 'framer-motion'
import { Reveal } from './Reveal'
import { scaleIn } from '../lib/motion'

const socials = [
  { label: 'Email', href: 'mailto:hello@example.com' },
  { label: 'GitHub', href: 'https://github.com' },
  { label: 'LinkedIn', href: 'https://linkedin.com' },
]

export function Contact() {
  return (
    <section id="contact" className="scroll-mt-24 px-6 py-28">
      <Reveal variants={scaleIn} className="mx-auto max-w-3xl text-center">
        <p className="text-xs uppercase tracking-[0.2em] text-white/40">Contact</p>
        <h2 className="mt-4 text-4xl font-semibold tracking-tight sm:text-5xl">
          Let's build something
          <span className="bg-gradient-to-r from-accent to-accent-warm bg-clip-text text-transparent">
            {' '}
            worth using.
          </span>
        </h2>
        <p className="mx-auto mt-6 max-w-lg leading-relaxed text-white/60">
          Taking on new work from Q1. Tell me what you're making and where it's stuck.
        </p>

        <motion.a
          href="mailto:hello@example.com"
          whileHover={{ scale: 1.04 }}
          whileTap={{ scale: 0.97 }}
          className="mt-10 inline-block rounded-full bg-white px-8 py-3.5 font-medium text-ink"
        >
          hello@example.com
        </motion.a>

        <div className="mt-10 flex justify-center gap-6">
          {socials.map((social) => (
            <motion.a
              key={social.label}
              href={social.href}
              whileHover={{ y: -2 }}
              className="text-sm text-white/50 underline-offset-4 hover:text-white hover:underline"
            >
              {social.label}
            </motion.a>
          ))}
        </div>
      </Reveal>
    </section>
  )
}
