# Publishing Guide: from an empty folder to a live plugin on GitHub

This guide walks you through publishing the **jupyter-notebook** Claude Code
plugin, step by step, in plain language. It assumes you have never published
anything to GitHub before. Follow it top to bottom.

By the end you will have:

1. The plugin files organised in a folder on your computer.
2. That folder tested locally in Claude Code.
3. The folder uploaded to a GitHub repository.
4. A one-line command other people can run to install your plugin.

Every command is shown in a grey box. Lines that start with `#` are comments
explaining the command — you do not type those.

---

## Part 0 — Things you need first (one-time setup)

You need four things installed. Check each one; install only what is missing.

### 0.1 Git

Git is the tool that uploads your files to GitHub.

```bash
# Check if git is already installed:
git --version
```

If you see a version number (e.g. `git version 2.43`), you're done. If you see
"command not found":

- **macOS**: run `xcode-select --install`, or install from https://git-scm.com
- **Windows**: download from https://git-scm.com and run the installer
- **Linux**: `sudo apt install git` (Debian/Ubuntu) or your distro's equivalent

The very first time you use git, tell it who you are (this labels your uploads):

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### 0.2 A GitHub account

Sign up free at https://github.com if you don't have one. Remember your
username — you will use it a lot below. This guide writes it as
`YOUR-USERNAME`.

### 0.3 The GitHub CLI (recommended, makes step 4 painless)

The `gh` tool lets you create a GitHub repository and log in from the terminal
without fiddling with passwords.

```bash
# Check if it's installed:
gh --version
```

If missing, install from https://cli.github.com. (You can skip this and use the
website instead — see the alternative in Part 4 — but `gh` is the easy path.)

### 0.4 Claude Code and the Python dependencies

You need Claude Code installed to test the plugin, and the plugin's two Python
libraries available in the environment Claude Code runs in.

```bash
# Check Claude Code:
claude --version

# Install the plugin's Python dependencies:
pip install nbformat markdown
# (or, if you use uv:  uv pip install nbformat markdown)
```

---

## Part 1 — Put the plugin files in a folder

You already have the finished plugin in the folder
`jupyter-notebook-marketplace`. If you have it, **skip to Part 2**.

If you are starting from a truly empty folder and want to build the structure
yourself, here is the exact layout you are aiming for:

```
jupyter-notebook-marketplace/
├── .claude-plugin/
│   └── marketplace.json
├── README.md
├── PUBLISHING-GUIDE.md            <- this file
└── plugins/
    └── jupyter-notebook/
        ├── .claude-plugin/
        │   └── plugin.json
        └── skills/
            └── jupyter-notebook/
                ├── SKILL.md
                ├── README.md
                ├── pyproject.toml
                ├── nbtools/        (the Python package: 7 .py files)
                └── tests/
                    └── test_nbtools.py
```

To create the empty folder structure from scratch:

```bash
# Make the folders (the -p flag creates parent folders as needed):
mkdir -p jupyter-notebook-marketplace/.claude-plugin
mkdir -p jupyter-notebook-marketplace/plugins/jupyter-notebook/.claude-plugin
mkdir -p jupyter-notebook-marketplace/plugins/jupyter-notebook/skills/jupyter-notebook
```

Then copy the provided files into those folders so the tree matches the diagram
above. The two small JSON files (`marketplace.json`, `plugin.json`) are the
manifests; everything under `skills/jupyter-notebook/` is the skill itself.

---

## Part 2 — Edit the three placeholders

Before publishing, open these files in any text editor and replace the
placeholder values. This is important: the names are public and one of them is
what people type to install your plugin.

### 2.1 `.claude-plugin/marketplace.json`

```json
{
  "name": "my-skills",            <- rename to your own catalog name
  "owner": {
    "name": "Your Name"           <- put your name or team here
  }
}
```

- `name` is your **marketplace** name. People will install with
  `plugin-name@THIS-NAME`. Use lowercase letters, numbers, and hyphens only
  (this is called *kebab-case*), e.g. `janes-skills`.
- Do **not** use names reserved for Anthropic, such as `agent-skills`,
  `anthropic-plugins`, `claude-code-plugins`, or anything that looks like an
  official Anthropic marketplace. Those are blocked.

