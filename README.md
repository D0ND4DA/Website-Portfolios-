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
`API_KEY_21ST` must be in the **process environment** — Claude Code expands
`${...}` in `.mcp.json` from the environment, it does not read a `.env` file.
(Vite's `.env` handling is separate and applies only to `import.meta.env` in
`src/`.) If the variable is unset, the server still loads but authenticates with
the literal string `${API_KEY_21ST}` and every call fails; `claude mcp list`
flags it as a missing-variable warning.

### Alternative: keep the key out of your shell too

Local scope overrides project scope, so you can register a personal copy that
wins over `.mcp.json` without touching the repo or exporting anything:

```bash
claude mcp add --transport http 21st https://21st.dev/api/mcp \
  --header "x-api-key: 21st_sk_…"
```

That writes to `~/.claude.json` under this project's path — private to you, never
committed. The committed `.mcp.json` still serves anyone else who clones the repo.

### Cloud sessions

Claude Code **cloud** sessions cannot hold this credential safely. Per the
[cloud environment docs](https://code.claude.com/docs/en/cloud-environments#set-environment-variables),
environment variables there are readable by anyone using the environment and
there is no secrets store — the docs say explicitly not to put API keys in them.
Use 21st.dev from local Claude Code instead.

If you accept that tradeoff anyway, note that a `.mcp.json` server's traffic goes
over the session network (unlike claude.ai connectors, which tunnel through
Anthropic), so the environment's network access must permit `21st.dev`.

Prefer the CLI? `npx @21st-dev/cli@latest login` stores a token in `~/.config/21st`
and `npx @21st-dev/cli@latest init --client claude --write` merges this same block
into `.mcp.json` without clobbering other servers.

> Note: `@21st-dev/magic` is superseded — it is now a thin compatibility proxy to
> the same endpoint configured above.

### What the server exposes

Verified against the live endpoint: **35 tools**. The ones that matter for this
project:

| Tool | Use |
| --- | --- |
| `search` | Search components, themes, and templates (metadata). **Free.** |
| `get_component` | Pull a component's full source + demo. **Metered.** |
| `get_theme` | Fetch a theme's `:root` / `.dark` CSS tokens. Free. |
| `search_logo` | Brand/UI SVG logos from svgl.app. Free, no login. |
| `generate` / `iterate_generation` / `get_take` | Generate UI from a prompt, then refine a variant. |
| `get_usage` | Current tier and remaining daily quota. |

Search and metadata calls are free; retrieving component **code** is the metered
action. Free accounts get a small daily allowance — check it with `get_usage`.

Because 21st components are React + Tailwind + shadcn, pulled-in code drops into
`src/components/` with little adaptation. Keep animation on the shared vocabulary
in `src/lib/motion.ts` rather than whatever timings a fetched component ships
with, so the page stays one system.

## Discord (MCP)

`.mcp.json` also wires in [`@ncodelife/discord-mcp-server`](https://github.com/ngoctranfire/discord-mcp-server),
which gives Claude Code a Discord bot it can drive — read and send messages,
manage channels and threads, assign roles, run webhooks.

Unlike the 21st server, this one is **not about building the site**. It's useful
for the workflow *around* the site (posting release notes to a community channel,
triaging a feedback channel), so it's opt-in: with no token exported the server
simply fails to start and nothing else in the project is affected.

```json
{
  "discord": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@ncodelife/discord-mcp-server@0.1.1"],
    "env": {
      "DISCORD_TOKEN": "${DISCORD_TOKEN}",
      "DISCORD_GUILD_ID": "${DISCORD_GUILD_ID}"
    }
  }
}
```

The version is pinned. This package is young (0.1.1, low download volume) and it
runs with your bot's full authority, so it's worth reading the diff before bumping
it rather than floating on `@latest`.

### Creating the bot

1. [Developer Portal](https://discord.com/developers/applications) → **New
   Application** → **Bot** → **Reset Token**, and copy it.
2. Under **Privileged Gateway Intents**, enable **Message Content Intent** and
   **Server Members Intent**. Both are mandatory, not optional — the server asks
   the gateway for `Guilds`, `GuildMessages`, `MessageContent`, `GuildMembers`
   and `GuildWebhooks`, and Discord rejects the connection outright if a
   privileged intent it requests is switched off.
3. **OAuth2 → URL Generator**, scope `bot`. Most walkthroughs tell you to tick
   **Administrator** here. Don't: a bot token is a bearer credential, and
   Administrator means anyone holding it can delete every channel in the server.
   Grant only what you actually intend Claude to do:

   | If you want | Permission |
   | --- | --- |
   | `send_message`, `edit_message`, `reply_to_thread` | Send Messages |
   | `read_messages` | View Channels + Read Message History |
   | `add_reaction` / `remove_reaction` | Add Reactions |
   | `create_text_channel`, `create_voice_channel`, `delete_channel`, `move_channel`, categories | Manage Channels |
   | `create_role`, `edit_role`, `assign_role`, `remove_role` | Manage Roles |
   | `create_webhook`, `edit_webhook`, `delete_webhook`, `send_webhook_message` | Manage Webhooks |
   | `create_thread`, `list_threads` | Create Public Threads |

   A read-and-post bot needs only the first three rows. Discord also caps role
   management by hierarchy: the bot can only touch roles positioned *below* its
   own, so drag its role up only as far as it needs to go.
4. Open the generated URL to invite the bot.

### Finishing the connection

```bash
export DISCORD_TOKEN="…"            # from step 1
export DISCORD_GUILD_ID="…"         # optional; right-click the server → Copy Server ID
claude
```

Same rule as `API_KEY_21ST`: Claude Code expands `${...}` in `.mcp.json` from the
**process environment**, not from a `.env` file.

`DISCORD_TOKEN` is required — the server also accepts `--token`, and with neither
it prints a `DISCORD_TOKEN is required` banner and exits. `DISCORD_GUILD_ID`
(`--guild-id`) is optional; it's just the default guild for tool calls that don't
name one, which is convenient when the bot is only in one server.

One behaviour worth knowing, because it differs from the 21st server: this one
logs into Discord *before* it serves MCP, so a missing or bad token means the
process exits `1` and `/mcp` shows the server as **failed** rather than connected
with failing calls. If the variable is unset, `${DISCORD_TOKEN}` is passed through
literally and Discord answers `TokenInvalid` — that's the symptom to look for.

Two more knobs, both optional: `MCP_TRANSPORT` (`stdio` default, or `sse`/`http`)
and `MCP_PORT` (default `8080`) for the non-stdio transports.

### What the server exposes

Verified against `@ncodelife/discord-mcp-server@0.1.1`: **31 tools**.

| Category | Tools |
| --- | --- |
| Servers | `list_servers`, `get_server_info` |
| Channels | `list_channels`, `find_channel`, `create_text_channel`, `create_voice_channel`, `delete_channel`, `create_category`, `list_categories`, `move_channel` |
| Messages | `send_message`, `read_messages`, `edit_message`, `delete_message`, `add_reaction`, `remove_reaction` |
| Webhooks | `list_webhooks`, `create_webhook`, `delete_webhook`, `send_webhook_message`, `edit_webhook` |
| Roles | `list_roles`, `create_role`, `edit_role`, `delete_role`, `assign_role`, `remove_role` |
| Threads | `list_threads`, `create_thread`, `reply_to_thread`, `get_thread` |

Plenty of these are destructive (`delete_channel`, `delete_role`, `delete_message`)
and Discord has no undo for them, so approve those calls deliberately rather than
adding them to an allowlist.

### Cloud sessions

The [21st.dev caveat](#cloud-sessions) applies here with more force. Cloud
environment variables are readable by anyone using the environment and there's no
secrets store, and a Discord bot token is a longer-lived, higher-blast-radius
credential than an API key. Run this server from local Claude Code. If a token
does leak, **Reset Token** in the Developer Portal invalidates the old one
immediately.

### Alternative: `mcp-discord`

[`mcp-discord`](https://github.com/barryyip0625/mcp-discord) is the other
maintained option. Verified live at `1.3.4`: **22 tools**, all prefixed
`discord_`. Compared with the above:

- **It has forum support** — `discord_get_forum_channels`, `discord_create_forum_post`,
  `discord_reply_to_forum`, `discord_delete_forum_post` — where the other server
  folds forums into `create_thread`.
- **It has no role tools at all.** If assigning roles is the point, it's the wrong pick.
- **It starts without a valid token** and exposes a `discord_login` tool instead,
  so `/mcp` shows it connected and you authenticate afterwards.
- It's more widely used but has not been published since July 2025.

Swap it in by replacing the `args` with `["-y", "mcp-discord@1.3.4"]`; it reads the
same `DISCORD_TOKEN` variable and ignores `DISCORD_GUILD_ID`.

> Looking for the protocol community rather than a bot? That's the
> [Model Context Protocol Discord](https://discord.com/invite/model-context-protocol-1312302100125843476)
> — nothing to install, and unrelated to this config.
