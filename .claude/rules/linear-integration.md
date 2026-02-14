# Linear Integration Protocol

**Project:** NotesApp | **Team:** Azdigi | **Tool prefix:** `mcp__linear__`

## Core Principle

All work MUST be tracked in Linear. Every bug found, feature built, and task completed must have a corresponding Linear issue with full history via comments.

## Linear Context (MANDATORY for subagents)

When spawning any subagent, include in prompt:
```
Linear context:
- Team: Azdigi
- Project: NotesApp
- Use mcp__linear__* tools for issue tracking
```

## Agent Responsibilities

### Tester Agent
- **On test failure:** Create Linear issue with label `Bug`, priority based on severity
  - Urgent (1): app crash, data loss, auth bypass
  - High (2): feature broken, wrong behavior
  - Medium (3): edge case failure, minor regression
  - Low (4): cosmetic, non-blocking
- **Issue content:** failing test name, error output, affected file, reproduction steps
- **On all tests pass:** Comment on related issue(s) confirming tests pass

### Code Reviewer Agent
- **On critical finding:** Create Linear issue with appropriate label (`Bug`, `Security`, `Performance`)
- **On review complete:** Comment on the feature's Linear issue with review summary
- Include: approved/changes-requested, key findings, suggestions

### Debugger Agent
- **On bug identified:** Create Linear issue if not exists, or comment on existing issue with root cause analysis
- **On fix applied:** Update issue status to `In Review`, add comment with fix description
- **On fix verified:** Update issue status to `Done`

### Project Manager Agent
- **On milestone check:** Comment on project with progress summary
- **On blocker found:** Create issue with `Urgent` priority, link as `blockedBy`
- **On phase complete:** Update milestone, comment with completion summary

### Planner Agent
- **On plan created:** Create Linear issues for each phase/task in the plan
- Link issues with `blocks`/`blockedBy` for dependency tracking
- Set milestones and priority based on plan phases

### Docs Manager Agent
- **On docs updated:** Comment on related issue noting which docs changed

## Issue Lifecycle

```
Backlog → Todo → In Progress → In Review → Done
                                    ↓
                                Canceled/Duplicate
```

### Status Transitions
| Action | From | To | Who |
|--------|------|----|-----|
| Start working | Backlog/Todo | In Progress | implementer |
| Submit for review | In Progress | In Review | implementer |
| Review passed | In Review | Done | reviewer/tester |
| Review failed | In Review | In Progress | reviewer |
| Bug discovered | (new) | Backlog | tester/debugger |
| Won't fix | any | Canceled | project-manager |

## Comment Format

All Linear comments MUST follow this format:
```markdown
**[Agent: <agent-type>]** <action>

<details>

---
*Session: <date> | Branch: <branch-name>*
```

**Example:**
```markdown
**[Agent: tester]** 3 tests failing in auth module

- `test_jwt_validation`: ES256 key fetch timeout
- `test_expired_token`: wrong error code (400 vs 401)
- `test_missing_header`: passes

---
*Session: 2026-02-14 | Branch: feat/auth-tests*
```

## When to Create vs Comment

| Scenario | Action |
|----------|--------|
| New bug discovered | Create issue |
| Bug in existing issue scope | Comment on issue |
| Feature task from plan | Create issue |
| Progress update | Comment on issue |
| Test results | Comment on related issue |
| Code review findings | Comment on related issue |
| Blocker or dependency | Create issue + link with `blockedBy` |

## Issue Templates

### Bug Report
```
Title: [Bug] <short description>
Labels: Bug
Priority: <1-4 based on severity>
Description:
**What:** <what's wrong>
**Where:** <file:line or endpoint>
**Expected:** <expected behavior>
**Actual:** <actual behavior>
**Steps:** <reproduction steps>
```

### Feature Task
```
Title: <imperative description>
Labels: Feature
Priority: <1-4>
Milestone: <phase milestone>
Description:
**Goal:** <what to achieve>
**Files:** <files to modify/create>
**Acceptance:** <definition of done>
```

## Workflow Integration

### Starting a Task
1. Find or create Linear issue
2. Update status → `In Progress`
3. Assign to `me`
4. Work on the task

### Completing a Task
1. Comment with implementation summary
2. If tests pass → status `In Review`
3. If review passes → status `Done`
4. If tests/review fail → stay `In Progress`, comment with findings

### Session End
Before ending any session that touched Linear issues:
- Comment on all in-progress issues with current state
- Note any blockers or next steps
- Do NOT leave issues in `In Progress` without a status comment
