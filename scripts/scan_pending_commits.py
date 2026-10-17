#!/usr/bin/env python3
"""Scan git repos under the home directory and write a dated markdown report
for later review.

Recording tool only: it never suggests committing or pushing. It records
repository state for later review.
"""
"""
import os
import subprocess
import datetime
from pathlib import Path

HOME = Path.home()
EXCLUDE_DIRS = {"Library", ".Trash", "node_modules", ".Trash-1000"}


def configured_exclude_paths():
    """Return common defaults plus paths configured for this machine."""
    paths = {HOME / ".cache"}
    raw_paths = os.environ.get("PENDING_SCAN_EXCLUDE_PATHS", "")
    for raw in raw_paths.split(os.pathsep):
        raw = raw.strip()
        if not raw:
            continue
        path = Path(raw).expanduser()
        paths.add(path if path.is_absolute() else HOME / path)
    return paths


EXCLUDE_PATHS = configured_exclude_paths()
MAX_DEPTH = int(os.environ.get("PENDING_SCAN_MAX_DEPTH", "4"))


def find_git_repos(root: Path, max_depth: int = MAX_DEPTH):
    """Repos whose directory sits at most max_depth below root.

    The .git check runs before the depth cut-off. Results are keyed by realpath
    so a repo reachable through a symlinked or duplicate path is reported once,
    under its real location.
    """
    repos = {}
    root_depth = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root):
        p = Path(dirpath)
        depth = len(p.parts) - root_depth
        dirnames[:] = [d for d in dirnames
                       if d not in EXCLUDE_DIRS and p / d not in EXCLUDE_PATHS]
        if ".git" in dirnames or ".git" in filenames:  # .git file = worktree/submodule
            real = p.resolve()
            repos.setdefault(str(real), real)
            if ".git" in dirnames:
                dirnames.remove(".git")
        if depth >= max_depth:
            dirnames[:] = []
    return sorted(repos.values(), key=lambda x: str(x))


def run(cmd, cwd):
    # rstrip only: git status --short codes are meaningful in the leading
    # column (" M" unstaged vs "M " staged), so a leading strip() would
    # corrupt the first line's status code.
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result.stdout.rstrip("\n")


def scan_repo(repo: Path):
    status = run(["git", "status", "--short"], repo)
    branch = run(["git", "branch", "--show-current"], repo)
    diff_stat = run(["git", "diff", "--stat"], repo)

    upstream = run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], repo
    )
    ahead_log = ""
    ahead_stat = ""
    remotes = run(["git", "remote"], repo)
    has_head = bool(run(["git", "rev-parse", "--verify", "--quiet", "HEAD"], repo))
    # remote_state: "upstream" (normal), "no-upstream" (remote exists but this
    # branch tracks nothing), "local-only" (repo has no remote at all).
    remote_state = "upstream"
    local_commits = 0
    last_commit = ""
    if upstream and "fatal" not in upstream.lower():
        ahead_log = run(["git", "log", f"{upstream}..HEAD", "--oneline"], repo)
    elif has_head and remotes:
        remote_state = "no-upstream"
        # Commits on this branch that no remote-tracking ref or tag contains
        # (tags count as published, so detached checkouts of tagged releases
        # are not reported as local work).
        ahead_log = run(["git", "log", "HEAD", "--not", "--remotes", "--tags", "--oneline"], repo)
    elif has_head:
        remote_state = "local-only"
        local_commits = int(run(["git", "rev-list", "--count", "HEAD"], repo) or 0)
        last_commit = run(["git", "log", "-1", "--format=%cd %h %s", "--date=format:%Y-%m-%d %H:%M"], repo)
    if ahead_log:
        ahead_stat = run(["git", "show", "--stat", "HEAD"], repo)

    return {
        "path": repo,
        "branch": branch,
        "status": status,
        "diff_stat": diff_stat,
        "ahead_log": ahead_log,
        "ahead_stat": ahead_stat,
        "remote_state": remote_state,
        "local_commits": local_commits,
        "last_commit": last_commit,
        "has_changes": bool(status) or bool(ahead_log),
    }


def build_report(results):
    changed = [r for r in results if r["has_changes"]]
    clean = [r for r in results if not r["has_changes"]]
    today = datetime.date.today().isoformat()

    lines = [
        f"# 本地待提交内容记录（{today}）",
        "",
        f"扫描范围：`~` 下 {MAX_DEPTH} 层内所有 git 仓库。共发现 {len(changed)} 个仓库有未提交/未推送内容。",
        "",
        "---",
        "",
    ]

    for i, r in enumerate(changed, 1):
        name = r["path"].name
        rel = str(r["path"]).replace(str(HOME), "~")
        lines.append(f"## {i}. {name}")
        lines.append("")
        lines.append(f"路径：`{rel}`　分支：`{r['branch']}`")
        lines.append("")
        if r["status"]:
            lines.append("**未暂存/未跟踪改动：**")
            lines.append("```")
            lines.append(r["status"])
            lines.append("```")
            if r["diff_stat"]:
                lines.append("")
                lines.append("**diff 摘要：**")
                lines.append("```")
                lines.append(r["diff_stat"])
                lines.append("```")
            lines.append("")
        if r["remote_state"] == "local-only":
            lines.append(f"**无远端仓库：**本地共 {r['local_commits']} 个提交，最近一次 {r['last_commit']}。")
            lines.append("")
        if r["ahead_log"]:
            lines.append("**待推送提交：**" if r["remote_state"] == "upstream"
                         else "**当前分支未设上游，以下提交不在任何远端：**")
            lines.append("```")
            lines.append(r["ahead_log"])
            lines.append("```")
            if r["ahead_stat"]:
                lines.append("")
                lines.append("```")
                lines.append(r["ahead_stat"])
                lines.append("```")
            lines.append("")
        lines.append("---")
        lines.append("")

    local_only = [r for r in clean if r["remote_state"] == "local-only"]
    if local_only:
        lines.append("## 无远端的本地仓库（工作区干净）")
        lines.append("")
        lines.append("这些仓库没有配置任何远端，提交只存在本机；这里只记录数量，不代表需要推送。")
        lines.append("")
        lines.append("| 仓库 | 路径 | 本地提交数 | 最近一次提交 |")
        lines.append("|---|---|---|---|")
        for r in local_only:
            rel = str(r["path"]).replace(str(HOME), "~")
            lines.append(f"| `{r['path'].name}` | `{rel}` | {r['local_commits']} | {r['last_commit']} |")
        lines.append("")
        clean = [r for r in clean if r["remote_state"] != "local-only"]

    lines.append("## 未发现改动的仓库")
    lines.append("")
    if clean:
        names = "、".join(f"`{r['path'].name}`" for r in clean)
        lines.append(f"{names} 均无未提交内容（working tree clean）。")
    else:
        lines.append("（无）")

    return "\n".join(lines) + "\n"


def main():
    repos = find_git_repos(HOME)
    results = [scan_repo(r) for r in repos]
    report = build_report(results)

    today = datetime.date.today().isoformat()
    out_dir = Path(os.environ.get("PENDING_SCAN_OUTPUT_DIR", str(HOME / "Documents"))).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"待提交内容_{today}.md"
    out_path.write_text(report, encoding="utf-8")
    print(str(out_path))


if __name__ == "__main__":
    main()
