import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { snap } from '../lib/motion'
import type { Project } from '../lib/projects'

type Props = {
  project: Project
  onClose: () => void
}

/**
 * Detail overlay. The cover and title carry the same `layoutId` as the card
 * that opened it, so Framer Motion tweens the shared elements between the two
 * rather than cross-fading.
 */
export function ProjectModal({ project, onClose }: Props) {
  const panelRef = useRef<HTMLDivElement>(null)
  const [from, to] = project.cover

  // Close on Escape, and hold the page still while the overlay is up.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    panelRef.current?.focus()

    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = previousOverflow
    }
  }, [onClose])

  return (
    <div className="fixed inset-0 z-50 grid place-items-center p-4 sm:p-8">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
      />

      <motion.div
        ref={panelRef}
        layoutId={`card-${project.id}`}
        transition={snap}
        role="dialog"
        aria-modal="true"
        aria-labelledby={`modal-title-${project.id}`}
        tabIndex={-1}
        className="relative max-h-[86svh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-white/10 bg-ink-soft outline-none"
      >
        <motion.div
          layoutId={`cover-${project.id}`}
          className="aspect-16/9 w-full"
          style={{ background: `linear-gradient(135deg, ${from}, ${to})` }}
        />

        <button
          type="button"
          onClick={onClose}
          aria-label="Close case study"
          className="absolute right-4 top-4 grid h-9 w-9 place-items-center rounded-full bg-black/40 text-white/80 backdrop-blur-sm hover:bg-black/60"
        >
          ✕
        </button>

        <div className="p-6 sm:p-8">
          <div className="flex items-baseline justify-between gap-4">
            <motion.h2
              layoutId={`title-${project.id}`}
              id={`modal-title-${project.id}`}
              className="text-2xl font-semibold tracking-tight"
            >
              {project.title}
            </motion.h2>
            <span className="shrink-0 text-sm text-white/40">{project.year}</span>
          </div>

          {/* Body copy is not part of the shared layout, so it fades in after. */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15, duration: 0.3 }}
          >
            <p className="mt-4 leading-relaxed text-white/70">{project.detail}</p>

            <div className="mt-6 flex flex-wrap gap-1.5">
              {project.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full border border-white/10 px-2.5 py-1 text-xs text-white/50"
                >
                  {tag}
                </span>
              ))}
            </div>

            {project.link && (
              <motion.a
                href={project.link}
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                className="mt-8 inline-block rounded-full bg-white px-5 py-2.5 text-sm font-medium text-ink"
              >
                Visit project →
              </motion.a>
            )}
          </motion.div>
        </div>
      </motion.div>
    </div>
  )
}
