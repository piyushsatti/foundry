# Consistency review, 2026-10-31

Design review only. Nothing in this file is shipped, implemented, or approved to run. It does not change the plugin compiler, the governance pack, the diagrams, or the Engineering pages.

Compared, read-only, on 2026-10-31:

| Surface | What was read |
| --- | --- |
| Settle brief | `sat-oct31-settle-brief.md` in the review bundle. Same text as the uploaded brief. |
| Pack docs | `foundry-pack/` markdown in the bundle: README, GAPS, CHECKLIST, DONE, `docs/00` through `docs/07`, and `docs/03-systems/`. |
| Guided path | `foundry-cli/guided-path-v1-draft.md`. |
| GAPS | Pack `GAPS.md`. Same text as the uploaded `GAPS.md`. |
| Update reports | `docs-update-report.md`, `excal-update-report.md`. The Excalidraw files and the pack `site/` HTML are not in the bundle. Those claims are unverified here. |
| Engineering SoT | [Engineering, Department Definition](https://app.notion.com/p/3f5ef52d77aa811b971ad669f9c67c6e), fetched 2026-10-31, last edited 2026-10-31T21:49:56Z. Section "Foundry v1 CLI design (decisions)". |
| Engineering Rules | [Engineering Rules](https://app.notion.com/p/404ef52d77aa8128b50be5c888929244), fetched the same evening, last edited 2026-10-31T21:49:17Z. |
| This repository | Plugin-compiler tree (`README.md`, `CLAUDE.md`, `docs/`). No governance-pack vocabulary. |

The pack's root `CHECKLIST.md` and `docs/CHECKLIST.md` match. The two `DONE.md` copies differ only by relative links. Pack GAPS and the uploaded GAPS match.

Scores: **Pass** matches the brief and does not fill an open. **Partial** has the right decision and a stale label, a missing sentence, or a diagram that picks a side the prose leaves open. **Fail** disagrees with the brief or with another surface that claims to follow it. **Open-ok** leaves the item open. **N/A** is a different product, or a gaps list that is not supposed to restate the decision.

## 1. Pass and fail per settle item

| Settle item | Brief | Pack | Guided path | GAPS | SoT | Rules | This repo |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VM is the outer box. No host layer. | Pass | Partial | Pass | Pass | Pass | Pass | N/A |
| Foundry node = supervisor + task store + secret store + A2A gateway + harness-facing surface. No separate adapter noun. | Pass | Pass | Partial | Pass | Pass | Pass | N/A |
| Endpoint at `/etc/foundry/endpoints/<name>.yaml`. Agent Card means the A2A object only. | Pass | Pass | Pass | Pass | Partial | Pass | N/A |
| `SendMessage` and artifacts. Large payloads are URLs, where a page discusses size. | Pass on SendMessage. No URL rule in the brief. | Partial | Pass on SendMessage. Silent on size. | Open-ok on size. | Fail | Fail | N/A |
| Two storage tiers, local and shared. Shared scratch. Backends stay open. | Pass | Partial | Pass | Open-ok | Pass | Pass | N/A |
| Git-clone-on-demand workers. Owner stays undecided. | Pass | Fail | Pass | Open-ok | Pass | Pass | N/A |
| Remote tool calls adjacent only. | Pass | Pass | Pass | Pass | Pass | Pass | N/A |
| `foundry join` is the user-facing verb, Control-only. Mode B skips join and uses `foundry mint -f`. | Pass | Pass | Pass | Pass | Partial | Pass | N/A |
| CLI split: top-level `foundry` is the control plane (`foundry start`). `foundry node` is per node (`create`, `start`). | Pass | Fail | Partial | Open-ok | Partial | Pass | N/A |
| `foundry console` is a btop-style TUI, native Vim motions, no web UI. First pane is node fleet status. | Pass | Pass | Fail | Open-ok | Partial | Partial | N/A |
| Harness config multiplicity is unknown and out of v1. | Pass | Partial | Pass | Pass | Pass | Partial | N/A |
| `stop` scope stays open. | Pass | Open-ok | Open-ok | Open-ok | Open-ok | Open-ok | N/A |
| Control-to-node YAML delivery stays open. | Pass | Open-ok | Open-ok | Open-ok | Open-ok | Open-ok | N/A |
| Mode B binary channel stays open. | Pass | Open-ok | Open-ok | Open-ok | Open-ok | Partial | N/A |
| Storage backends stay open. | Pass | Open-ok | Open-ok | Open-ok | Open-ok | Partial | N/A |

### Where a score is not a clean pass

**VM outer box, pack Partial.** Prose in `01-c4-context.md`, `02-c4-containers.md`, `04-deployment-view.md`, and the README says the VM is the outer box and no host layer is drawn. The deployment figure does that: a VM subgraph, a Foundry node subgraph inside it. The C4 level 2 figure fuses them into one boundary named "VM: Foundry node" and puts the local storage tier inside that fused box. The deployment figure puts the local tier inside the VM and outside the node. The Excalidraw report describes the same split the deployment figure uses, and puts the worker outside the node.

**Node composition, guided path Partial.** The settled list at the top names all five parts. The Mode B happy path then says the node comes up as "supervisor + local A2A gateway" and drops the task store, the secret store, and the harness-facing surface. Mode A on the same page keeps the harness-facing surface.

**Agent Card, SoT Partial.** The settled row is right: endpoint path, Agent Card reserved for A2A. The guided-path block on the same page still defers a verb called `card edit`.

**SendMessage, SoT and Rules Fail.** The pack and the guided path both say request and response are `SendMessage` in and artifacts out. The SoT settled table has storage, workers, remote tool calls, and diagram layering, and it has no `SendMessage` row. Rules restates tiers, workers, remote tool calls, and the VM box, and it also omits `SendMessage`. No page in this review states that large artifacts are URLs. The gateway page is the one place size is discussed, and it leaves the choice open: bytes inline, or a reference into the shared tier. That matches the brief, which does not settle a URL rule. It does not match a reading where "large, so URLs" is already decided.

**Storage tiers, pack Partial.** Both tiers and shared scratch are in the prose, and backends are marked open. The container table still assigns "node-local artifacts" to the local tier, while the gateway page says artifact bytes versus a shared-tier reference is open. See placement below for who is drawn talking to shared scratch.

**Git-clone owner, pack Fail.** The pattern name is present and correct. `supervisor.md` says the supervisor is a natural owner and that the placement is not decided. The C4 level 2 figure draws "Workers clone on demand" from the harness-facing surface to the local tier. The deployment figure draws the same edge from the harness-facing surface. The Excalidraw report puts the worker on the VM, outside the node box, and draws no arrow to the harness-facing surface. Three placements, one sentence that says the placement is open.

**CLI split, pack Fail, guided path Partial, SoT Partial.** The brief's control-plane example is `foundry start`. Join is a separate rule (Control-only). Console is a separate rule (the TUI). Mint is spelled `foundry mint -f` and is not given a third command family.

| Page | What it assigns |
| --- | --- |
| `docs/06-audit.md` | Control plane examples: `foundry start`, `foundry console`. Join is absent from that cell. |
| README settled list | Control plane examples: `foundry start`, `foundry console`, `foundry join`. |
| `installer.md` CLI table, headed "Examples (settled)" | Control plane row includes `foundry join`. A third row gives `foundry mint -f` its own surface. |
| `console.md` | Calls `foundry console` the control-plane side of the split. |
| Guided path | Matches the brief for `foundry start` versus `foundry node start`. Then says where `status`, `logs`, `doctor`, `config`, and `mint` sit is open, while every example spells `foundry mint` at top level. |
| SoT settled row | Matches the brief. |
| SoT guided-path summary | Mode A is still `foundry join`, then `foundry start` (control plane) / node start as applicable, then mint. The draft this summary points at already changed node start to `foundry node start`. |

**Console, guided path Fail.** `console.md` settles the TUI, btop, Vim, and the first pane, and it leaves Mode B open: what the console shows with no Control, and whether it can target one node. GAPS items 6, 7, and 8 say the same. The guided path glance table marks the console Control-only and not available in Mode B. The Mode B copy-paste story says "No foundry console". That closes an open. `00-vision.md` also states, unqualified, that the console talks only to the Control API and does not open a socket to a VM. `console.md` still has that single-node path as an open question.

**Console, SoT and Rules Partial.** The settled values (TUI, btop, Vim, first pane, rejected command names) are right. The SoT row is still titled "Dashboard / UI command". Rules still says "Dashboard command is `foundry console`". The SoT unspecified list still says "Mode B A2A client without dashboard".

**Multiplicity, pack Partial, Rules Partial.** `harness-facing.md` and GAPS say "one mapping per harness family" is a drawing convenience. `01-c4-context.md` states "one mapping per harness family" as the description of the component, with no convenience label. Rules and the SoT unknown-table both say "two harnesses on one host", which reintroduces "host" in the sentence that records the cancelled investigation.

**Rules Partial on two opens.** Rules names `stop` and Control-to-node YAML as still open. It does not restate the Mode B binary channel or storage backends. The SoT open list has all four. The pack and the guided path have all four.

**This repository, N/A on every row.** It is the plugin compiler. A search of the tree found none of: adapter, enroll, dashboard, host layer, Agent Card, `foundry join`, `foundry console`. The pack records that name collision and leaves it unresolved. This review does not resolve it either.

### Opens that stayed open

These four are flagged and not filled in the pack, the guided path, or the SoT open list:

| Open | Where it stays open |
| --- | --- |
| `stop` scope: local processes only, or also mark the node unavailable at Control | `supervisor.md`, installer CLI table, GAPS 1, guided path step 5, SoT open list, Rules |
| How endpoint YAML gets from Control to a node | Installer Mode A row, GAPS 2, guided path step 4, SoT open list, Rules |
| How a Mode B binary is distributed | Installer Mode B row, GAPS 3, guided path step 1, SoT open list. Rules omits it. |
| Storage backends, and where the shared tier lives | Containers store table, deployment prose, GAPS 4, guided path, SoT. Rules omits it. |

GAPS 5 through 14 are extra opens found while editing (join chained inside `curl | bash`, console transport, Mode B console, pane order, Mode B A2A client, artifact bytes versus a reference, worker owner, shared-scratch access, harness-at-install versus mint, and carried-over crypto and token questions). None of those are answered in the pack. The guided path adds one recommendation the brief does not contain: Mode B should still mint a machine key. That sentence is marked unspecified, then says "recommend yes".

Nothing in the pack CHECKLIST marks implementation done. Section H leaves "Opens resolved by Pi" and "Any implementation" unchecked. README, DONE, and each system page say design only.

## 2. Contradictions and stale names

| Stale or split name | Where it still lives | What the brief requires |
| --- | --- | --- |
| `foundry join` classified as a control-plane command | README settled list. Installer CLI table. | Join is Control-only. The control-plane example is `foundry start`. |
| `foundry mint` given a settled third surface, and also called an open placement | Installer table versus guided path item 11 | The brief spells `foundry mint -f`. It does not settle which family owns mint. |
| Mode A install still runs `foundry start` in the node path | SoT guided-path summary | Node start is `foundry node start`. The draft already says this. The SoT summary of that draft does not. |
| Console unavailable in Mode B | Guided path glance table, happy path, and copy-paste story. Vision line that the console talks only to the Control API. | Mode B console behavior is open. `console.md` and GAPS 7 say so. |
| "Agent up" | SoT guided path, start/status for Mode A and Mode B | The machine unit is a node. "Node agent" is retired in `supervisor.md`. |
| `card edit` | SoT deferred verbs | The config noun is endpoint. Agent Card is the A2A object. |
| "Dashboard / UI command" and "Dashboard command" | SoT row title. Rules bullet. | Rejected names include dashboard. The command is `foundry console`. |
| "without dashboard" | SoT unspecified list, Mode B A2A client | The open is the Mode B client, already in GAPS 9. The word dashboard is the old surface. |
| "enrolled-node" and "POST enroll" | SoT lede. SoT guided path join line. | User-facing verb is `foundry join`. An internal path can stay, and it has to be labeled as a proposal. |
| `POST /v1/machines/enroll`, `machine.enrolled` | `control-api.md`, `audit.md`, installer figure, install sequence | Flagged on purpose in GAPS and in the installer prose. Left as an older proposal. Safe only while every use says the user verb is `foundry join`. The SoT line "POST enroll" does not. |
| "Supervisor / node agent" | Excalidraw report, edge deck frame 3, reported unchanged | `supervisor.md` retires "node agent". |
| `site/wireframe/dashboard.html` | Named in CHECKLIST, DONE, GAPS, `console.md` | Kept as a superseded record, according to those pages. The HTML is not in the bundle, so the banner was not checked. |
| "Host detect", "detect host", "on the host", "control host" | Installer component, install sequence, installer token note, `07-poc.md` | These mean OS detection or the machine that serves Control. They are easy to read as the removed host layer. Low priority. "On one host" in the multiplicity sentence is the one to change first. |
| `hybroai/a2a-adapter` and the rejected-noun list | `harness-facing.md`, `06-audit.md` | Historical and third-party. Acceptable. The product noun is gone from pack prose. |
| Installer flags `--harness`, `--role`, required at install | Installer flags table, README operator story bash block, vision steps 2 to 4 | GAPS says this table predates the CLI split and that harness-at-install versus harness-at-mint is open. The README story still shows `--harness` as the path. |
| "one mapping per harness family" with no caveat | `01-c4-context.md` actors table | Unknown, out of v1. The harness-facing page already has the caveat. Context does not. |

User-facing "enroll" as the command name is gone from the pack and from the guided path. The guided path still cites `POST /v1/machines/enroll` and labels it a proposed resource. That matches the pack's flag.

## 3. Placement calls still unresolved

From the Excalidraw report. The report says these were flagged and not invented as decisions. The pack then drew some of them anyway.

| Call | Excalidraw report | Pack |
| --- | --- | --- |
| Where the git-clone worker sits | On the VM, in the local tier, outside the node box. No arrow to the harness-facing surface. | `supervisor.md` says the owner is not decided and names the supervisor as a natural owner. C4 level 2 and the deployment figure both draw the clone from the harness-facing surface. |
| What backs the shared tier | Labeled only "off-VM". | Same. Backend and location marked open. The figure places it outside both VMs and says that is only to show it is not one node's disk. |
| Harness-facing surface and the worker | No arrow, because it is not decided. | Arrows exist. See the row above. |
| Console to Control, and Mode B | The console-to-Control-API arrow carries the earlier "dashboard talks only to Control" design. Mode B is not drawn. | Deployment puts the TUI in the operator zone with an arrow to the Control API, and says transport and auth are open. C4 level 2 puts `foundry console` inside the Foundry Control boundary. Mode B has no C4 view and no sequence. GAPS 41 says so. |
| Endpoint path, join, `mint -f`, YAML delivery, CLI split | Not drawn. Report says they are outside that diagram. | In prose. YAML delivery still open. CLI split disagrees across pages, section 2. |
| Edge deck frame 3 | Still "Supervisor / node agent". | Supervisor page retires that name. |
| Excalidraw collection named Foundry | Not possible with this connector. Tools are create view, export, read checkpoint, save checkpoint. No collection API. Anonymous json.excalidraw.com upload has no collections. No collection URL. | Not a pack question. |

Two further placement splits are inside the pack, and the Excalidraw report did not settle them:

| Call | What the figures say |
| --- | --- |
| Local tier inside the node or beside it | C4 level 2: inside the fused "VM: Foundry node" box. Deployment: inside the VM, outside the node subgraph. Excalidraw: outside the node, and the report notes that the task store and the secret store are also local. |
| Who reads and writes shared scratch | C4 level 2 draws the gateway to the shared tier, label "mechanism open". Deployment draws the same gateway edge and the prose says the edges are placeholders. GAPS 12 says the component and the access rules are open. |

## 4. Recommended fixes, in priority order

Design text only. Do not invent a mechanism while renaming.

| Priority | Fix |
| --- | --- |
| 1 | One CLI table, copied into the README, `06-audit.md`, `installer.md`, the guided path, and the SoT summary. `foundry start` starts the control plane. `foundry node create` and `foundry node start` are per node. `foundry join` is Control-only and is not described as the control plane. `foundry console` is the TUI. `foundry mint` and `foundry mint -f` keep today's spelling, and the family they belong to stays open. Remove "Examples (settled)" from any row the brief did not settle. Update the SoT guided-path summary so Mode A node start is `foundry node start`, matching the draft. |
| 2 | Worker and shared scratch: delete the owner from the arrows until Pi decides. `supervisor.md`, C4 level 2, the deployment figure, and the Excalidraw layers should describe the same undecided state. The Excalidraw choice (worker on the VM, outside the node) and the pack choice (arrow from the harness-facing surface) cannot both stand. |
| 3 | Guided path Mode B: put the console back to open. Session bind, policy pin, and the fleet registry can stay Control-only, which is what `console.md` already says. Delete "console is not available". Soften the vision sentence that the console talks only to the Control API, so it matches the open single-node question. |
| 4 | Add `SendMessage` and artifacts to the SoT settled table and to Rules. Leave large-payload transport as the gateway page has it: inline bytes versus a shared-tier reference, open. Do not write a URL rule unless Pi settles one. |
| 5 | Stale labels, live text only. SoT: retitle the console row, replace `card edit`, replace "enrolled-node", replace "Agent up", label or drop "POST enroll", replace "without dashboard". Rules: replace "Dashboard command" and "on one host". Excalidraw frame 3: replace "Supervisor / node agent". Context page: add the drawing-convenience label on "one mapping per harness family". |
| 6 | C4 level 2: draw the VM as the outer box and the Foundry node inside it, the way the deployment figure and the Excalidraw layers already do. Put the local tier where that decision lands, once, in both figures. |
| 7 | Leave these untouched until a decision exists: `stop` scope, Control-to-node YAML delivery, Mode B binary channel, storage backends, console transport and auth, pane order after the first pane, Mode B A2A client configuration. Rules should mention the binary channel and the backends so the open list matches the SoT. |
| 8 | README operator story and the installer flags table: mark `--harness` and `--role` as the pre-split proposal, the way GAPS already does. Verify `site/wireframe/dashboard.html` still carries the superseded banner. The bundle did not include `site/`. |

## 5. Design only, not shipped

This review is a consistency check of design text. It does not mark the governance pack, the CLI, the console, the node, or the diagrams as shipped. The pack itself leaves implementation unchecked. The SoT says the CLI record is design-only until Pi says to apply an implementation. No product code was written for this review.

Surfaces this review did not execute: the pack static site, the Excalidraw files, and a collection in Excalidraw. The Excalidraw report's collection conclusion stands as reported: the connector cannot create one.
