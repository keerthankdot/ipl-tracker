# CODEBIBLE.md
### The Ascnd Builder's Law for AI-Assisted Development
> Maintained by KDOT. Updated after every session where something goes wrong or right.
> Inspired by Boris Cherny's Claude Code principles, adapted for solo founder building in Cursor IDE.
> Sources: Boris Cherny workflow, Simon Willison agentic engineering patterns, HumanLayer context engineering research, Anthropic official best practices, DataCamp production workflow analysis.

---

## 0. The One Rule That Governs All Others

**You are not a coder. You are a director of a system that ships software.**

Stop asking: "How do I get a better output from this prompt?"
Start asking: "How do I build a system where good output is the default?"

Every principle below serves that shift.

---

## 1. BEFORE YOU WRITE A SINGLE LINE

### 1.1 Read This File
You are reading it. Good.

### 1.2 Define the System in One Sentence
Before opening a chat, write one sentence:
> "I am building [X] that does [Y] for [Z]."

If you cannot write that sentence, you are not ready to build. Go think first.

### 1.3 State the Stack Upfront
Tell Claude the stack at the start of every session, every time. Do not assume it remembers.

Example opener:
```
Stack: React + Vite + Tailwind + TypeScript
Package manager: bun (never npm, never yarn)
Deployment: Vercel
This project is [name]. Here is what it does: [one sentence].
Now let's work on: [specific task].
```

---

## 2. THE PLANNING LAW

### 2.1 The One-Sentence Rule
Before Plan Mode: can you describe the diff in one sentence?

- **Yes** → skip Plan Mode, just do it directly.
- **No** → Plan Mode is mandatory.

This is the fastest heuristic for knowing when planning overhead pays off and when it wastes time.

### 2.2 Plan Mode Is Mandatory for Every Non-Trivial Task
Before Claude writes a single line of code, it must produce a plan.

**Trigger phrase to use every time:**
> "Before doing anything, give me a plan. List every file you will touch, every decision you will make, and flag any ambiguity. Do not write code until I approve the plan."

Use Plan Mode specifically for: new features, multi-file changes, unfamiliar code, architectural decisions, and any refactor that touches more than one file. The overhead is a few extra minutes upfront. It prevents Claude from spending 20 minutes confidently solving the wrong problem.

### 2.3 What a Good Plan Contains
- Every file that will be created or modified
- Every architectural decision being made and why
- Any ambiguity flagged with a question
- The order of operations (what happens first, second, third)
- Tests interleaved with implementation, NOT all at the end
- What "done" looks like and how it will be verified

**IMPORTANT: Plans that put all implementation steps first and tack on "add tests" at the end produce worse results.** Without tests during implementation, Claude has no feedback loop mid-session. A stronger plan interleaves testing: write tests for auth/ before extracting auth functions, confirm they pass, then move to the next module.

### 2.4 Push Back on the Plan Before Approving
Never approve the first plan blindly. Ask at least one of:
- "What could go wrong with this approach?"
- "Is there a simpler way to do this?"
- "What are you assuming that I haven't confirmed?"

Only after refinement: "Plan approved. Proceed."

### 2.5 Save Plans as Files for Complex Work
For any feature that spans multiple sessions or is architecturally significant, save the plan as a markdown file:

```
.claude/plans/2026-03-25-feature-name.md
```

Plans stored in version control serve as decision records. They capture why you built something a certain way, not just what you built. That context is invaluable during debugging and revisits. They also survive context compaction — which conversational plans do not.

### 2.6 When Things Go Sideways, Return to Plan
If Claude starts producing wrong output or going in circles: stop. Do not keep pushing.
Say: "Stop. Let's re-plan. Forget the last approach. Given what we now know, what's the right plan?"

---

## 3. THE VERIFICATION LAW

### 3.1 "Done" Does Not Mean Written. It Means Verified.
Claude is not finished when the code is written. Claude is finished when the code is confirmed to work.

