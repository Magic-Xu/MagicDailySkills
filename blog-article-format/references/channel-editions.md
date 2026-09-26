# 渠道适配

按目标渠道读取相关部分。作者约定决定需要保留的表达与信息，平台能力和同步工具决定实现边界；排版根据本篇内容判断。

## 公众号阅读与排版

公众号以手机阅读为主要场景。开头与措辞遵循 [MagicTone](../../magic-tone/SKILL.md) 及本篇已审定的结构；渠道适配保留背景、导读和正文各自的作用，不移动或删减内容来迁就渲染模板。阅读时间按渠道需要提供，结合篇幅估算，不作为显示导读样式的前提。

### 排版判断

从文章的信息关系决定呈现：主要论点应容易找到，解释和证据靠近所支持的内容，补充信息与主线有适当区分。字号、字重、颜色、边线和留白共同服务于这些关系，同类内容在一篇文章中保持一致。

连续说明适合连贯的段落；需要依次完成的动作适合步骤；比较多个对象时考虑表格或图；理解依赖界面时，把截图放在对应操作旁边。长内容是否分节、配图或移到附录，取决于读者是否需要连续阅读或随时查阅。手机上的宽表、长代码与大图应分别检查，不能只按字数拆段或统一缩小。

强调要有轻重。先用位置、字重和间距建立主次，只有需要读者特别留意的信息才加强处理。配色应保证对比度、用途清楚且彼此协调；不为凑颜色或模块增加内容。图注紧邻图片，说明理解所需的信息；引用注明来源，示意图与实拍、截图区分。

### 排版实现

[wechat-layout.mjs](../scripts/wechat-layout.mjs) 提供一种可调整的基础实现，将正文样式写在元素上，以适应平台可能移除样式表的行为。内置颜色、字号与容器外观可按本篇设计调整；预览与导出共用调整后的正文样式。

按内容语义选择 HTML：`blockquote` 表示引用，作者自己的说明使用段落或普通容器。随附脚本支持以下可选标记，标记描述用途，不要求文章具备这些内容：

| 标记 | 用途 |
| --- | --- |
| `section data-wechat-kind="warning"` | 需要突出显示的条件或注意事项 |
| `section data-wechat-kind="prompt"` | 本文确实需要提供的提示词 |
| `p data-wechat-caption="true"` | 图注；也兼容紧随图片的独立斜体段落 |

容器标签内外留空行，内部可继续写 Markdown。普通正文中的斜体保持强调语义。

实际编辑器对引用组件存在长度限制；随附脚本按已观察的限制，将真实引用块的可见文本预检上限设为 300 个字符，准确边界以后台为准。长引用保留必要摘句，作者的长说明使用普通容器，不套用整篇字数限制。代码块标注语言；树形目录使用 `text` 围栏，导出按行保留缩进，验收时核对可复制性与层级。

### 排版验收

从同步 HTML 使用 [render_wechat_preview.mjs](../scripts/render_wechat_preview.mjs) 生成预览，在桌面和约 320–390px 手机宽度阅读。检查读者能否辨认主次、顺畅理解图文关系，以及本篇采用的内容形式是否可读，据实际效果调整设计。

同时核对所选内容块的样式已进入同步正文，图片比例正确、来源可访问或复制，页面无横向溢出。纯排版修改应保持已审定的文字与素材；设计调整后重新导出，使用验收过的同一文件同步。文字完整、图片加载或 CLI 成功不能代替视觉审查。

审查记录注明稿件版本和范围。用户对本地呈现的确认只记为本地确认，平台保存稿与发布状态按实际证据记录。

### 封面与摘要

随渠道预览稿一起准备，交付目录见主文件。使用 `wechat-cover.png` 与 `wechat-summary.txt`，最终交付给出直接链接。

- 封面按当前渠道尺寸制作，公众号横版可从约 2.35:1 起设计，核对裁切与缩略图可读性。素材根据文章内容选择；需要生成或改图时使用 [imagegen](/Users/magic/.codex/skills/.system/imagegen/SKILL.md)。封面作为独立发布素材交付。
- 摘要用一至两句说明主题与阅读价值，按当时后台限制校验。文本文件只保留可粘贴的摘要。
- 本机同步助手可能不填写封面和摘要；根据实际结果，把素材与仍需填写的字段一起交付。

