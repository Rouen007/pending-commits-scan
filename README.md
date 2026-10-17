# Pending Commits Scan

扫描用户主目录下的 Git 仓库，把未提交改动、未推送提交和无远端仓库的本地提交整理成一份带日期的 Markdown 记录。扫描过程不执行 git commit、push、reset 或清理；报告文件会写入本地磁盘。

## 适合什么场景

- 想回顾电脑上有哪些仓库有未提交工作。
- 想盘点分支上的本地提交，尤其是尚未配置 upstream 的分支。
- 想保存一个便于日后查阅的本地快照，而不是立即处理代码。

它是状态盘点工具，不负责判断改动是否安全或是否应该提交。

## 运行

仅需 Python 3 标准库，不需要 pip 安装第三方包：

~~~bash
python3 scripts/scan_pending_commits.py
~~~

默认扫描当前用户主目录，并把报告写到 Documents/待提交内容_YYYY-MM-DD.md。执行前可先设置单独的输出目录：

~~~bash
PENDING_SCAN_OUTPUT_DIR="$HOME/Documents/git-scan" python3 scripts/scan_pending_commits.py
~~~

同一天重复运行会写入同名报告并覆盖该文件；如果要保留多个快照，请在每次运行时指定不同的输出目录，或先自行备份已有报告。

## 扫描范围与排除项

默认扫描主目录下最多 4 层深的 Git 仓库。脚本按仓库真实路径去重，并跳过常见目录 Library、.Trash、node_modules、.Trash-1000 以及 ~/.cache。其他额外排除路径可通过环境变量设置：

~~~bash
PENDING_SCAN_MAX_DEPTH=6 PENDING_SCAN_EXCLUDE_PATHS="$HOME/Downloads:$HOME/private-work" PENDING_SCAN_OUTPUT_DIR="$HOME/Documents/git-scan" python3 scripts/scan_pending_commits.py
~~~

PENDING_SCAN_EXCLUDE_PATHS 使用当前系统的路径分隔符；macOS / Linux 通常是冒号。相对路径按主目录解析。增加扫描深度会增加扫描时间，建议把大型缓存或敏感目录加入排除列表。

## 报告内容

- 仓库路径和当前分支。
- git status --short 输出，包括暂存、未暂存和未跟踪文件名。
- 未暂存改动的 git diff --stat 摘要。
- 与 upstream 不同的提交；没有 upstream 时，记录不在任何 remote-tracking ref 或 tag 上的提交。
- 没有 remote 的仓库会记录本地提交数和最近一次提交。
- 干净仓库会集中列出，不为每个仓库生成长篇说明。

有 upstream 时以 upstream..HEAD 判断待推送提交。没有 upstream 但仓库有 remote 时，按不在远端跟踪引用或 tag 中的提交判断；完全没有 remote 的仓库只记录提交数和最近提交。无 upstream 分支上的普通本地提交不会自动被标记为待推送，因为脚本无法知道目标分支。

## 隐私与数据安全

报告可能包含本机目录路径、分支名、文件名、diff 统计和 commit subject。报告是明文本地 Markdown，默认位置通常在同步或备份目录中；分享或上传前先人工检查并脱敏。

脚本只读取 Git 状态、diff 统计和提交元数据，不读取完整 diff 内容，也不扫描文件内容中的 API Key / token。因此它不能替代凭据扫描或发布前安全审查。

## 文件结构

- **scripts/scan_pending_commits.py**：扫描与报告生成逻辑。
- [SKILL.md](SKILL.md)：供 agent 使用的行为说明。
- **README.md**：安装和运行手册。

## 许可证

当前仓库未附 LICENSE 文件。公开可见不等于授予复制、修改或再分发许可。
