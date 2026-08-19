export type Project = {
  id: string
  title: string
  blurb: string
  detail: string
  year: string
  tags: string[]
  /** Two-stop gradient used for the card's cover art. */
  cover: [string, string]
  link?: string
}

export const categories = ['All', 'Product', 'Web', 'Brand'] as const
export type Category = (typeof categories)[number]

export const projects: Project[] = [
  {
    id: 'atlas',
    title: 'Atlas Dashboard',
    blurb: 'Analytics surface for a logistics fleet running in 14 countries.',
    detail:
      'Rebuilt the operator console around a single live map. Cut median time-to-triage from nine minutes to under two by collapsing four legacy screens into one prioritised queue.',
    year: '2025',
    tags: ['Product', 'Web'],
    cover: ['#6d28d9', '#2563eb'],
    link: '#',
  },
  {
    id: 'ember',
    title: 'Ember Identity',
    blurb: 'Wordmark, motion system, and design tokens for a climate startup.',
    detail:
      'A brand built to move: every mark has a defined entrance, and the token set ships as a package the product team consumes directly, so the site and the app never drift.',
    year: '2025',
    tags: ['Brand'],
    cover: ['#f97316', '#db2777'],
    link: '#',
  },
  {
    id: 'quill',
    title: 'Quill Editor',
    blurb: 'Collaborative long-form writing tool with offline-first sync.',
    detail:
      'CRDT-backed document model with a deliberately quiet interface. The hard part was conflict resolution that never surprises the writer — edits merge without the cursor ever jumping.',
    year: '2024',
    tags: ['Product', 'Web'],
    cover: ['#0d9488', '#4f46e5'],
    link: '#',
  },
  {
    id: 'northwind',
    title: 'Northwind Studio',
    blurb: 'Marketing site and case-study system for an architecture practice.',
    detail:
      'Editorial layout driven entirely by scroll position. Case studies are authored in Markdown and lay themselves out from a handful of layout hints, so the practice publishes without a developer.',
    year: '2024',
    tags: ['Web', 'Brand'],
    cover: ['#0891b2', '#7c3aed'],
    link: '#',
  },
  {
    id: 'signal',
    title: 'Signal Reports',
    blurb: 'Scheduled reporting pipeline with a human-readable diff view.',
    detail:
      'Every report renders alongside what changed since the last run. Reviewers stopped re-reading unchanged sections, which is where most of the time was going.',
    year: '2023',
    tags: ['Product'],
    cover: ['#be123c', '#7c2d12'],
    link: '#',
  },
  {
    id: 'meridian',
    title: 'Meridian',
    blurb: 'Design-system documentation site with live, editable examples.',
    detail:
      'Components are documented from their own source. Props tables, accessibility notes, and playground state all derive from the implementation, so the docs cannot fall out of date.',
    year: '2023',
    tags: ['Web'],
    cover: ['#4338ca', '#0ea5e9'],
    link: '#',
  },
]
