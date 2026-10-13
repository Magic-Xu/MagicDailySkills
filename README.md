# MagicDailySkills

可独立安装的通用 Codex Skills，用于交付审查、会话目录清理、小红书研究与网站精修。

本仓库是以下四个 Skill 的唯一源码。安装使用符号链接指向源码目录，按需选择，不复制文件。

| 显示名 | 内部名称 |
| --- | --- |
| Daily · 产物边界检查 | `artifact-boundary-review` |
| Daily · 会话清理 | `codex-session-cleanup` |
| Daily · 小红书探索 | `xiaohongshu-explore` |
| Daily · 网站精修 | `website-refine` |

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

### `xiaohongshu-explore`

围绕实际问题搜索小红书，结合笔记正文、图片或视频中的关键信息，以及评论中的追问、更正和反面体验，整理有来源的结论。适用于旅居、消费、社群、办事经验、产品需求和内容选题探索。

优先复用用户指定的已登录浏览器，按当前可用工具完成阅读。区分个人经历、经营账号信息与已核实事实，核对时间、适用条件和独立来源；按用户目标交付比较、关键发现或下一步验证方案。探索默认只搜索和读取，发布、联系商家或预订需有相应授权。

### `website-refine`

对已有个人网站、产品官网和落地页进行视觉与交互精修。结合网站目标与审美偏好，选择相关优秀作品作为参考，把问题诊断、实际修改、浏览器检查与持续迭代连成完整流程。

覆盖排版、留白、视觉层级、色彩、动效、微交互、响应式和原创性，并按改动检查功能、可访问性与加载体验。交付可体验的预览、关键前后截图及验证范围；仅要求评审时保持只读。需要访问目标页面，实施时需要项目编辑与运行能力，视觉验收需要真实浏览器。

## 安装与更新

克隆仓库，将示例中的源路径替换为本机真实绝对路径：

```sh
git clone https://github.com/Magic-Xu/MagicDailySkills.git
mkdir -p ~/.agents/skills
ln -s /absolute/path/MagicDailySkills/artifact-boundary-review ~/.agents/skills/artifact-boundary-review
ln -s /absolute/path/MagicDailySkills/codex-session-cleanup ~/.agents/skills/codex-session-cleanup
ln -s /absolute/path/MagicDailySkills/xiaohongshu-explore ~/.agents/skills/xiaohongshu-explore
ln -s /absolute/path/MagicDailySkills/website-refine ~/.agents/skills/website-refine
```

只安装需要的 Skill。已有入口时先检查来源，同一个 Skill 在 `~/.agents/skills` 与 `~/.codex/skills` 中保留一个发现入口。新 Skill 未出现时，重启 Codex。

更新前检查工作区，干净时拉取主干，已链接的 Skill 随源码更新：

```sh
git -C /absolute/path/MagicDailySkills pull --ff-only
```

## 使用

交付前检查本次产物：

```text
$artifact-boundary-review 检查本次交付产物并修复明确的边界问题
```

只读盘点或执行清理：

```text
$codex-session-cleanup 仅盘点 2026-08-01 之前的本地 Codex 会话目录
$codex-session-cleanup 清理 2026-08-01 之前的本地 Codex 会话目录
```

需要其他目录时显式给出根目录。请求“清理”会执行已核验的安全项；“仅盘点”或“预览”保持只读。移动到回收站不会立即释放磁盘空间，不会删除 App 中的任务记录。

围绕当前问题探索小红书：

```text
$xiaohongshu-explore 用已登录的 Chrome 比较这几个地方是否适合住一个月，重点查普通工作日的生活体验、短租条件和反面反馈，给我有来源的比较及试住方案。
$xiaohongshu-explore 查找这类用户反复遇到的问题、已有解决办法和实际解决成本，区分已观察到的需求线索与待验证的产品假设。
```

探索需要当前可用的连接器、CLI 或浏览器；登录与账号由使用者自行配置。

精修已有网站：

```text
$website-refine 精修这个产品官网。保留现有品牌色，让产品展示更突出、排版更克制，并完成桌面、移动端与关键交互验收。
$website-refine 先评审这个个人网站，对照适合的优秀案例说明主要差距和建议，暂不修改。
```

## 维护

每个一级 Skill 目录以 `SKILL.md` 为入口，附属资料和脚本随目录维护。会话清理需要 macOS、Python 3.10 或更新版本，以及能读取实时任务状态的 Codex 桌面工具；缺少所需能力时保持只读，不猜测任务状态。

清理脚本变化时运行：

```sh
python3 -B -m unittest discover -s codex-session-cleanup/tests
```

## License

本仓库以 [MIT License](LICENSE) 开源。
