// Keep the publication styles on the content itself: the platform can discard <style>.
export function formatWechat(html, {parseFragment, serialize}, {requireIntro=false}={}) {
  const tree = parseFragment(html);
  const text = node => node.nodeName === '#text' ? node.value : (node.childNodes || []).map(text).join('');
  const base = {
    p: 'margin:0 0 20px;font-size:16px;line-height:1.85;color:#383e47;letter-spacing:0.3px;text-align:left;overflow-wrap:anywhere;',
    h2: 'margin:42px 0 22px;padding:0 0 12px;border-bottom:2px solid #d9dde4;font-size:22px;line-height:1.5;font-weight:700;color:#1f2329;text-align:left;',
    h3: 'margin:30px 0 16px;padding-left:10px;border-left:3px solid #2f7d71;font-size:18px;line-height:1.5;font-weight:700;color:#1f2329;',
    strong: 'font-weight:700;color:#1f2329;',
    blockquote: 'margin:24px 0;padding:18px 18px 1px;border-left:3px solid #abb3bf;background:#f5f6f8;color:#4b5563;',
    ul: 'margin:8px 0 24px;padding-left:24px;list-style-type:disc;',
    ol: 'margin:8px 0 24px;padding-left:26px;list-style-type:decimal;',
    li: 'margin:0 0 12px;font-size:16px;line-height:1.8;color:#383e47;',
    pre: 'margin:22px 0 24px;padding:18px 16px;background:#f5f6f8;border:1px solid #e1e5eb;border-radius:8px;white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word;font-size:13px;line-height:1.75;color:#334155;',
    code: 'font-family:Menlo,Consolas,monospace;font-size:0.88em;padding:2px 4px;border-radius:3px;background:#eef2f7;color:#275d8a;overflow-wrap:anywhere;',
    a: 'color:#275d8a;text-decoration:underline;overflow-wrap:anywhere;',
    hr: 'margin:32px 0;border:0;border-top:1px solid #d9dde4;',
    table: 'margin:20px 0;border-collapse:collapse;width:100%;font-size:14px;line-height:1.7;',
    th: 'padding:10px;border:1px solid #d9dde4;background:#f1f3f6;text-align:left;',
    td: 'padding:10px;border:1px solid #d9dde4;text-align:left;',
  };
  function style(node, value, override=false) {
    const current = node.attrs?.find(attr => attr.name === 'style');
    if(current) current.value = override ? current.value + value : value + current.value;
    else (node.attrs ||= []).push({name:'style',value});
  }
  const callouts = {
    warning: {frame:'border-left-color:#c68a35;background:#fff6e8;', color:'#684b2d', emphasis:'#7c4a16'},
    prompt: {frame:'border-left-color:#6683aa;background:#f0f4fa;', color:'#394b63', emphasis:'#2b4669'},
  };
  const visibleNode = node => node.nodeName !== '#comment' && (node.nodeName !== '#text' || node.value.trim());
  function followsImage(node) {
    const siblings = node.parentNode?.childNodes || [];
    let previous = siblings.slice(0,siblings.indexOf(node)).reverse().find(visibleNode);
    // Recognize the existing image wrappers without treating any earlier image
    // elsewhere in a container as the caption's subject.
    while (previous && ['div','p','figure'].includes(previous.tagName)) {
      const children = (previous.childNodes || []).filter(visibleNode);
      if (children.length !== 1) return false;
      previous = children[0];
    }
    return previous?.tagName === 'img';
  }
  function visit(node, inQuote=false, inPre=false, quote=null) {
    const kind = node.attrs?.find(attr=>attr.name==='data-wechat-kind')?.value;
    const variant = Object.hasOwn(callouts,kind) ? callouts[kind] : null;
    const authorPanel = (node.tagName==='section' || node.tagName==='blockquote') && variant;
    const quoteContainer = node.tagName==='blockquote' || authorPanel;
    if(base[node.tagName]) style(node,base[node.tagName]);
    if(authorPanel && node.tagName==='section') style(node,base.blockquote);
    if(quoteContainer) {
      quote = variant || {frame:'',color:'#4b5563',emphasis:'#1f2329'};
      style(node,quote.frame+'color:'+quote.color+';',true);
      // Author prompts and notes are ordinary panels, not quoted-source widgets.
      if(authorPanel) node.tagName=node.nodeName='section';
    }
    if(node.tagName==='p' && inQuote) style(node,'font-size:15px;line-height:1.8;color:'+quote.color+';',true);
    if(node.tagName==='strong' && inQuote) style(node,'color:'+quote.emphasis+';',true);
    if(node.tagName==='code' && inPre) style(node,'font-size:inherit;padding:0;background:none;',true);
    // Explicit captions, plus the existing image-followed-by-italic convention.
    // An italic paragraph elsewhere remains ordinary emphasized prose.
    const italicParagraph = node.childNodes?.length===1 && node.childNodes[0].tagName==='em';
    const markedCaption = node.attrs?.some(attr=>attr.name==='data-wechat-caption' && attr.value==='true');
    if(node.tagName==='p' && (markedCaption || (italicParagraph && followsImage(node)))) {
      style(node,'margin:-8px 0 26px;font-size:12px;line-height:1.6;color:#667085;text-align:center;',true);
      if(italicParagraph) style(node.childNodes[0],'font-style:normal;');
    }
    for(const child of node.childNodes || []) visit(child,inQuote||quoteContainer,inPre||node.tagName==='pre',quote);
  }
  visit(tree);
  // Conservative guard based on the editor's 300-character quote limit observed
  // on 2026-09-18. This is not a whole-article limit or an exact platform counter.
  function checkQuotes(node) {
    if(node.tagName==='blockquote') {
      const count=Array.from(text(node).replace(/\s+/gu,' ').trim()).length;
      if(count>300) throw Error(`公众号引用块超过 300 个字符（保守预检：${count}）。请精简真实引用；自写提示词或提醒使用 data-wechat-kind="prompt" / "warning" 普通容器。`);
    }
    for(const child of node.childNodes || []) checkQuotes(child);
  }
  checkQuotes(tree);
  // Directory hierarchy must survive editors that normalize code-block whitespace.
  function layoutDirectoryTrees(parent) {
    parent.childNodes = (parent.childNodes || []).map(node => {
      const code = node.tagName === 'pre' && node.childNodes?.find(child => child.tagName === 'code');
      const plainText = code?.attrs?.some(attr => attr.name === 'class' && attr.value.split(/\s+/).includes('language-text'));
      const source = code && text(code).replace(/\r\n?/g, '\n').replace(/\n$/, '');
      if (plainText && /(^|\n)[ │]*[├└]── /.test(source)) {
        const block = parseFragment('<section data-wechat-directory="true"></section>').childNodes[0];
        style(block, base.pre.replace('white-space:pre-wrap;', '') + 'font-family:Menlo,Consolas,monospace;');
        block.parentNode = parent;
        block.childNodes = source.split('\n').map(line => {
          const paragraph = parseFragment('<p><span></span></p>').childNodes[0];
          const span = paragraph.childNodes[0];
          style(paragraph, 'margin:0;padding:0;font-family:Menlo,Consolas,monospace;font-size:13px;line-height:1.75;color:#334155;letter-spacing:0;text-align:left;overflow-wrap:anywhere;word-break:break-word;');
          style(span, 'font-family:Menlo,Consolas,monospace;font-size:13px;line-height:1.75;');
          // NBSP preserves the tree's indentation even without white-space CSS.
          // Each row is a real paragraph, so source newlines cannot collapse.
          span.childNodes = [{nodeName:'#text', value:line.replace(/ /g, '\u00a0') || '\u00a0', parentNode:span}];
          paragraph.parentNode = block;
          return paragraph;
        });
        return block;
      }
      if (node.childNodes) layoutDirectoryTrees(node);
      return node;
    });
  }
  layoutDirectoryTrees(tree);
  const content = tree.childNodes.filter(n=>n.nodeName!=='#text'||n.value.trim());
  // Guide paragraphs may follow the opening background. Recognize them only
  // before the first section heading, without moving any author content.
  const headingIndex=content.findIndex(node=>/^h[1-6]$/.test(node.tagName || ''));
  const opening=content.slice(0,headingIndex<0 ? content.length : headingIndex);
  const introStart=opening.findIndex(node=>node.tagName==='p' && /^(阅读时间|适用读者)[：:]/.test(text(node)));
  const hasReadingTime=introStart>=0 && /^阅读时间[：:]/.test(text(opening[introStart]));
  const introLabels=[...(hasReadingTime ? ['阅读时间'] : []),'适用读者','文章收获','一句话总结'];
  const hasIntro=introStart>=0 && introLabels.every((label,i)=>opening[introStart+i]?.tagName==='p' && new RegExp('^'+label+'[：:]\\s*\\S').test(text(opening[introStart+i])));
  if(requireIntro && !hasIntro) throw Error('已启用公众号导读模板检查：首节标题之前须依次包含非空的适用读者、文章收获、一句话总结；可在三项之前附阅读时间，背景段落保留原位。');
  if(hasIntro) {
    const intro=parseFragment('<section data-wechat-intro="true"></section>').childNodes[0];
    intro.childNodes=content.slice(introStart,introStart+introLabels.length);
    style(intro,'margin:24px 0 30px;padding:20px 20px 4px;background:#f3f5f8;border-top:3px solid #2f7d71;border-radius:0 0 8px 8px;');
    for(const [i,node] of intro.childNodes.entries()) {
      node.parentNode=intro;
      node.attrs.find(a=>a.name==='style').value += hasReadingTime && i===0
        ? 'font-size:13px;color:#667085;margin-bottom:14px;'
        : 'font-size:14px;line-height:1.75;margin-bottom:14px;';
    }
    tree.childNodes=[...content.slice(0,introStart),intro,...content.slice(introStart+introLabels.length)];
    intro.parentNode=tree;
  }
  let references=false;
  for(const node of tree.childNodes) {
    if(node.tagName==='h2') references=text(node).trim()==='参考资料';
    if(references && node.tagName==='p') {
      node.attrs.find(a=>a.name==='style').value+='font-size:12px;line-height:1.65;color:#667085;margin-bottom:12px;';
    }
  }
  return '<section data-wechat-layout="editorial-v2" style="font-family:-apple-system,BlinkMacSystemFont,\'PingFang SC\',\'Microsoft YaHei\',sans-serif;font-size:16px;line-height:1.85;color:#383e47;text-align:left;word-wrap:break-word;">'+serialize(tree)+'</section>';
}
