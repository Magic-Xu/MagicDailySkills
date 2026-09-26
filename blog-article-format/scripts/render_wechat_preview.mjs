#!/usr/bin/env node
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';

const [inputArg,...options]=process.argv.slice(2);
if(!inputArg || (options.length && (options.length!==2 || options[0]!=='--output-dir' || !options[1]))) {
  throw Error('用法：render_wechat_preview.mjs wechat-sync.html [--output-dir 预览目录]');
}
const input=path.resolve(inputArg);
const dir=options.length ? path.resolve(options[1]) : path.dirname(input);
const sync=await fs.readFile(input,'utf8');
const bodyMatch=sync.match(/<body>([\s\S]*)<\/body>/i);
const title=sync.match(/<title>([\s\S]*?)<\/title>/i)?.[1];
if(!bodyMatch || !title || !bodyMatch[1].includes('data-wechat-layout=')) {
  throw Error('预览输入必须是 prepare_channel_sync.mjs 生成的公众号同步 HTML。');
}
// The exporter owns the HTML format. Only local image addresses change; content
// styles remain exactly those sent to the sync CLI, independent of the frame.
const body=bodyMatch[1].replace(/<img\b[^>]*>/gi,img=>img.replace(/\bsrc="([^"]*)"/i,(match,encoded)=>{
  const src=encoded.replaceAll('&amp;','&').replaceAll('&quot;','"').replaceAll('&lt;','<').replaceAll('&gt;','>');
  if(!path.isAbsolute(src)) return match;
  const relative=path.relative(dir,src).split(path.sep).map(encodeURIComponent).join('/');
  return `src="${relative}"`;
}));
function frame(mobile) {
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${title}</title><style>
body{margin:0;background:#f1f2f4;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}
.preview-nav{padding:12px 18px;background:#252a32;color:white;text-align:center;font-size:13px;line-height:1.6}
.preview-nav a{color:#f4f5f7;margin:0 10px}
.preview-article{box-sizing:border-box;max-width:${mobile?'390':'700'}px;margin:28px auto;padding:34px 30px;background:#fff}
.preview-title{margin:0 0 28px;font-size:27px;line-height:1.5;font-weight:700;color:#1f2329}
@media(max-width:600px){.preview-article{margin:0 auto;padding:26px 20px}.preview-title{font-size:24px}}
</style></head><body><nav class="preview-nav">公众号本地审查稿 · <a href="wechat-review.html">桌面</a><a href="wechat-mobile.html">手机</a></nav><article class="preview-article"><h1 class="preview-title">${title}</h1><div data-wechat-preview-body="true">${body}</div></article></body></html>`;
}
const files=['wechat-review.html','wechat-mobile.html'];
if(files.some(name=>path.join(dir,name)===input)) throw Error('不能用预览覆盖同步输入文件。');
await fs.mkdir(dir,{recursive:true});
for(const [i,name] of files.entries()) await fs.writeFile(path.join(dir,name),frame(i===1),{mode:0o600});
console.log(JSON.stringify({syncSha256:createHash('sha256').update(sync).digest('hex'),previews:files.map(name=>path.join(dir,name))}));
