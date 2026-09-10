#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
const [channel, sourceArg, outputArg, ...options] = process.argv.slice(2);
if (!['juejin', 'wechat'].includes(channel) || !sourceArg || !outputArg ||
    (options.length && (options.length !== 2 || options[0] !== '--project' || !options[1]))) {
  throw Error('用法：prepare_channel_sync.mjs juejin|wechat 渠道稿.md 导出稿.html [--project 网站项目目录]');
}
const project = options.length ? path.resolve(options[1]) : null;
const source = path.resolve(sourceArg), output = path.resolve(outputArg);
const md = await fs.readFile(source, 'utf8');
const heading = md.match(/^# (.+)\r?\n/);
if (!heading) throw Error('渠道稿首行必须是已审查的文章标题。');
const require = createRequire(project ? path.join(project, 'package.json') : source);
const {createMarkdownProcessor} = await import(pathToFileURL(require.resolve('@astrojs/markdown-remark')).href);
const processor = await createMarkdownProcessor({syntaxHighlight:false});
let html = (await processor.render(md.slice(heading[0].length))).code;
// The Wechatsync WeChat adapter strips external anchors. Keep their destinations in readable text.
if (channel === 'wechat') {
  const {parseFragment} = require('parse5');
  const external = new Set();
  const text = [];
  function visit(node) {
    if (['script', 'style', 'template'].includes(node.tagName)) return;
    if (node.nodeName === '#text') text.push(node.value);
    if (node.tagName === 'a') {
      const href = node.attrs.find(attr => attr.name === 'href')?.value;
      if (/^(?:https?:)?\/\//i.test(href || '')) {
        const host = new URL(href, 'https://example.invalid').hostname;
        if (host !== 'weixin.qq.com' && !host.endsWith('.weixin.qq.com')) external.add(href);
      }
    }
    for (const child of node.childNodes || []) visit(child);
  }
  visit(parseFragment(html));
  const visible = text.join('');
  const missing = [...external].filter(url => !visible.includes(url));
  if (missing.length) throw Error('公众号导出含仅保存在超链接中的外部地址；请在正文或文末保留完整可复制网址：' + missing.join(', '));
}
const escape = s => s.replaceAll('&','&amp;').replaceAll('"','&quot;').replaceAll('<','&lt;').replaceAll('>','&gt;');
let count = 0;
const styles = [];
html = html.replace(/<div align="center">\s*(<img\b[^>]+>)\s*<\/div>/gi, (block, img) => {
  const width = Number(img.match(/\bwidth="(\d+)"/)?.[1]);
  const src = img.match(/\bsrc="([^"]+)"/)?.[1];
  if (!(width > 0) || !src || /^(?:https?:|data:|file:)/i.test(src)) throw Error('必须使用有明确尺寸的本地已审查图片。');
  const imagePath = path.resolve(path.dirname(source), src);
  count++;
  img = img.replace(/\bsrc="[^"]+"/, 'src="' + escape(imagePath) + '"');
  styles.push(`[data-sync-image="${count}"] img{width:${width}px;max-width:100%;height:auto;display:block;margin:24px auto;}`);
  return `<div align="center" data-sync-image="${count}">${img}</div>`;
});
if (count !== (html.match(/<img\b/gi) || []).length) throw Error('有图片未生成可验证的导出块。');
for (const match of html.matchAll(/<img\b[^>]+src="([^"]+)"/gi)) await fs.access(match[1].replaceAll('&amp;', '&'));
const css = channel === 'wechat' ? `<style>${styles.join('\n')}</style>` : '';
await fs.mkdir(path.dirname(output), {recursive:true});
await fs.writeFile(output, `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>${escape(heading[1])}</title></head><body>${css}${html}</body></html>`, {mode:0o600});
console.log(JSON.stringify({channel,output,images:count}));
