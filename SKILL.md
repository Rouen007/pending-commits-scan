---
name: pending-commits-scan
description: 只读扫描本地 Git 仓库的未提交改动与未推送提交，生成带日期的待提交记录。用户要求盘点待提交内容时使用；不催促、不执行 commit 或 push。
---

# Pending Commits Scan

Records a snapshot of every git repo under `~` that currently has local-only
work: uncommitted changes, untracked files, or commits that haven't been
pushed to the upstream remote. The output is a dated markdown file, nothing
more — it's a log entry, not a to-do reminder.

## Why this exists

This skill tracks local-only changes across git repos between commits. It
leaves a dated record of pending work without prompting anyone to commit
sooner.

## How to run it

Run the bundled script, which does the full scan and writes the file:

```bash
python3 scripts/scan_pending_commits.py
```

It prints the path of the file it wrote (e.g.
`$HOME/Documents/待提交内容_YYYY-MM-DD.md`). The script:

1. Walks the home directory for `.git` repositories up to 4 levels deep by
   default. Repos are de-duplicated by realpath (a repo reachable through a
   symlinked path is reported once, under its real location). It skips common
   system/cache directories and any extra paths in `PENDING_SCAN_EXCLUDE_PATHS`.
   Set `PENDING_SCAN_MAX_DEPTH` to change the search depth.
2. For each repo, collects `git status --short`, `git diff --stat`, and
   commits not yet on a remote:
   - branch has an upstream → `git log <upstream>..HEAD`;
   - remote exists but the branch tracks nothing → `git log HEAD --not
     --remotes --tags` (commits on no remote-tracking ref or tag, so a
     detached checkout of a release tag is not reported);
   - repo has no remote at all → total local commit count and the latest
     commit. Clean local-only repos go in their own table instead of the
     changed list, since there is nothing to push to.
3. Writes a single markdown report to `PENDING_SCAN_OUTPUT_DIR`, defaulting to
   `~/Documents`, using **today's actual date** — never hardcode a date.
4. Repos with no pending changes are listed together in a short closing
   section instead of getting their own write-up.

After running it, briefly summarize in chat which repos had pending content
(repo name + one-line gist of what changed) and point to the generated file.
Do not suggest committing, pushing, or cleaning anything up — that's outside
this skill's scope unless the user asks separately.

## Notes

- If a repo's diff touches something that looks like a live credential (API
  key, token, password) changing value, flag that specifically in your chat
  summary so the user can double check before it ever gets committed — but
  still don't tell them to commit or not commit, just surface the fact.
- If no repos have pending changes, the script still writes a file; say so
  plainly rather than treating it as an error.