**Every task must end with a verification step. No exceptions.**

### 3.2 TDD Is the Strongest Verification Pattern
Test-Driven Development gives Claude an unambiguous feedback loop and is the single strongest pattern for agentic coding. The sequence:

1. Write tests first: `"Write tests for [module] using [framework]. TDD approach, no mock implementations yet."`
2. Confirm tests fail: `"Run the tests. They should all fail right now."`
3. **Commit the failing tests as a checkpoint** — this is critical. If Claude later alters the tests to make them pass instead of fixing the implementation, the diff will show exactly what changed and you can revert.
4. Implement until green: `"Write the implementation. Do not modify the tests. Keep going until all tests pass."`

**Warning:** Claude will sometimes change tests to make them pass rather than fixing the implementation. The commit-before-implement step is your protection against this.

### 3.3 Standard Verification Closers
Add one of these to the end of every prompt:

| Task Type | Verification Command |
|---|---|
| Any code change | `bun run typecheck` then `bun run lint` |
| UI change | "Open the browser, check the component renders correctly, check mobile size" |
| New feature | "Run the relevant tests. If none exist, write one and run it." |
| Bug fix | "Reproduce the original bug first, then confirm it no longer occurs" |
| API/backend | "Run the endpoint and show me the response" |
| Refactor | "Confirm all existing tests still pass after the change" |

### 3.4 Visual Verification for UI Work
For frontend changes, the visual loop is the equivalent of TDD:

1. Give Claude a design mock or screenshot of the target state
2. Claude implements in code
3. Claude takes a screenshot of the result
4. Compare to mock and iterate
5. Usually 2-3 iterations for a strong match

This is what Boris does with the Chrome extension for every claude.ai/code UI change. In Cursor, the equivalent is: give Claude the target, have it open the browser, check the result, and iterate until it matches.

### 3.5 The Verification Phrase
Always end complex prompts with:
> "Once you've made the changes, verify by running [X]. Show me the output before calling this done."

### 3.6 Never Accept "It Should Work"
If Claude says "this should work" or "that should fix it" without running anything, respond:
> "Don't tell me it should work. Run it and show me it does."

---

## 4. THE MEMORY LAW

### 4.1 The Four-Layer Memory Architecture
Claude Code now has four distinct memory layers. Understanding all four is required to use memory correctly.

| Layer | What It Is | Who Writes It | When It Loads |
|---|---|---|---|
| **CODEBIBLE.md** | Universal law across all projects | You | Every session (upload manually) |
| **CLAUDE.md** | Project-specific rules and context | You | Every session (auto-loaded from root) |
| **MEMORY.md** (Auto Memory) | Claude's own notes from working sessions | Claude | Every session (auto-loaded, 200-line cap) |
| **Auto Dream** | Periodic consolidation of MEMORY.md | Background subagent | Between sessions (not yet GA) |

The strongest setup runs all four. An instruction manual (CODEBIBLE + CLAUDE.md), a note-taker (Auto Memory), and a consolidation cycle (Auto Dream). Right now layers 1-3 are fully available. Layer 4 is in phased rollout.

### 4.2 This File IS the Memory
Claude has no memory between sessions. This file is the universal memory. Every important decision, pattern, and mistake lives here. Keep it updated.

### 4.3 After Every Correction, Add a Rule
When Claude does something wrong and you correct it, end with:
> "Add this as a rule to CODEBIBLE.md so you never make this mistake again."

Then actually add it to Section 13 (Learned Rules) of this file.

### 4.4 CLAUDE.md Per Project
Every project also gets its own CLAUDE.md at the root. The CODEBIBLE is the universal law. The project CLAUDE.md is the project-specific law. Both must be uploaded at the start of every session.

Project CLAUDE.md should contain:
- Project-specific stack details
- File structure map
- Naming conventions for this project
- What has already been built (brief)
- What is being built right now

