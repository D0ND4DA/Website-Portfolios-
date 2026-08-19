import { useMemo, useState } from 'react'
import { AnimatePresence, LayoutGroup, motion } from 'framer-motion'
import { ProjectCard } from './ProjectCard'
import { ProjectModal } from './ProjectModal'
import { Reveal, StaggerGroup } from './Reveal'
import { snap } from '../lib/motion'
import { categories, projects } from '../lib/projects'
import type { Category, Project } from '../lib/projects'

export function Projects() {
  const [filter, setFilter] = useState<Category>('All')
  const [selected, setSelected] = useState<Project | null>(null)

  const visible = useMemo(
    () => (filter === 'All' ? projects : projects.filter((p) => p.tags.includes(filter))),
    [filter],
  )

  return (
    <section id="work" className="mx-auto max-w-5xl scroll-mt-24 px-6 py-28">
      <Reveal className="flex flex-wrap items-end justify-between gap-6">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-white/40">Selected work</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
            Six projects worth talking about
          </h2>
        </div>
      </Reveal>

      {/* Filter row. The underline is one element that slides between tabs. */}
      <LayoutGroup>
        <Reveal className="mt-10 flex flex-wrap gap-2" amount={0.5}>
          {categories.map((category) => (
            <button
              key={category}
              type="button"
              onClick={() => setFilter(category)}
              aria-pressed={filter === category}
              className="relative rounded-full px-4 py-1.5 text-sm text-white/60 transition-colors hover:text-white"
            >
              {filter === category && (
                <motion.span
                  layoutId="filter-pill"
                  transition={snap}
                  className="absolute inset-0 rounded-full border border-white/15 bg-white/10"
                />
              )}
              <span className="relative z-10">{category}</span>
            </button>
          ))}
        </Reveal>

        {/* `layout` on the grid lets surviving cards slide as siblings leave. */}
        <StaggerGroup
          as="ul"
          className="mt-8 grid gap-6 sm:grid-cols-2"
          amount={0.1}
        >
          <AnimatePresence mode="popLayout">
            {visible.map((project) => (
              <ProjectCard key={project.id} project={project} onSelect={setSelected} />
            ))}
          </AnimatePresence>
        </StaggerGroup>

        {/* Kept inside the LayoutGroup so the modal and its card share layout. */}
        <AnimatePresence>
          {selected && (
            <ProjectModal
              key={selected.id}
              project={selected}
              onClose={() => setSelected(null)}
            />
          )}
        </AnimatePresence>
      </LayoutGroup>
    </section>
  )
}
