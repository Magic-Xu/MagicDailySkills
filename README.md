# MagicDailySkills

一组可独立安装、持续维护的 Codex Skills，用于日常重复工作流。

本仓库是这些 Skills 的唯一事实来源。用户级安装使用符号链接指向仓库目录，更新时只需拉取本仓库，不复制 Skill 文件。

## Skills

### `codex-session-cleanup`

按截止日期盘点并清理项目less Codex 任务产生的本地目录，重点防止误删仍被任务引用、正在运行或包含未保存 Git 工作的目录。

主要行为：

- 默认使用当前用户的 `Documents/Codex`，也可在请求中指定其他根目录。
- 使用任务最后更新时间，而不是目录名或文件修改时间判断新旧。
- 已归档且通过安全检查的目录可直接清理。
- 未归档、孤儿目录或包含未保存 Git 工作的目录必须确认。
- 正在运行的任务、符号链接、Git worktree 和带 `.codex-keep` 的目录不会删除。
- 支持“仅盘点”“预览”和 `dry run`，不执行任何写入。
- 只删除本地工作目录，不永久删除 Codex App 中的任务记录。

该 Skill 需要能列出、归档 Codex 任务并操作本地文件的 Codex 桌面环境。缺少所需任务工具时，它会停止，不会根据目录名猜测任务状态。

## 安装

克隆仓库：

```bash
git clone https://github.com/Magic-Xu/MagicDailySkills.git
```

把需要的 Skill 链接到 Codex 用户级发现目录。请将源路径替换为仓库在本机的真实绝对路径：

```bash
mkdir -p ~/.agents/skills
ln -s /absolute/path/MagicDailySkills/codex-session-cleanup ~/.agents/skills/codex-session-cleanup
```

Codex 会跟随符号链接读取 Skill。若新 Skill 没有立即出现，重启 Codex。

更新仓库即可更新已链接的 Skill：

```bash
git -C /absolute/path/MagicDailySkills pull --ff-only
```

## 使用

先只读盘点：

```text
$codex-session-cleanup 仅盘点 2026-08-01 之前的本地 Codex 会话目录
```

执行清理：

```text
$codex-session-cleanup 清理 2026-08-01 之前的本地 Codex 会话目录
```

指定其他根目录：

```text
$codex-session-cleanup 仅盘点 2026-08-01 之前的会话目录，根目录是 /absolute/path/to/Codex
```

删除是永久操作。首次使用或调整清理根目录后，建议先运行“仅盘点”。

## 目录结构

```text
MagicDailySkills/
├── README.md
└── codex-session-cleanup/
    ├── SKILL.md
    └── agents/
        └── openai.yaml
```

每个一级子目录都是一个独立 Skill，以其中的 `SKILL.md` 作为运行指令入口。

## License

本仓库以 [MIT License](LICENSE) 开源，可自由使用、复制、修改、发布和分发。
