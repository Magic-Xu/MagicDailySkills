# MagicDailySkills

一组可独立安装、持续维护的 Codex Skills，用于日常重复工作流。

本仓库是这些 Skills 的唯一事实来源。用户级安装使用符号链接指向仓库目录，更新时只需拉取本仓库，不复制 Skill 文件。

## Skills

### `artifact-boundary-review`

在最终交付前审查代码、文档、UI、测试、配置、提交和 PR 等持久化产物，避免把中间尝试、纠错过程或临时约束误写进最终结果。

主要行为：

- 以当前有效需求、目标读者和实际变更为审查基准。
- 区分表达最终状态、真实变化和必要过程的不同产物。
- 使用语义判断识别边界问题，不依赖关键词或历史错误清单。
- 在既有授权内最小修复本任务引入的明确问题；只读审查时仅报告建议。
- 不替代功能测试、构建、视觉检查、安全审查或领域验证。

### `codex-session-cleanup`

按截止日期盘点 projectless Codex 任务产生的本地目录，并把确认可清理的目录移入 macOS 回收站，重点保护仍被任务引用、正在运行或包含未保存 Git 工作的目录。

主要行为：

- 默认使用当前用户的 `Documents/Codex`，也可在请求中指定其他根目录。
- 使用任务最后更新时间，而不是目录名或文件修改时间判断新旧。
- 结合本机状态库与实时任务状态建立完整引用映射，避免受最近任务列表数量限制影响。
- 已归档且通过安全检查的目录可直接移入回收站，并生成可核对的 `manifest.json`。
- 未归档、孤儿目录或包含未保存 Git 工作的目录必须确认。
- 正在运行的任务、符号链接、Git worktree 和带 `.codex-keep` 的目录不会移动。
- “仅盘点”“预览”和 `dry run` 不执行任何写入。
- App 中的任务记录仍然保留；移入回收站的目录在清空回收站后才会永久删除并释放空间。

该 Skill 需要能列出、归档 Codex 任务并操作本地文件的 Codex 桌面环境。缺少所需任务工具时，它会停止，不会根据目录名猜测任务状态。

## 安装

克隆仓库：

```bash
git clone https://github.com/Magic-Xu/MagicDailySkills.git
```

把需要的 Skill 链接到 Codex 用户级发现目录。请将源路径替换为仓库在本机的真实绝对路径：

```bash
mkdir -p ~/.agents/skills
ln -s /absolute/path/MagicDailySkills/artifact-boundary-review ~/.agents/skills/artifact-boundary-review
ln -s /absolute/path/MagicDailySkills/codex-session-cleanup ~/.agents/skills/codex-session-cleanup
```

Codex 会跟随符号链接读取 Skill。若新 Skill 没有立即出现，重启 Codex。

更新仓库即可更新已链接的 Skill：

```bash
git -C /absolute/path/MagicDailySkills pull --ff-only
```

## 使用

交付前检查本次产物：

```text
$artifact-boundary-review 检查本次交付产物并修复明确的边界问题
```

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

首次使用或调整清理根目录后，建议先运行“仅盘点”。执行清理后可根据批次目录和 `manifest.json` 二次审查，再决定是否清空回收站。

## 目录结构

```text
MagicDailySkills/
├── README.md
├── artifact-boundary-review/
│   ├── SKILL.md
│   └── agents/
│       └── openai.yaml
└── codex-session-cleanup/
    ├── SKILL.md
    ├── agents/
    │   └── openai.yaml
    ├── scripts/
    │   ├── inventory.py
    │   └── move_to_trash.py
    └── tests/
        └── test_scripts.py
```

每个一级子目录都是一个独立 Skill，以其中的 `SKILL.md` 作为运行指令入口。

## License

本仓库以 [MIT License](LICENSE) 开源，可自由使用、复制、修改、发布和分发。