## 公开范围与渠道脱敏

正文及所有素材使用同一公开范围。读取私人材料不等于获准公开；检查可识别信息、链接目标以及图片实际包含的内容。

作者应用实践的现行约定：个人官网可以保留具体应用身份；公众号及其他外部分发渠道默认隐藏应用身份及可推断用途的细节。Magic 明确要求在指定渠道宣传时，按该次授权保留。此约定仅用于相关应用实践。

- 在需要脱敏的渠道统一处理正文、代码、图注、替代文本、文件名、链接及图片中的标识和用途线索。采用自然泛称或明确的示例值，保留文章所依据的事实与通用方法。
- 图片使用真正处理过的副本；网页遮罩、缩小显示或修改替代文本不能代替处理图片本身。渠道目录保存副本，母稿按自身用途引用素材。
- 检查导出与实际保存稿，避免混用原图或通过链接暴露被隐藏的信息。

## 个人网站、掘金及其他渠道

网站按其内容模型和页面模板呈现，保留长期查阅所需的来源与背景。首次发布后维护稳定链接，更新信息按项目约定显示。

技术社区稿保留理解或复现所需的前提与细节；其他渠道按读者调整背景和解释深度。渠道偏好作为编辑判断，功能和限制以当前实际能力为准。支持超链接的渠道优先以资料名称承载链接，避免重复长网址。

## CLI 导出与同步

以下是当前本机的分发机制。使用前读取 [Wechatsync 接入说明](/Users/magic/.local/share/wechatsync/README.md)，核对已安装版本、参数及已知限制。**正文同步使用 CLI**，入口为 `/Users/magic/.local/bin/wechatsync`；不操作扩展弹窗，不用 MCP 替代，也不把正文粘贴或逐张上传交回给 Magic。

每个平台使用各自已审查的稿件，显式指定目标；公众号 ID 为 `weixin`，掘金为 `juejin`。CLI 按需连接已安装扩展。

导出脚本从 `--project` 指定的项目读取 Astro 渲染依赖；渠道稿可位于项目之外，图片路径相对于渠道稿解析。替换示例中的文章标识，并使用本次实际项目路径：

```sh
article_dir='/Users/magic/Documents/MagicArticle/<article-slug>'
website_dir='/Users/magic/MagicDevProject/MagicPersonalIP/magic-site'

node /Users/magic/.codex/skills/blog-article-format/scripts/prepare_channel_sync.mjs \
  juejin "$article_dir/juejin.md" "$article_dir/juejin-sync.html" --project "$website_dir"

node /Users/magic/.codex/skills/blog-article-format/scripts/prepare_channel_sync.mjs \
  wechat "$article_dir/wechat.md" "$article_dir/wechat-sync.html" --project "$website_dir" --require-intro

node /Users/magic/.codex/skills/blog-article-format/scripts/render_wechat_preview.mjs \
  "$article_dir/wechat-sync.html"
```

源稿首行为 `# 文章标题`。上例适用于采用三项导读的稿件，`--require-intro` 检查已选导读完整且非空；支持前置背景与可选的阅读时间，保持原顺序。按已审定结构不含导读的稿件省略该参数，旧调用的 `--allow-no-intro` 仍兼容。检查与选定结构不符时修复源稿或识别逻辑，保留作者要求的信息与其呈现作用。脚本同时检查引用长度、图片尺寸和外部地址。

预览脚本生成同目录下的 `wechat-review.html` 与 `wechat-mobile.html`，正文和内联样式与同步稿一致，只增加外层审查界面并转换本地图片路径。改稿后重新导出、生成预览，按上文排版验收后同步。

当前接入说明使用 150000ms 连接等待，覆盖扩展自动重连间隔。掘金含正文图片的 HTML 使用 `--keep-image-layout`；纯文字稿去掉该参数，否则当前兼容层会因没有图片而拒绝建稿。封面不计入正文图片。

```sh
/Users/magic/.local/bin/wechatsync --timeout 150000 sync \
  "$article_dir/juejin-sync.html" -p juejin --keep-image-layout \
  --result-json /private/tmp/juejin-sync-result.json

/Users/magic/.local/bin/wechatsync --timeout 150000 sync \
  "$article_dir/wechat-sync.html" -p weixin \
  --result-json /private/tmp/wechat-sync-result.json
```

