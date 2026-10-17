# pending-commits-scan

只读扫描本地 Git 仓库的未提交改动与未推送提交，生成带日期的待提交记录。用户要求盘点待提交内容时使用；不催促、不执行 commit 或 push。

## 用途与使用方式

这是一个 Agent skill（Claude Code / Codex 通用格式），入口是 `SKILL.md`：
agent 按其中的 `description` 判断何时触发，按正文流程执行。脚本、参数和数据口径以 `SKILL.md` 为准。
人工使用时直接阅读 `SKILL.md`；带脚本的按其中给出的命令运行。

## 目录

- `SKILL.md`
- `scripts/`
