# 示例

按技能浏览可运行示例、效果预览与案例说明。示例展示具体任务的实现和取舍；每个项目仍应根据自己的目标选择设计方向。

| 技能 | 示例 | 内容 |
| --- | --- | --- |
| [网站精修](../website-refine/SKILL.md) | [余量 · AI 订阅用量概念官网](website-refine/yuliang/) | 中文产品官网、桌面与移动端布局、交互演示和精修前后对比 |

[![余量官网预览](website-refine/yuliang/previews/desktop.png)](website-refine/yuliang/)

## 目录约定

```text
examples/
  README.md
  <skill-name>/
    <example-name>/
      README.md
      site/
      previews/
```

- 使用技能的内部名称分组，示例目录采用稳定的小写英文名称。
- 每例的 `README.md` 说明命题、对应技能、打开方式、可体验能力、限制及必要的验证方法。
- `site/` 是本例的可运行网页源码；其他类型的示例按自身用途组织源码。`previews/` 保存少量真实截图和需要的演示录屏。
- 依赖和检查脚本在示例内维护；生成的检查结果、依赖缓存和临时材料不进入版本库。
- 新增示例时更新本页目录和对应技能的示例入口。技能安装入口与执行说明继续保留在技能自身目录，浏览示例按需进行。

示例源码沿用仓库的 [MIT License](../LICENSE)。示例中的服务名称用于说明场景，不表示官方关联。
