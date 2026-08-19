import { useEffect, useState } from 'react'
import { AnimatePresence, motion, useMotionValueEvent, useScroll } from 'framer-motion'
import { snap } from '../lib/motion'

const links = [
  { id: 'work', label: 'Work' },
  { id: 'about', label: 'About' },
  { id: 'contact', label: 'Contact' },
]

export function Nav() {
  const [active, setActive] = useState('work')
  const [open, setOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const { scrollY } = useScroll()

  useMotionValueEvent(scrollY, 'change', (y) => setScrolled(y > 24))

  // Track which section is on screen so the pill indicator follows the reader.
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0]
        if (visible) setActive(visible.target.id)
      },
      { rootMargin: '-45% 0px -45% 0px', threshold: [0, 0.25, 0.5, 1] },
    )

    for (const { id } of links) {
      const el = document.getElementById(id)
      if (el) observer.observe(el)
    }
    return () => observer.disconnect()
  }, [])

  return (
    <motion.header
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ ...snap, delay: 0.2 }}
      className="fixed inset-x-0 top-0 z-40"
    >
      <motion.nav
        animate={{
          backgroundColor: scrolled ? 'rgba(8,8,12,0.72)' : 'rgba(8,8,12,0)',
          borderColor: scrolled ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0)',
        }}
        transition={{ duration: 0.3 }}
        className="mx-auto flex max-w-5xl items-center justify-between border-b px-6 py-4 backdrop-blur-md"
      >
        <a href="#top" className="text-sm font-semibold tracking-tight">
          <span className="text-accent">◆</span> Portfolio
        </a>

        {/* Desktop links — layoutId lets the pill slide between items. */}
        <ul className="hidden items-center gap-1 sm:flex">
          {links.map((link) => (
            <li key={link.id} className="relative">
              <a
                href={`#${link.id}`}
                className="relative z-10 block rounded-full px-4 py-1.5 text-sm text-white/70 transition-colors hover:text-white"
              >
                {link.label}
              </a>
              {active === link.id && (
                <motion.span
                  layoutId="nav-pill"
                  transition={snap}
                  className="absolute inset-0 rounded-full bg-white/10"
                />
              )}
            </li>
          ))}
        </ul>

        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-controls="mobile-menu"
          aria-label="Toggle menu"
          className="relative flex h-9 w-9 items-center justify-center rounded-full border border-white/10 sm:hidden"
        >
          <motion.span
            animate={{ rotate: open ? 45 : 0, y: open ? 3 : -3 }}
            transition={snap}
            className="absolute h-px w-4 bg-white"
          />
          <motion.span
            animate={{ rotate: open ? -45 : 0, y: open ? 0 : 3 }}
            transition={snap}
            className="absolute h-px w-4 bg-white"
          />
        </button>
      </motion.nav>

      {/* Mobile drawer — AnimatePresence keeps the exit animation alive. */}
      <AnimatePresence>
        {open && (
          <motion.ul
            id="mobile-menu"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
            className="overflow-hidden border-b border-white/10 bg-ink/95 backdrop-blur-md sm:hidden"
          >
            {links.map((link) => (
              <li key={link.id}>
                <a
                  href={`#${link.id}`}
                  onClick={() => setOpen(false)}
                  className="block px-6 py-3 text-sm text-white/80"
                >
                  {link.label}
                </a>
              </li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </motion.header>
  )
}
