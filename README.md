# Website Portfolios

Portfolio site built with **Vite + React 19 + TypeScript**, **Tailwind CSS v4**, and
**Framer Motion v13**.

## Getting started

```bash
npm install
npm run dev      # dev server on http://localhost:5173
npm run build    # typecheck + production build to dist/
npm run preview  # serve the production build
npm run typecheck
```

## The motion system

Animation is centralised rather than scattered across components, so the whole
site shares one set of timings.

| File | Role |
| --- | --- |
| `src/lib/motion.ts` | Shared `Variants` and `Transition` presets — `fadeUp`, `fadeIn`, `scaleIn`, `stagger()`, `ease`, `snap`. |
| `src/lib/useMotionPreference.ts` | `useVariants()` swaps in inert variants when the visitor prefers reduced motion. |
| `src/components/Reveal.tsx` | `<Reveal>` and `<StaggerGroup>` — scroll-triggered entrances via `whileInView`. |
| `src/components/AnimatedText.tsx` | Word-by-word headline entrance, with the full string kept in the a11y tree. |
| `src/components/ScrollProgress.tsx` | Top progress bar from `useScroll` smoothed through `useSpring`. |

### Framer Motion features in use

- **`whileInView` + `viewport={{ once: true }}`** — sections animate in once as you
  reach them (`Reveal`, `StaggerGroup`).
- **Variant propagation and staggering** — parents drive children through
  `hidden`/`visible` states; see `stagger()` in `src/lib/motion.ts`.
- **`layoutId` shared layout** — the nav pill and the work-filter pill slide between
  tabs, and a project card's cover and title tween into the detail overlay
  (`ProjectCard.tsx` → `ProjectModal.tsx`).
- **`AnimatePresence`** — exit animations for the mobile drawer, the filtered project
  grid (`mode="popLayout"`), and the case-study modal.
- **`useScroll` + `useTransform`** — hero parallax, where the copy and the ambient
  gradient move at different rates.
- **`useMotionValueEvent`** — the nav background reacts to scroll offset without
  re-rendering on every frame.
- **`whileHover` / `whileTap`** — button and card affordances, using the shared
  `snap` spring.

### Accessibility

`useReducedMotion` is respected throughout via `useVariants`. Under
`prefers-reduced-motion: reduce`, entrance animations, parallax, and the scroll cue
are disabled while all content stays visible and interactive. The case-study modal
traps focus on open, closes on <kbd>Escape</kbd>, and restores body scroll on exit.

## Adding a project

Append an entry to `projects` in `src/lib/projects.ts`. `cover` is a two-stop
gradient; `tags` must be drawn from `categories` for the filter to pick it up.

## 21st.dev components (MCP)

`.mcp.json` wires the [21st.dev](https://21st.dev) MCP server into this project, so
Claude Code can search the 21st component registry and pull component source
directly into `src/components/`. It's a good fit here — 21st ships React +
Tailwind + shadcn components, which is exactly this stack.

The config holds **no secret**; it reads an env var:

```json
{
  "mcpServers": {
    "21st": {
      "type": "http",
      "url": "https://21st.dev/api/mcp",
      "headers": { "x-api-key": "${API_KEY_21ST}" }
    }
  }
}
```

### Finishing the connection

1. Grab a key at <https://21st.dev/settings/api-keys> (starts with `21st_sk_…`).
2. Export it, then start Claude Code from this directory:

   ```bash
   export API_KEY_21ST="21st_sk_…"   # add to your shell profile to persist
   claude
   ```

   Claude Code prompts once to approve the project-scoped server; `/mcp` shows it
   as connected.
3. For a Claude Code **web/remote** session, set `API_KEY_21ST` as an environment
   variable on the environment instead — the container has no access to your
   local shell.

Prefer the CLI? `npx @21st-dev/cli@latest login` stores a token in `~/.config/21st`
and `npx @21st-dev/cli@latest init --client claude --write` merges this same block
into `.mcp.json` without clobbering other servers.

> Note: `@21st-dev/magic` is superseded — it is now a thin compatibility proxy to
> the same endpoint configured above.