### 2.2 `plugins/jupyter-notebook/.claude-plugin/plugin.json`

```json
{
  "author": {
    "name": "Your Name"          <- put your name here
  }
}
```

You may also add a `"repository"` line later pointing at your GitHub URL — it's
optional.

### 2.3 A note on `version`

`plugin.json` has `"version": "1.0.0"`. Remember this rule for later: **every
time you publish a change, increase this number** (e.g. to `1.0.1`). Claude Code
only sends updates to users when this number changes.

---

## Part 3 — Test it locally before uploading

Always confirm it works on your own machine first. Open a terminal in the folder
that **contains** `jupyter-notebook-marketplace` (i.e. one level above it).

### 3.1 Check the manifests are valid

```bash
claude plugin validate ./jupyter-notebook-marketplace
```

This checks the JSON files for mistakes (missing commas, bad paths, etc.). Fix
anything it reports before continuing.

### 3.2 Add the marketplace and install the plugin

You can do this inside a Claude Code session (commands starting with `/`) or
from the terminal (commands starting with `claude`). Pick one style.

Inside a Claude Code session:

```
/plugin marketplace add ./jupyter-notebook-marketplace
/plugin install jupyter-notebook@my-skills
```

Or from the terminal:

```bash
claude plugin marketplace add ./jupyter-notebook-marketplace
claude plugin install jupyter-notebook@my-skills
```

(Replace `my-skills` with whatever you named your marketplace in step 2.1.)

### 3.3 Try it

Start Claude Code and ask it something like "read this notebook and list its
cells" with an `.ipynb` file. The skill is used automatically. If it works,
you're ready to publish.

---

## Part 4 — Upload to GitHub

Now we put the folder online. Open a terminal **inside** the
`jupyter-notebook-marketplace` folder:

```bash
cd jupyter-notebook-marketplace
```

### 4.1 Turn the folder into a git repository

```bash
# Start tracking this folder with git:
git init

# Stage every file (the dot means "everything in this folder"):
git add .

# Save a labelled snapshot (your first "commit"):
git commit -m "Initial commit: jupyter-notebook plugin"

# Name the main branch "main" (GitHub's default):
git branch -M main
```

### 4.2 Create the GitHub repository and push — the easy way (`gh`)

If you installed the GitHub CLI in step 0.3:

```bash
# Log in once (opens your browser to confirm):
gh auth login

# Create the repo on GitHub AND upload your files in one command:
gh repo create jupyter-notebook-marketplace --public --source=. --remote=origin --push
```

That's it — your code is now on GitHub. Skip to Part 5.

### 4.2 (Alternative) The manual way, without `gh`

If you didn't install `gh`:

1. Go to https://github.com/new in your browser.
2. **Repository name**: `jupyter-notebook-marketplace`
3. Set it to **Public**.
4. Do **not** tick "Add a README" (you already have one).
5. Click **Create repository**.
6. GitHub now shows you a URL like
   `https://github.com/YOUR-USERNAME/jupyter-notebook-marketplace.git`.
   Use it in the commands below:

```bash
# Connect your local folder to the empty GitHub repo:
git remote add origin https://github.com/YOUR-USERNAME/jupyter-notebook-marketplace.git

# Upload everything:
git push -u origin main
```

If git asks for a password, GitHub no longer accepts your account password
here. Either install `gh` (easiest), or create a "Personal Access Token" at
https://github.com/settings/tokens and paste that as the password.

---

## Part 5 — Install from GitHub (and share with others)

Once the repo is online, anyone (including you, on another machine) can install
the plugin with just your username and repo name — no downloading by hand.

Inside a Claude Code session:

```
/plugin marketplace add YOUR-USERNAME/jupyter-notebook-marketplace
/plugin install jupyter-notebook@my-skills
```

Or from the terminal:

```bash
claude plugin marketplace add YOUR-USERNAME/jupyter-notebook-marketplace
claude plugin install jupyter-notebook@my-skills
```

To share with a teammate, send them those two lines (with your real username and
marketplace name). They run them and they're done.