结果文件使用本次任务的临时路径，发布记录保存真实草稿链接与状态。原版公众号适配器每次新建草稿，重复同步前核对已有结果，合并相关修复后再同步。连接、上传、转换或平台校验失败时先定位对应环节；遇到无法解决的登录、权限或服务阻碍，保留成果并说明缺口。工具切换与重试遵守当前权限边界。

### 图片尺寸与转换

同步稿须保留已审查的显示尺寸，窄屏允许缩到正文栏宽度。随附脚本接受本地图片的显式 HTML，按以下结构传入 `width` 与内联样式；示例尺寸仅演示语法：

```html
<div align="center">
<img src="assets/illustration.png" alt="图片所说明的内容" width="480" style="width:480px;max-width:100%;height:auto;display:block;margin:24px auto;" />
</div>
```

扩展上传、HTML 转 Markdown 或网页提取可能重建标签并丢失样式。本机掘金兼容路径用 `--keep-image-layout` 保留图片 HTML，该参数仅用于单独同步掘金。公众号由 CLI 上传本地图片并替换地址，导出稿保留内联尺寸。工具升级后重新验证转换结果，再核验平台稿；不修改原版扩展。

### 超链接与参考资料

原版公众号适配器会移除非微信域名的链接标签，仅留下文字。使用这条路径时保留资料名称与完整可复制网址，可按阅读需要在文末集中列出并在正文编号；长网址允许换行，地址不能只藏在 `href` 中。导出会拒绝缺少可见地址的外部链接。

区分账号外链能力与同步工具行为，工具移除链接不代表所有账号都不支持外链。若使用“阅读原文”承接完整资料，须落实已获用户接受的阅读路径与有效原文入口。验收时核对链接目标或可复制地址；普通文字网址需让读者知道应复制到浏览器打开。

## 平台验收与交付

### 非微信平台

CLI 成功后在 Chrome 打开本次返回的草稿，补齐当前平台需要的分类、标签、摘要、封面等字段。保存后重新打开，核对全文以及实际存在的图片、代码、表格和链接。错误修到源稿或转换环节，再同步复验。

掘金的封面比例、独立窗口恢复、原生文件选择器和图片测量替代路径见 [掘金发布与窗口恢复](juejin-publishing.md)。浏览器连接失败与 CLI 同步失败分别处理，不能因为页面操作失败重复建稿。

已有发布授权且验收通过后继续发布，不重复询问同一动作；核对结果页，分别记录发布成功、审核中或公开可见。发布后立即回填该渠道的链接、验收及剩余事项，再处理其他渠道，避免下一渠道中断后仍留下旧的“草稿／阻塞”记录。

### 微信公众号

当前约定由 Magic 在微信后台审查并发布，代理不使用 Chrome 检查或操作微信后台。代理负责本地检查、CLI 结果核对，交付本次草稿链接、封面、摘要与仍需手动填写的字段。

收到实际验收前记录“待用户审查”。根据反馈修复本地稿及相关导出逻辑，再按需同步；本地预览或其他平台的验收不能代替微信验收。

### 有图稿件的测量

非微信平台保存并重新打开草稿后，读取正文图片的实际尺寸与加载状态。基准来自已审查源稿，测量来自平台 DOM，不包括封面、头像和工具栏图片。

临时 JSON 包含 `savedAndReloaded`、正文宽度 `contentWidth`，以及按顺序排列的 `images`，每项含 `width`、`height`、`naturalWidth`、`naturalHeight`、`complete`。不记录凭据或带签名的图片地址。

```sh
python3 /Users/magic/.codex/skills/blog-article-format/scripts/check_channel_images.py \
  --source /已审查的渠道稿.md --measurements /临时目录/平台图片测量.json
```

脚本检查缺图、加载失败、尺寸丢失与比例失真；通过后仍查看实际排版。纯文字稿跳过图片测量；无法取得实际证据的检查保持未完成状态。

导出或验收代码变动时运行相关回归检查，使用已有依赖、不连接平台：

```sh
ARTICLE_RENDER_PROJECT=/Users/magic/MagicDevProject/MagicPersonalIP/magic-site python3 -B -m unittest discover \
  -s /Users/magic/.codex/skills/blog-article-format/scripts -p 'test_*.py'
```
