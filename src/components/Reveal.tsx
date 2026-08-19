import { motion } from 'framer-motion'
import type { Variants } from 'framer-motion'
import type { ReactNode } from 'react'
import { fadeUp, stagger } from '../lib/motion'
import { useVariants } from '../lib/useMotionPreference'

type RevealProps = {
  children: ReactNode
  /** Variants applied to this element. Defaults to a fade-up. */
  variants?: Variants
  /** Fraction of the element that must be visible before it animates in. */
  amount?: number
  className?: string
  as?: 'div' | 'section' | 'li' | 'article'
}

/**
 * Animates its children in the first time they scroll into view.
 * `once` keeps the page calm on the way back up.
 */
export function Reveal({
  children,
  variants = fadeUp,
  amount = 0.3,
  className,
  as = 'div',
}: RevealProps) {
  const resolved = useVariants(variants)
  const Tag = motion[as]

  return (
    <Tag
      className={className}
      variants={resolved}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount }}
    >
      {children}
    </Tag>
  )
}

type StaggerGroupProps = {
  children: ReactNode
  className?: string
  gap?: number
  amount?: number
  as?: 'div' | 'section' | 'ul'
}

/**
 * Scroll-triggered parent. Children using `fadeUp` (or any variant keyed
 * "hidden"/"visible") inherit the state and arrive one after another.
 */
export function StaggerGroup({
  children,
  className,
  gap = 0.08,
  amount = 0.2,
  as = 'div',
}: StaggerGroupProps) {
  const resolved = useVariants(stagger(gap))
  const Tag = motion[as]

  return (
    <Tag
      className={className}
      variants={resolved}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount }}
    >
      {children}
    </Tag>
  )
}