> **Why this works**: the plugin's location is written as a relative path
> (`./plugins/jupyter-notebook`). That works because GitHub gives Claude Code
> the *whole* repository when someone adds it. If you ever serve only the
> `marketplace.json` file from a bare web link instead of a Git repo, relative
> paths break — in that case you'd change the plugin's `source` to a GitHub
> object. For normal GitHub publishing you don't need to worry about this.

---

## Part 6 — Installing or updating on your own machine (Claude CLI)

This is for getting the plugin from GitHub onto a machine, and later pulling a
newer version. Everything here runs in your normal terminal — you do not need to
be inside a Claude Code session.

### 6.1 Fresh install (a machine that has never had it)

```bash
# 1. Register your published marketplace (this clones the repo behind the scenes):
claude plugin marketplace add YOUR-USERNAME/jupyter-notebook-marketplace

# 2. Install the plugin from that marketplace:
claude plugin install jupyter-notebook@my-skills

# 3. Install the Python libraries the skill needs:
pip install nbformat markdown

# 4. Confirm it's installed (shows version, source marketplace, enabled status):
claude plugin list
```

By default the plugin installs for your whole user account. To limit it to the
current project instead, add a scope:

```bash
claude plugin install jupyter-notebook@my-skills --scope project
```

### 6.2 Update to a newer version

Installing does **not** automatically pull new commits. You first refresh the
marketplace's local copy from GitHub, then update the plugin:

```bash
# 1. Pull the latest marketplace contents from GitHub:
claude plugin marketplace update my-skills

# 2. Update the plugin to the newest version:
claude plugin update jupyter-notebook

# 3. Check the version actually changed:
claude plugin list
```

If the update doesn't seem to take effect, fully quit and restart Claude Code so
it reloads its skill list.

---

## Part 7 — Publishing the next version (after you edit the skill)

When you improve the skill later, follow these steps in order. Step 7.2 (the
version bump) is the one people forget — and without it, your users never
receive the update.

### 7.1 Make and test your changes

Edit the skill files under
`plugins/jupyter-notebook/skills/jupyter-notebook/`. Then run the test suite
from inside that folder to prove nothing broke:

```bash
cd plugins/jupyter-notebook/skills/jupyter-notebook
pytest
cd -        # returns you to the marketplace root
```

### 7.2 Bump the version number

Open `plugins/jupyter-notebook/.claude-plugin/plugin.json` and raise `version`.
The convention (called *semantic versioning*) is `MAJOR.MINOR.PATCH`:

- **PATCH** — `1.0.0` → `1.0.1` — a bug fix, no behaviour change.
- **MINOR** — `1.0.0` → `1.1.0` — a new feature, still backwards-compatible.
- **MAJOR** — `1.0.0` → `2.0.0` — a breaking change.

Set the number in `plugin.json` only — not also in `marketplace.json`. If both
carry a version, `plugin.json` silently wins, which is confusing later.

### 7.3 Validate, commit, and push

```bash
claude plugin validate .                 # re-check the manifests are still valid
git add .
git commit -m "v1.0.1: describe what you changed"
git push
```

Optionally tag the release so the version is easy to find on GitHub:

```bash
git tag v1.0.1
git push --tags
```

### 7.4 Tell users how to upgrade

They run the update flow from Part 6.2:

```bash
claude plugin marketplace update my-skills
claude plugin update jupyter-notebook
```

---

## Part 8 — Removing the plugin or the marketplace

There are two different kinds of "remove". Decide which you mean before running
anything.

### 8.1 Remove it from your own machine (stop using it locally)

```bash
# Uninstall the plugin (the plugin@marketplace form avoids ambiguity):
claude plugin uninstall jupyter-notebook@my-skills

# Optionally also unregister the whole marketplace:
claude plugin marketplace remove my-skills
```

To also clean up any dependencies the plugin brought in, newer Claude Code
versions accept a prune flag:

```bash
claude plugin uninstall jupyter-notebook --prune     # requires Claude Code v2.1.121+
```

Known quirks, if a removal doesn't fully "stick":

- Removing a marketplace through the interactive `/plugin` menu has been
  reported to leave an entry in `~/.claude/settings.json` that quietly reloads
  it on the next start. Using the **CLI** command
  `claude plugin marketplace remove` is the reliable path.