### 4.5 Auto Memory: Enable It and Understand Its Limits

Auto Memory (available from Claude Code v2.1.59+) lets Claude take its own notes as it works. It captures build commands, debugging insights, architecture decisions, and your preferences without you writing anything manually.

**Enable it:** Run `/memory` in any session and confirm the Auto Memory toggle is on. It defaults to on for most installations, but worth verifying.

**The hard limit — CRITICAL:** Only the first 200 lines of MEMORY.md load at session startup. The index also truncates at 25KB. Anything beyond either cap is silently invisible to Claude at the start of every session. A MEMORY.md that grows past 200 lines is actively harmful — Claude references an index that doesn't reflect its actual knowledge.

**Check and prune manually:** Periodically open `~/.claude/projects/<your-project>/memory/MEMORY.md` and review it. If it's past 150 lines, prune it. Keep only entries that are still true, still relevant, and specific enough to be useful. Delete anything stale, contradicted, or redundant.

**Explicit saves work:** During a session, say "remember that we use pnpm, not npm" or "note that the API tests require a local Redis instance." Claude writes it to MEMORY.md immediately. Use this actively rather than relying on Claude to infer what's important.

### 4.6 After Major Refactors, Manually Consolidate Memory

When you rename large parts of the codebase, migrate frameworks, change your API structure, or make any change that makes a significant chunk of past memory wrong, say this directly to Claude:

> "Consolidate my memory files. Remove anything that's no longer accurate, convert relative dates to absolute dates, and merge any duplicate entries."

This works even without Auto Dream being live. Claude will review MEMORY.md and clean it up in that session. Old entries that reference deleted files, outdated patterns, or superseded decisions cause more confusion than clarity. Don't let them accumulate.

### 4.7 Auto Dream (Coming — Not Yet GA)

Auto Dream is a background subagent that consolidates MEMORY.md between sessions, running a four-phase cycle: orient, gather signal from session transcripts, consolidate and de-duplicate, prune index to under 200 lines.

**Current status (March 2026):** Infrastructure is built into Claude Code v2.1.59+. It appears as a toggle in `/memory` but cannot be activated by most users yet. It's behind a server-side feature flag in phased rollout.

**Trigger conditions when live:** Requires both 24 hours elapsed AND 5 sessions accumulated since last consolidation. The dual-gate prevents unnecessary runs on light-use projects.

**Check your status:** Run `/memory`. If you see "Auto-dream: on" or "Auto-dream: off", the feature is available in your installation. If you see the toggle but it won't activate, the manual workaround is: "consolidate my memory files" said directly to Claude in any session.

**Before it touches your memory:** Back up `~/.claude/projects/<project>/memory/` first. There is no undo mechanism. Copy the folder to a backup location before the first consolidation run.

**When it goes GA:** Auto Dream will become the primary maintenance mechanism for MEMORY.md. The manual consolidation step in 4.6 will become something you do only when you want to force an immediate cycle. Until then, 4.6 is your fallback.

## 5. THE CONTEXT LAW

### 5.1 Context Degradation Is the Primary Failure Mode
The most successful Claude Code users obsessively manage context. When the context window fills, models are more likely to forget early constraints, misread requirements, and make detail-level mistakes. This is not a limitation to work around. It is the central engineering problem of agentic coding.

### 5.2 The /clear and /compact Protocol
- `/compact` when context usage exceeds ~80% but you're still on the same task. Add focus instructions: `/compact retain the auth flow and the list of modified files`.
- `/clear` when switching to a completely different task entirely. Old context from a previous task will confuse the next one.
- Give Claude a standing instruction in CLAUDE.md: `"When compacting, preserve the full list of modified files and current test status."`

**Never let context fill to 100% silently.** Check `/context` or `/cost` every 15-20 minutes during active agentic sessions. Token usage spikes during loops where Claude reads files, edits, runs tests, and iterates.

