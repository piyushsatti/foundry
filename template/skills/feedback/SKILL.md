---
name: feedback
description: Use when something in this plugin went wrong, behaved unexpectedly, or worked well enough to be worth keeping. Walks through filing a GitHub issue on the right repository, and decides whether the fault belongs to this plugin or to Foundry underneath it.
---

# Report what happened

Something in this plugin did not do what you expected, or did something worth keeping. Write it down where the person who can fix it will read it.

**File against the repository you are working in.** Not against Foundry, not against a plugin this one depends on. Whoever picks the issue up decides where it really belongs, and they have context you do not.

## What to write

Four things, in this order. Skip any you genuinely do not have rather than guessing.

| Part | What it is |
|---|---|
| What you were doing | The command, the skill, or the step. One sentence |
| What you expected | What you thought would happen |
| What happened instead | The actual output. Paste the shortest piece that shows it, including any error verbatim |
| What is going right | Anything nearby that worked. This is not politeness: it is what stops a fix breaking something that was fine |

Add the plugin's version if you can find it. It is in `foundry.lock.json` in the installed folder, next to the `contents` fingerprint of what you actually have.

## Filing it

```
gh issue create --repo <owner>/<this-plugin> --title "<one line>" --body-file <your notes>
```

If `gh` is not set up, open the repository's Issues tab in a browser and paste the same four parts.

**Do not file the same thing twice.** Search first: `gh issue list --repo <owner>/<this-plugin> --search "<a distinctive phrase>"`. An existing issue you can add a second case to is worth more than a new one.

## Where the fault actually lives

Every plugin built with Foundry sits on top of it, so a problem can come from either. **The session that picks up the issue makes this call, not the person filing it.**

| The problem is | Signs | What happens |
|---|---|---|
| This plugin's | A skill's own instructions, its content, a command it defines, something only this plugin does | Fixed here. Nothing goes upstream |
| Foundry's, showing through this plugin | The build refused something it should have accepted, a file is missing from the installed folder, a lock file disagrees with what is on disk, an error message names something untrue about a harness | Fixed here if a workaround exists, and **filed upstream against Foundry as well**, quoting the same four parts |

A build problem usually reads as "the folder I installed is not what the repository holds". That is Foundry's shape of fault.

**Nothing reports itself automatically.** Foundry keeps no list of the plugins built with it and never reaches into a repository. It learns about a problem when somebody chooses to tell it, which is the whole reason this skill exists.
