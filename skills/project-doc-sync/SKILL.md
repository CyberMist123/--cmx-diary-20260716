---
name: project-doc-sync
description: Synchronize completed implementation changes and confirmed design decisions into PI OS canonical project documents.
---

# Project Doc Sync

Keep the next agent from relearning the project from scratch. Correct the current facts in place; do not write a narrative about the session.

## Trigger

Run after implementation or a confirmed design decision when at least one changed:

- requirement or acceptance condition
- implemented feature or user-visible behavior
- scope boundary or explicit non-goal
- architecture, module responsibility, data ownership, or deployment topology
- exact interface name: endpoint, port, env key, service, script, task, command, path, token scope
- operational flow: setup, startup, upload, domain switch, backup, restore, failure handling
- current state, verification state, progress table, or next executable step

Do not run for formatting, comments, tests-only changes, or internal refactors that preserve all documented facts and interfaces.

## Source of truth for the delta

Use only:

1. the originating user request, issue, or accepted plan
2. the actual changed files or diff
3. verification output from the completed work
4. the existing canonical documents below

Do not rescan the whole repository to reconstruct architecture. Do not describe an unimplemented plan as current behavior.

## Canonical document ownership

### Primary current-facts file

- `PROJECT.md` — **must stay current**. It owns project purpose, confirmed requirements, boundaries, current architecture, exact interfaces, data ownership, operational flows, progress table, verification state and next step.

### Detailed documents

Update only when their owned detail changed:

- `docs/MVP_SCOPE.md` — detailed requirements, acceptance criteria, boundaries and non-goals.
- `docs/ARCHITECTURE.md` — component responsibilities, data flow, topology and storage ownership.
- `docs/DEPLOYMENT.md` / `docs/CLOUDFLARE.md` / `docs/RESTORE.md` — exact operator procedures.
- `docs/MUTABLE_WEB_DOMAIN_RFC.md` — accepted mutable-`WEB_DOMAIN` design and its safety constraints.
- `README.md` — public entry point and navigation only.
- current GitHub issue — checklist, remaining work and status.

### Entry pointers

- `AGENTS.md` points agents to `PROJECT.md` and defines execution discipline.
- `AI_HANDOFF.md` is a compatibility pointer only. Do not put a second project state there.

Do not create another `STATUS.md`, `PROJECT_STATE.md`, architecture summary, handoff copy or duplicate TODO list.

## Process

### 1. Extract the fact delta

List only concrete before → after facts supported by accepted decisions, changed files or verification. Classify under:

- requirement / feature
- boundary
- architecture
- interface name
- flow
- current state / verification state

If no category changed, stop and report `No project documentation sync required.`

### 2. Update `PROJECT.md` first

For every changed fact:

- replace stale text instead of appending a second version
- use exact identifiers copied from code/configuration
- distinguish `计划中`, `已实现/未实测`, and `已运行验证`
- update the progress table and next step
- keep rationale only when it prevents a future agent from undoing a hard boundary

### 3. Update affected detail documents

- update diagrams or flow blocks when routes or responsibilities changed
- remove obsolete commands, names, ports, paths and client assumptions
- do not mechanically rewrite unrelated documents
- update the active Issue when checklist or remaining work changed

### 4. Check drift

Search canonical documents for identifiers made stale by this task. Resolve contradictions caused by this task.

Confirm that:

- one concept has one canonical name
- `PROJECT.md` and the implementation agree
- planned functionality is not described as deployed
- unverified GitHub code is not described as runtime-proven
- sensitive values are absent
- links and referenced filenames exist

### 5. Finish with a compact sync report

Return:

```text
Project doc sync
- Updated: <files and changed facts>
- Unchanged: <canonical files checked but not affected>
- Evidence: <accepted decision, changed files, or runtime verification>
- Remaining uncertainty: <real unverified facts, or none>
```

The report is not a new repository document.

## Common failure modes

- copying the conversation or diff into docs
- adding a changelog instead of correcting current facts
- describing planned CMX/AI/MCP work as implemented
- claiming local deployment passed without target-machine output
- preserving both Mastodon App and CMX-browser architectures
- treating `ALTERNATE_DOMAINS` as a complete origin migration mechanism
- changing interface names in prose without matching code
- creating extra handoff/status documents instead of updating `PROJECT.md`