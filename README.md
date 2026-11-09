# archr-skills

Agent skills for developing for [ArchR](https://github.com/archr-linux), the
Arch Linux distro for RK3326 handhelds such as the R36S.

| Skill | What it teaches |
|---|---|
| [`archr-launcher-dev`](archr-launcher-dev/SKILL.md) | Create, test and publish themes and modules for archr-launcher (Rust + SDL2; 640×480, 720×720 and 480×320 screens): `theme.toml`, views, `[aspect.*]` layouts per screen shape, frames, sounds, `module.toml`, the JSON-RPC protocol, permissions, the sandbox, and the Theme and Module store rules. |

The skills follow the [Agent Skills](https://agentskills.io) format: a folder
with a `SKILL.md` and the files it points to. Any coding assistant that reads
that format can use them.

## Install in Claude Code

Inside Claude Code:

```
/plugin marketplace add archr-linux/archr-skills
/plugin install archr@archr-skills
```

Or from a shell:

```sh
claude plugin marketplace add archr-linux/archr-skills
claude plugin install archr@archr-skills
```

Restart Claude Code. The skill loads when you ask for an ArchR theme or
module, and you can also call it as `/archr:archr-launcher-dev`. To update:

```sh
claude plugin marketplace update archr-skills
claude plugin update archr@archr-skills
```

## Install by hand

Copy the skill folder to your personal skills folder:

```sh
git clone https://github.com/archr-linux/archr-skills
mkdir -p ~/.claude/skills
cp -r archr-skills/archr-launcher-dev ~/.claude/skills/
```

For a single project, copy it to `.claude/skills/` inside that project. Other
tools that support Agent Skills read the same folder from their own skills
directory; check your tool's documentation for the path.

## What is inside

```
archr-launcher-dev/
  SKILL.md                 workflow and ground rules
  references/themes.md     theme.toml schema, limits, PC capture test, store rules
  references/modules.md    module.toml, API 2 protocol, permissions, sandbox, store rules
  references/checklist.md  what to verify before publishing
  assets/theme-template/   minimal theme that loads
  assets/module-template/  minimal module that passes --check-module
  scripts/precheck.py      static check of a theme or module folder (Python 3.11+)
```

## Limits

The skill does not replace a test on the handheld, and it cannot give a module
the "Reviewed by ArchR" badge: only the ArchR maintainer grants it after
reading the package. The references describe archr-launcher with module API 2;
when the launcher changes, the launcher's `docs/temas.md` and `docs/modulos.md`
win.

## License

MIT. The Lucide icon in the module template is under the ISC license
(lucide-static 0.468.0).