### 5.3 Fresh Context for Reviews
A fresh context improves code review quality because Claude won't be biased toward code it just wrote. Use the Writer/Reviewer pattern:

- Session A writes the code.
- Session B (fresh, no prior context) reviews what Session A produced.
- Session C, informed by both, edits based on the review.

This is one of the highest-leverage uses of parallel sessions.

### 5.4 Skills Over CLAUDE.md for Domain-Specific Knowledge
CLAUDE.md loads on every session. Skills load only when relevant. If you have specialized domain knowledge that matters sometimes but not always (API patterns, deployment steps, a specific library's quirks), put it in a skill file at `.claude/skills/`, not CLAUDE.md.

This keeps CLAUDE.md lean and prevents irrelevant context from diluting the instructions Claude actually needs to follow.

### 5.5 The Instruction Budget
CLAUDE.md is advisory, not guaranteed. Research shows frontier thinking models can reliably follow roughly 150-200 instructions. Claude Code's system prompt already uses about 50 of those. Your CLAUDE.md shares the remaining budget with every other instruction in the session.

Implication: every unnecessary line in CLAUDE.md actively reduces Claude's compliance with the lines you care about. Keep it short. If Claude keeps ignoring a rule, the file is probably too long — not the rule too weak.

---

## 6. THE ARCHITECTURE LAW

### 6.1 Finish What You Start
Never leave a migration half-done. Never have two frameworks doing the same job in the same codebase. Partially-migrated code confuses both humans and AI.

Rule: **If you start moving from X to Y, you finish moving everything from X to Y in that session.**

### 6.2 File Structure Is a Decision, Not a Default
Before creating files, decide the structure. State it explicitly.

Standard Ascnd project structure unless specified otherwise:
```
/src
  /components      # UI components, one file per component
  /pages           # Page-level components
  /hooks           # Custom React hooks
  /utils           # Pure utility functions
  /lib             # Third-party integrations
  /types           # TypeScript type definitions
  /styles          # Global styles only
/public
CODEBIBLE.md
CLAUDE.md          # Project-specific rules
```

### 6.3 One Pattern Per Problem
Do not allow multiple solutions to the same problem in one codebase. If you're using Zustand for state, everything uses Zustand. If you're using React Query for fetching, everything uses React Query. Inconsistency is a tax on every future session.

### 6.4 Simplify After Building
After the feature works: run a simplification pass.

Prompt:
> "The feature works. Now simplify. Look for: duplicate code, unnecessary abstraction, files that should be merged, logic that's harder than it needs to be. Propose the simplifications before making them."

### 6.5 No Over-Engineering
Claude will sometimes build for scale you don't need yet. Catch this early.

If a solution feels complex for the problem size, say:
> "This feels over-engineered for what we need right now. What's the simplest version that works? We can add complexity later when we actually need it."

---

## 7. THE PROMPTING LAW

### 7.1 Specificity Is Respect for Your Own Time
Vague prompts produce vague results. Every prompt should contain:
- What you want (the outcome)
- What you don't want (the constraints)
- What "done" looks like (the verification)

**Bad:** "Fix the login bug"
**Good:** "The login button is not redirecting after successful auth. It should redirect to /dashboard. Check the auth callback handler first. Show me the issue before fixing it. After fixing, verify by running the auth flow."

### 7.2 Challenge Claude, Don't Accept the First Solution
After a mediocre fix or output, use:
> "Knowing everything you know now, scrap this and implement the elegant solution."

Or:
> "Prove to me this works. Show me the difference between the old behavior and the new behavior."

Or:
> "Grill me on this approach. What are the weaknesses? What would a senior engineer question?"

Or:
> "Grill me on these changes and don't make a PR until I pass your test."

### 7.3 Reduce Ambiguity Before Handing Off
The more specific the brief, the better the output. If you're about to hand Claude a large task, spend 5 minutes writing a clear spec first. It saves 30 minutes of back-and-forth.

A good spec contains: the outcome you want, the constraints you have, the patterns already in the codebase to follow, and what "done" looks like.

Example of a strong spec for a UI change:
```
Create a user settings page at /settings with:
- Profile section (name, email, avatar upload)
- Notification preferences (checkboxes for email/push)
- Use existing UserProfile component pattern
- Follow the MUI v7 layout grid system already in place
- Add tests for form validation
```

### 7.4 Don't Micromanage the How
Tell Claude what you want to achieve, not every step of how to achieve it.

**Bad:** "Go to line 47, change the variable name, then update the import, then..."
**Good:** "Rename all instances of `userObj` to `user` across the codebase. Verify nothing breaks after."

### 7.5 Use Two Claudes for Complex Decisions
For important architectural decisions:
1. Claude 1: "Here is the problem. Give me three possible approaches with tradeoffs."
2. You review the options.
3. Claude 2 (fresh chat): "Here is the approach we're taking and why. Now implement it."

Separation of planning and execution produces cleaner results.

### 7.6 Use Voice for Better Prompts
You speak 3x faster than you type, and your prompts become significantly more detailed as a result. On Mac: double-tap `fn` to activate system dictation. Give Claude a full verbal brief instead of a short typed prompt. The more context Claude has upfront, the less steering it needs during execution.

---

## 8. THE PARALLELIZATION LAW

### 8.1 One Task Per Session
Each Claude chat session should have exactly one job. Do not pile multiple features into one session.

Name your sessions mentally:
- Session A: Building the feature
- Session B: Writing tests for the feature
- Session C: Simplifying/refactoring after the feature works

### 8.2 Use Worktrees for True Parallel Work
When working on multiple things simultaneously, use git worktrees so each Claude session has its own clean branch with no file conflicts:

```bash
git worktree add .worktrees/feature-name origin/main
cd .worktrees/feature-name
# Open in second Cursor window, run Claude Code here
```

### 8.3 The Dedicated Analysis Session
Keep one Cursor window/session reserved for reading: checking logs, reviewing what the other sessions built, running analytics queries. This session never writes code. It only reads and reports.

---

## 9. THE AUTOMATION LAW

### 9.1 Automate Everything That Doesn't Require a Creative Decision
Lint, format, typecheck, test runs. These are not judgment calls. They are mechanical. Automate them.

Required setup for every Ascnd project:
- Format on save: ON in Cursor
- Pre-commit hook: lint + typecheck before every commit
- Claude always runs `bun run typecheck && bun run lint` before calling a task done

**CLAUDE.md is advisory (~80% compliance). Hooks are deterministic (100%).** If something must happen without exception — formatting, security checks, blocking dangerous commands — put it in a hook, not CLAUDE.md.

### 9.2 Essential Hooks to Set Up on Every Project

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [{ "type": "command", "command": "bun run format || true" }]
      }
    ]
  }
}
```

Add a PreToolUse hook to block dangerous commands:
```json
"PreToolUse": [
  {
    "matcher": "Bash",
    "hooks": [{ "type": "command", "command": "echo $TOOL_INPUT | grep -q 'rm -rf' && exit 2 || true" }]
  }
]
```

### 9.3 Build Slash Commands / Skills for Repeated Workflows
Any workflow you run more than twice per week becomes a saved skill in `.claude/skills/`.

Starter skills to build:
- `/commit`: typecheck, lint, write commit message, push
- `/simplify`: review the last feature for over-engineering and reduce it
- `/techdebt`: scan for duplicated code, incomplete patterns, inconsistent naming
- `/verify`: run all tests, check types, confirm nothing is broken
- `/spec`: given a feature description, write a full spec before touching code
- `/review`: fresh-context code review of the last set of changes

### 9.4 The Cost Optimization Rule
Do not optimize for token cost at the start of a project. Optimize for output quality. Use the best model (Opus) for all agentic and architectural work.

Use `/effort` to calibrate per task:
- `/effort low` → batch renames, formatting, mechanical edits
- `/effort medium` → default everyday coding
- `/effort high` → complex bugs, architecture, multi-file refactors
- `ultrathink` keyword → per-turn override to high effort without changing session default

When the product is proven and in maintenance mode: then optimize cost.

---

## 10. THE PERMISSIONS LAW

### 10.1 Decide Trust Upfront, Not Under Pressure
At the start of every project, decide and document what Claude can and cannot do without asking.

**Claude can do without asking:**
- Create new files in /src
- Edit existing files in /src
- Run typecheck, lint, tests, dev server
- Install packages with bun
- Read any file in the repo

**Claude must always ask before:**
- Deleting any file
- Modifying .env or any environment config
- Touching anything in a /deploy, /prod, or /scripts/deploy folder
- Changing package.json dependencies significantly
- Modifying git history

### 10.2 Never Skip Permissions Because You're In a Rush
Rushing is exactly when mistakes happen. The permission rules exist for tired, rushed, late-night sessions. Follow them especially then.

---

## 11. THE QUALITY LAW

### 11.1 Code Quality Is a Productivity Multiplier
Clean codebases produce more output per session. Messy codebases slow both you and the AI. Invest in quality continuously, not all at once at the end.

After every 5 PRs or major features: run a quality pass.

Prompt:
> "Review the last [X] changes. What is accumulating as technical debt? What naming is inconsistent? What should be refactored before we build more on top of it?"

### 11.2 AI-Generated Code Is Still Your Code
You are accountable for everything Claude writes. Review before merging. Understand before approving. If you don't understand what Claude built, ask it to explain before moving on.

### 11.3 Documentation Happens During, Not After
Claude is better than humans at writing its own PR descriptions and keeping documentation in sync with code. Use this.

After every significant feature:
> "Write a clear description of what was built, why, and how it works. Add this to the project README under [section]."

### 11.4 Use /diff Before Every Commit
Run `/diff` after Claude makes a series of edits. This opens an interactive diff viewer showing every change Claude made. Review before committing. It is far easier to catch a mistake at this point than three steps later.

---

## 12. THE MINDSET LAW

### 12.1 You Are a Builder, Not a Coder
The title is shifting. Coding is execution. Building is direction + execution. Focus your energy on the direction: what to build, why, for whom, with what tradeoffs.

### 12.2 Ideas Are the Only Currency
In a world where execution is increasingly automated, the quality and novelty of your ideas is the only true differentiator. Protect your thinking time. Invest in your taste. Build your judgment.

### 12.3 The Goal of All Tooling Is to Disappear
The best tool gets out of your way so your idea reaches the world as fast as possible. Every process in this document exists to serve that. If a rule is slowing you down without a clear payoff, question it and update this file.

### 12.4 Compound Your System
Every mistake that gets added as a rule makes the next session better. Every template you build saves future time. Every CLAUDE.md entry reduces friction. The system compounds. Invest in it consistently.

### 12.5 Outputs Are Disposable. Plans and Prompts Are Not.
Bad code can be rewritten. A bad plan generates a lot of bad code. A bad spec generates a lot of bad plans. Invest energy at the top of the chain — in the quality of your thinking — and the quality of everything downstream improves automatically.

---

## 13. LEARNED RULES
> This section grows over time. Every mistake Claude makes that you catch goes here as a rule.

*(Add rules below as you encounter them. Format: [Date] — [What went wrong] — [The rule.])*

---

**CODEBIBLE version:** 2.1
**Last updated:** March 31, 2026
**Maintained by:** KDOT / Ascnd

> "The question is never 'how do I get a better output from this prompt.' The question is 'how do I build a system where good output is the default.'" — Boris Cherny, adapted

> "Outputs are disposable. Plans and prompts compound. Debug at the source and it scales across every future task." — Claude Code Best Practices synthesis