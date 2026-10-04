# MagicDailySkills

一组可独立安装、持续维护的 Codex Skills，用于日常重复工作流。

本仓库是这些 Skills 的唯一事实来源。用户级安装使用符号链接指向仓库目录，更新时只需拉取本仓库，不复制 Skill 文件。

## 显示名与内部名称

日常 Skill 的显示名统一使用 `Daily · 用途`，便于与开发类的 `Magic` 名称区分。内部名称、目录、`$skill-name` 调用方式和符号链接保持稳定。

| 显示名 | 内部名称 |
| --- | --- |
| Daily · 个人创作 | `magic-creation` |
| Daily · 表达风格 | `magic-tone` |
| Daily · 内容格式 | `magic-content-format` |
| Daily · 产物边界检查 | `artifact-boundary-review` |
| Daily · 会话清理 | `codex-session-cleanup` |
| Daily · 小红书探索 | `xiaohongshu-explore` |

LifeOS 在自己的仓库维护，显示为 `Daily · LifeOS`，内部名称仍为 `lifeos`。第三方插件与开发类 Skill 不使用本仓库的命名约定。

## Skills

### `xiaohongshu-explore`

围绕实际问题搜索小红书，结合笔记正文、图片或视频中的关键信息，以及评论中的追问、更正和反面体验，整理有来源的结论。适用于旅居、消费、社群、办事经验、产品需求和内容选题探索。

优先复用用户指定的已登录浏览器，按当前可用工具完成阅读。区分个人经历、经营账号信息与已核实事实，核对时间、适用条件和独立来源；按用户目标交付比较、关键发现或下一步验证方案。探索默认只搜索和读取，发布、联系商家或预订需有相应授权。

### `artifact-boundary-review`

在最终交付前审查代码、文档、UI、测试、配置、提交和 PR 等持久化产物，避免把中间尝试、纠错过程或临时约束误写进最终结果。

主要行为：

- 以当前有效需求、目标读者和实际变更为审查基准。
- 区分表达最终状态、真实变化和必要过程的不同产物。
- 使用语义判断识别边界问题，不依赖关键词或历史错误清单。
- 在既有授权内最小修复本任务引入的明确问题；只读审查时仅报告建议。
- 不替代功能测试、构建、视觉检查、安全审查或领域验证。

### `codex-session-cleanup`

按截止日期清理 Codex 会话工作目录与可视化产物：已核验的安全项直接移入回收站，只列需要用户决定的内容；用户包含 worktree 时，可修剪已验证的失效登记。

主要行为：

- 默认检查当前用户的 `Documents/Codex` 与 Codex 可视化目录；用户可限定根目录和范围。
- 使用任务最后更新时间，而不是目录名或文件修改时间判断新旧。
- 结合本机状态库与实时任务状态建立完整引用映射，避免受最近任务列表数量限制影响。
- 已归档、通过安全检查且确认为无保留价值的目录直接移入回收站；执行结果简报数量，精确路径保存在 `manifest.json`。
- 未归档、孤儿目录、未保存 Git 工作及仍需判断价值的成果按用途聚合，只对这些项目请求确认。
- 正在运行的任务、符号链接、Git worktree 和带 `.codex-keep` 的目录不会移动。
- “仅盘点”“预览”和 `dry run` 不执行任何写入。
- App 中的任务记录仍然保留；移入回收站的目录在清空回收站后才会永久删除并释放空间。

该 Skill 需要能列出、归档 Codex 任务并操作本地文件的 Codex 桌面环境。缺少所需任务工具时，它会停止，不会根据目录名猜测任务状态。

### `magic-content-format`

按 Magic 的内容格式要求组织方案、行程、文档、报告、文章和较长答复：先放读者最需要的信息，控制密度，让段落、列表、表格和图示各有用途。精简时保留执行条件，更新时同步受影响的图文，并按交付载体检查实际呈现。

支持按任务自动匹配，也可用 `$magic-content-format` 显式调用；个人文风由 `magic-tone` 负责，产物边界由 `artifact-boundary-review` 检查。

### `magic-tone`

以 Magic 的个人表达起草、改写和校准文章：从真实经历和具体事实出发，表达有依据的个人判断，尊重读者的时间。以已发表文章为参照，按不同主题选择结构与节奏；只沉淀稳定的表达偏好。

### `magic-creation`

统一创作文章、随笔与真实到访足迹，按用户指定的类型写入飞书「个人创作」对应草稿分类；母稿和面向用户的操作说明均以飞书为入口。本机 `MagicPersonalIP/Blog/` 只保存素材、渠道稿、预览、缓存及发布记录，不纳入 Git。

创作、改稿和保存草稿不自动公开。网站与文章渠道按明确指令同步；随笔发布到 X 须本人明确要求，目标账号由本人提供。公众号继续由本人在后台审查发布。内容组织按需使用 `magic-content-format`，个人语气按需使用 `magic-tone`。

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
ln -s /absolute/path/MagicDailySkills/magic-tone ~/.agents/skills/magic-tone
ln -s /absolute/path/MagicDailySkills/magic-content-format ~/.agents/skills/magic-content-format
ln -s /absolute/path/MagicDailySkills/magic-creation ~/.agents/skills/magic-creation
ln -s /absolute/path/MagicDailySkills/xiaohongshu-explore ~/.agents/skills/xiaohongshu-explore
```

已有的 `~/.codex/skills` 安装也可用符号链接指向本仓库；同一个 Skill 保留一个发现入口即可。

Codex 会跟随符号链接读取 Skill。若新 Skill 没有立即出现，重启 Codex。

更新仓库即可更新已链接的 Skill：

```bash
git -C /absolute/path/MagicDailySkills pull --ff-only
```

## 使用

整理信息顺序、密度和图文分工：

```text
$magic-content-format 精简这份文档，先放当前要执行的安排，删掉图表与正文的重复说明，并检查实际呈现。
```

围绕当前问题探索小红书：

```text
$xiaohongshu-explore 用已登录的 Chrome 比较这几个地方是否适合住一个月，重点查普通工作日的生活体验、短租条件和反面反馈，给我有来源的比较及试住方案。
```

也可以探索目标用户的问题：

```text
$xiaohongshu-explore 查找这类用户反复遇到的问题、已有解决办法和实际解决成本，区分已观察到的需求线索与待验证的产品假设。
```

创作文章、随笔或足迹并保存草稿：

```text
$magic-creation 帮我把这段感悟写成随笔，保存到飞书「随笔／草稿」，先不发布。
```

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

请求“清理”时会直接执行已核验的安全项；只有明确要求“仅盘点”或“先给我检查”才停在预览。执行后可根据批次目录和 `manifest.json` 二次审查，再决定是否清空回收站。

## 目录结构

```text
MagicDailySkills/
├── README.md
├── xiaohongshu-explore/
│   ├── SKILL.md
│   └── agents/openai.yaml
├── artifact-boundary-review/
│   ├── SKILL.md
│   ├── references/
│   │   └── detailed-review.md
│   └── agents/
│       └── openai.yaml
├── magic-content-format/
│   ├── SKILL.md
│   └── agents/openai.yaml
├── magic-tone/
│   ├── SKILL.md
│   ├── references/voice-examples.md
│   └── agents/openai.yaml
├── magic-creation/
│   ├── SKILL.md
│   ├── references/channel-editions.md
│   ├── scripts/
│   │   ├── prepare_channel_sync.mjs
│   │   ├── check_channel_images.py
│   │   ├── test_prepare_channel_sync.py
│   │   └── test_check_channel_images.py
│   └── agents/openai.yaml
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