- Cached files under `~/.claude/plugins/cache/` can linger after removal. If a
  stale copy keeps reappearing, delete that marketplace's cache folder by hand:
  `rm -rf ~/.claude/plugins/cache/my-skills`.
- After removing, fully restart Claude Code so the skill list refreshes.

### 8.2 Remove it from your published marketplace (so others can no longer install it)

This is an edit-and-push job, not a single CLI command.

**To remove just this plugin while keeping the marketplace:** delete its entry
from the `plugins` array in `.claude-plugin/marketplace.json` (and optionally
delete the `plugins/jupyter-notebook/` folder), then commit and push:

```bash
git add .
git commit -m "Remove jupyter-notebook plugin from the marketplace"
git push
```

**To take down the entire marketplace:** delete the GitHub repository (on
github.com: open the repo → **Settings** → scroll to the **Danger Zone** →
**Delete this repository**), or switch it to private.

**Important:** removing it from GitHub stops *new* installs and *future*
updates, but it does **not** uninstall it from people who already have it. Their
copy keeps working until they remove it themselves (Part 8.1). If you need them
to stop, send them the uninstall commands.

---

## Quick reference

**Publish for the first time** (run from inside the marketplace folder):

```bash
git config --global user.name "Your Name"          # one-time identity setup
git config --global user.email "you@example.com"

cd jupyter-notebook-marketplace
claude plugin validate .                            # check it's valid
git init
git add .
git commit -m "Initial commit: jupyter-notebook plugin"
git branch -M main
gh auth login                                       # log in to GitHub
gh repo create jupyter-notebook-marketplace --public --source=. --remote=origin --push
```

**Everyday operations:**

```bash
# Install on a machine
claude plugin marketplace add YOUR-USERNAME/jupyter-notebook-marketplace
claude plugin install jupyter-notebook@my-skills
pip install nbformat markdown

# Update to a newer published version
claude plugin marketplace update my-skills
claude plugin update jupyter-notebook

# Publish a new version (after editing + bumping version in plugin.json)
claude plugin validate .
git add . && git commit -m "v1.0.1: ..." && git push

# Remove from your machine
claude plugin uninstall jupyter-notebook@my-skills
claude plugin marketplace remove my-skills

# Inspect what's installed
claude plugin list
```

---

## Troubleshooting

**`claude plugin validate` reports an error.**
Most often a JSON typo — a missing or extra comma in `marketplace.json` or
`plugin.json`. Open the file and check the punctuation around the line it names.

**"Duplicate plugin name" or "not kebab-case".**
Plugin and marketplace names must be lowercase letters, numbers, and hyphens
only, and each plugin name must be unique within the marketplace.

**`git push` asks for a password and rejects it.**
GitHub stopped accepting account passwords for pushing. Use `gh auth login`, or
create a Personal Access Token (https://github.com/settings/tokens) and use that
token as the password.

**Teammates get "path not found" when installing.**
This happens if they added your marketplace from a bare URL to the JSON file
instead of the Git repo. Have them add it with the `YOUR-USERNAME/repo`
shorthand (which clones the whole repo), as shown in Part 5.

**The plugin installs but Claude doesn't seem to use it.**
Confirm the Python dependencies are installed in the environment Claude Code
runs in: `pip install nbformat markdown`.

**`claude plugin update` didn't pull my new version.**
Run `claude plugin marketplace update my-skills` first (that refreshes the copy
from GitHub), then `claude plugin update jupyter-notebook`, then restart Claude
Code. Also double-check you bumped `version` in `plugin.json` and pushed it.

**I removed the plugin/marketplace but it keeps coming back.**
Remove it from the **terminal** with `claude plugin marketplace remove my-skills`
rather than the interactive menu, then restart Claude Code. If it still returns,
a leftover entry in `~/.claude/settings.json` or a cached folder at
`~/.claude/plugins/cache/my-skills` may need deleting by hand.

---

## Official documentation

- Create and distribute a marketplace: https://code.claude.com/docs/en/plugin-marketplaces
- Creating plugins: https://code.claude.com/docs/en/plugins
- Plugin & CLI reference (install / update / uninstall / remove): https://code.claude.com/docs/en/plugins-reference
- GitHub: getting started: https://docs.github.com/en/get-started