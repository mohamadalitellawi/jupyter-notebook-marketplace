# my-skills — a Claude Code plugin marketplace

A single-plugin marketplace that distributes the **jupyter-notebook** skill
(read / inspect / edit / create / convert `.ipynb` files via the `nbtools`
Python package).

## Layout

```
jupyter-notebook-marketplace/          <- marketplace repo root
├── .claude-plugin/
│   └── marketplace.json               <- the catalog (lists plugins)
└── plugins/
    └── jupyter-notebook/              <- one plugin
        ├── .claude-plugin/
        │   └── plugin.json            <- plugin manifest
        └── skills/
            └── jupyter-notebook/      <- the skill itself
                ├── SKILL.md
                ├── nbtools/           <- the Python package
                ├── tests/
                └── pyproject.toml
```

Two manifests, two jobs: `plugin.json` describes the plugin; `marketplace.json`
is the catalog that points at it. The skill lives under the plugin's `skills/`
directory — that's the convention Claude Code looks for.

## Before you publish: edit these

- `marketplace.json` → `name` (currently `my-skills`) and `owner.name`.
  The marketplace name is public; users type it when installing
  (`/plugin install jupyter-notebook@<name>`). Keep it kebab-case. Do **not**
  use names reserved for Anthropic (`agent-skills`, `anthropic-plugins`, etc.).
- `plugin.json` → `author.name` (and optionally add `"repository": "https://..."`).
- `plugin.json` → bump `version` on every release. Claude Code only ships
  updates to users when this string changes. (Set it in `plugin.json` *or* the
  marketplace entry, not both — `plugin.json` wins silently.)

## Use it locally (fastest path)

From inside a Claude Code session, point it at this folder:

```
/plugin marketplace add ./jupyter-notebook-marketplace
/plugin install jupyter-notebook@my-skills
```

Or from your terminal (equivalent, non-interactive):

```bash
claude plugin marketplace add ./jupyter-notebook-marketplace
claude plugin install jupyter-notebook@my-skills
```

The skill is model-invoked: once installed, Claude uses it automatically when
you mention notebooks or `.ipynb` files. Install the Python deps once in the
environment Claude Code runs in:

```bash
pip install nbformat markdown      # or: uv pip install nbformat markdown
```

## Validate before sharing

```bash
claude plugin validate .           # checks marketplace.json + referenced plugin.json
```

## Publish for others (GitHub)

1. Push this folder to a GitHub repo (e.g. `your-name/jupyter-notebook-marketplace`).
2. Others install with the `owner/repo` shorthand — no clone needed:

```
/plugin marketplace add your-name/jupyter-notebook-marketplace
/plugin install jupyter-notebook@my-skills
```

Relative `source` paths (used here) work over Git because the whole repo is
cloned. They do **not** work if you serve `marketplace.json` from a bare URL;
for that, switch the plugin `source` to a `github` object instead.

## Updating

- You: bump `version` in `plugin.json`, push.
- Users: `/plugin marketplace update my-skills` then `/plugin install` again,
  or rely on auto-update.

## Reference

- Plugin marketplaces: https://code.claude.com/docs/en/plugin-marketplaces
- Creating plugins: https://code.claude.com/docs/en/plugins
