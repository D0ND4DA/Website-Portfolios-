import { motion } from 'framer-motion'
import { fadeUp, snap } from '../lib/motion'
import { useVariants } from '../lib/useMotionPreference'
import type { Project } from '../lib/projects'

type Props = {
  project: Project
  onSelect: (project: Project) => void
}

export function ProjectCard({ project, onSelect }: Props) {
  const variants = useVariants(fadeUp)
  const [from, to] = project.cover

  return (
    <motion.li
      layout
      layoutId={`card-${project.id}`}
      variants={variants}
      exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.18 } }}
      whileHover={{ y: -6 }}
      transition={snap}
      className="list-none"
    >
      <button
        type="button"
        onClick={() => onSelect(project)}
        aria-label={`Open case study: ${project.title}`}
        className="group block w-full overflow-hidden rounded-2xl border border-white/10 bg-ink-soft text-left"
      >
        <motion.div
          layoutId={`cover-${project.id}`}
          className="relative aspect-16/10 overflow-hidden"
          style={{ background: `linear-gradient(135deg, ${from}, ${to})` }}
        >
          <motion.span
            aria-hidden
            className="absolute inset-0 bg-black/0 transition-colors group-hover:bg-black/10"
          />
        </motion.div>

        <div className="p-5">
          <div className="flex items-baseline justify-between gap-4">
            <motion.h3 layoutId={`title-${project.id}`} className="font-medium">
              {project.title}
            </motion.h3>
            <span className="shrink-0 text-xs text-white/40">{project.year}</span>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-white/55">{project.blurb}</p>
          <div className="mt-4 flex flex-wrap gap-1.5">
            {project.tags.map((tag) => (
              <span
                key={tag}
                className="rounded-full border border-white/10 px-2 py-0.5 text-[11px] text-white/50"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      </button>
    </motion.li>
  )
}
