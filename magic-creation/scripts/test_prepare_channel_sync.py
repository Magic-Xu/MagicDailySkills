"""Offline export checks. ARTICLE_RENDER_PROJECT optionally exercises legacy callers."""
import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from html.parser import HTMLParser


class Content(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.elements = []
        self.links = []
        self.text = []
        self.paragraphs = []
        self.paragraph = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.elements.append((tag,attrs))
        if tag == 'p':
            self.paragraph = []
        if tag == 'img':
            self.images.append(attrs)
        elif tag == 'a':
            self.links.append(attrs.get('href'))

    def handle_data(self, data):
        self.text.append(data)
        if self.paragraph is not None:
            self.paragraph.append(data)

    def handle_endtag(self, tag):
        if tag == 'p' and self.paragraph is not None:
            self.paragraphs.append(''.join(self.paragraph))
            self.paragraph = None


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='article-export-')
        self.addCleanup(self.tmp.cleanup)
        self.article = Path(self.tmp.name) / 'outside-project'
        self.article.mkdir()
        (self.article / 'assets').mkdir()
        (self.article / 'assets/phone.png').write_bytes(base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aCXQAAAAASUVORK5CYII='))
        self.output = self.article / 'sync.html'

    def export(self, channel, body, *, include_intro=False, options=()):
        source = self.article / 'draft.md'
        if channel=='wechat' and include_intro and not body.startswith('**阅读时间'):
            intro='\n\n'.join('**'+label+'：** 测试导读' for label in ('阅读时间','适用读者','文章收获','一句话总结'))
            body=intro+'\n\n'+body
        source.write_text('# Export check\n\n' + body)
        result = subprocess.run([
            'node', str(Path(__file__).with_name('prepare_channel_sync.mjs')),
            channel, str(source), str(self.output), *(['--project', os.environ['ARTICLE_RENDER_PROJECT']] if os.environ.get('ARTICLE_RENDER_PROJECT') else []), *options,
        ], capture_output=True, text=True)
        return result

    @staticmethod
    def image(width=True):
        size = ' width="300" style="width:300px;max-width:100%;height:auto;display:block;margin:24px auto;"' if width else ''
        return f'<div align="center">\n<img src="assets/phone.png" alt="测试图片"{size} />\n</div>\n'

    def parsed(self):
        content = Content()
        content.feed(self.output.read_text())
        return content

    def test_external_article_directory_keeps_local_image_and_width(self):
        result = self.export('wechat', self.image())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['images'], 1)
        image = self.parsed().images[0]
        self.assertEqual(image['src'], str(self.article / 'assets/phone.png'))
        self.assertEqual(image['width'], '300')
        self.assertIn('max-width:100%', image['style'])
        self.assertEqual(image['alt'], '测试图片')

    def test_wechat_rejects_hidden_external_destination(self):
        result = self.export('wechat', '[资料](https://example.org/docs?a=1&b=2#restore)')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())

    def test_wechat_visible_address_survives_anchor_removal(self):
        url = 'https://example.org/docs?a=1&b=2#restore'
        result = self.export('wechat', f'[资料]({url})\n\n参考资料：\n\n{url}\n\n' + self.image())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(url, ''.join(self.parsed().text))

    def test_juejin_keeps_clickable_link(self):
        url = 'https://example.org/docs#restore'
        result = self.export('juejin', f'[资料]({url})\n\n' + self.image())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(url, self.parsed().links)
        self.assertEqual(self.parsed().images[0]['width'], '300')

    def test_image_without_reviewed_width_blocks_export(self):
        result = self.export('wechat', self.image(width=False))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())

    def test_text_only_article_needs_no_artificial_image(self):
        result = self.export('wechat', '一篇没有配图的文章。')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['images'], 0)

    def test_wechat_body_style_survives_stylesheet_removal(self):
        result = self.export('wechat', '## 标题\n\n正文与 **重点**。\n\n> 引用\n\n```bash\necho ok\n```')
        self.assertEqual(result.returncode, 0, result.stderr)
        content = self.parsed()
        for tag in ('section', 'h2', 'p', 'strong', 'blockquote', 'pre', 'code'):
            elements = [attrs for name, attrs in content.elements if name == tag]
            self.assertTrue(elements, tag)
            self.assertTrue(all(attrs.get('style') for attrs in elements), tag)
        self.assertIn('font-size:16px', next(a['style'] for t,a in content.elements if t=='p'))
        self.assertIn('white-space:pre-wrap', next(a['style'] for t,a in content.elements if t=='pre'))

    def test_intro_and_references_keep_their_content(self):
        body = '\n\n'.join('**' + label + '：** 内容' for label in ('阅读时间','适用读者','文章收获','一句话总结'))
        body += '\n\n## 参考资料\n\nhttps://example.org/source'
        result = self.export('wechat', body)
        self.assertEqual(result.returncode, 0, result.stderr)
        content = self.parsed()
        self.assertEqual(sum('data-wechat-intro' in a for _,a in content.elements), 1)
        self.assertEqual(''.join(content.text).count('内容'), 4)
        self.assertIn('https://example.org/source', ''.join(content.text))

    def test_intro_after_background_preserves_order_and_inline_design(self):
        guide=['**'+label+'：** '+value for label,value in zip(
            ('适用读者','文章收获','一句话总结'),('目标读者','具体收获','核心判断'))]
        for reading_time in (False,True):
            with self.subTest(reading_time=reading_time):
                fields=(['**阅读时间：** 约 5 分钟'] if reading_time else [])+guide
                before=['先交代背景。','另一段背景。']
                body='\n\n'.join(before+fields+['## 第一节','正文内容。'])
                result=self.export('wechat',body,options=('--require-intro',))
                self.assertEqual(result.returncode,0,result.stderr)
                content=self.parsed()
                panel=next(a for _,a in content.elements if 'data-wechat-intro' in a)
                self.assertIn('background:',panel['style'])
                self.assertIn('border-top:',panel['style'])
                expected=before+([ '阅读时间： 约 5 分钟'] if reading_time else [])+[
                    '适用读者： 目标读者','文章收获： 具体收获','一句话总结： 核心判断','正文内容。']
                self.assertEqual(content.paragraphs,expected)
                # The opening must remain outside the guide, before it.
                html=self.output.read_text()
                self.assertLess(html.index('另一段背景。'),html.index('data-wechat-intro'))
                self.assertLess(html.index('核心判断'),html.index('<h2'))

    def test_guide_labels_in_body_do_not_become_an_opening_panel(self):
        body='正文开场。\n\n## 正文案例\n\n'+'\n\n'.join(
            '**'+label+'：** 示例' for label in ('适用读者','文章收获','一句话总结'))
        result=self.export('wechat',body)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse(any('data-wechat-intro' in a for _,a in self.parsed().elements))
        self.output.unlink()
        result=self.export('wechat',body,options=('--require-intro',))
        self.assertNotEqual(result.returncode,0)
        self.assertFalse(self.output.exists())

    def test_directory_rows_and_indentation_survive_whitespace_normalization(self):
        rows = ['workspace/', '├── app/', '│   └── tools/release/',
                '│       └── validate_store_listing.py', '└── app-legal/',
                '    ├── content/', '    │   └── legal.json', '    └── assets/a&b.html']
        result = self.export('wechat', '```text\n' + '\n'.join(rows) + '\n```', include_intro=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        content = self.parsed()
        # Paragraphs remain separate when an editor discards pre/white-space behavior.
        import re
        visible = [re.sub(r'[ \t\r\n]+', ' ', row).replace('\u00a0', ' ')
                   for row in content.paragraphs[4:]]
        self.assertEqual(visible, rows)
        self.assertFalse(any(tag == 'pre' for tag, _ in content.elements))
        self.assertEqual(content.links, [])

    def test_directory_fix_does_not_change_commands_or_juejin(self):
        for channel, language, code in [('wechat', 'bash', 'echo first\necho second'),
                                         ('juejin', 'text', 'workspace/\n└── app/')]:
            with self.subTest(channel=channel):
                result = self.export(channel, f'```{language}\n{code}\n```')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(any(tag == 'pre' for tag, _ in self.parsed().elements))
                self.assertIn(code, ''.join(self.parsed().text))

    def test_long_author_prompt_is_not_exported_as_a_quotation_widget(self):
        prompt = '读取项目代码并核对数据处理。' * 30
        body = '<blockquote data-wechat-kind="prompt">\n\n' + prompt + '\n\n</blockquote>\n\n> 官方来源的短引用。'
        result = self.export('wechat', body)
        self.assertEqual(result.returncode, 0, result.stderr)
        content = self.parsed()
        self.assertIn(prompt, ''.join(content.text))
        self.assertGreater(len(prompt), 300)
        self.assertEqual([tag for tag, attrs in content.elements if attrs.get('data-wechat-kind')=='prompt'], ['section'])
        self.assertEqual(sum(tag=='blockquote' for tag, _ in content.elements), 1)
        self.assertIn('官方来源的短引用。', ''.join(content.text))

    def test_native_author_panel_retains_long_content_and_inline_styles(self):
        prompt='检查每项功能的实际处理方式。'*30
        result=self.export('wechat',f'<section data-wechat-kind="prompt">\n\n{prompt}\n\n</section>')
        self.assertEqual(result.returncode,0,result.stderr)
        content=self.parsed()
        self.assertIn(prompt,''.join(content.text))
        self.assertFalse(any(tag=='blockquote' for tag,_ in content.elements))
        panel=next(attrs for _,attrs in content.elements if attrs.get('data-wechat-kind')=='prompt')
        self.assertIn('background:',panel['style'])

    def test_article_can_start_with_ordinary_prose(self):
        result=self.export('wechat','今天想聊聊一个小发现。')
        self.assertEqual(result.returncode,0,result.stderr)
        content=self.parsed()
        self.assertIn('今天想聊聊一个小发现。',''.join(content.text))
        self.assertFalse(any('data-wechat-intro' in attrs for _,attrs in content.elements))

    def test_required_intro_rejects_missing_reordered_or_empty_fields(self):
        empty_fields='\n\n'.join('**'+label+'：**' for label in ('阅读时间','适用读者','文章收获','一句话总结'))
        for body in ('直接开始正文。','**文章收获：** 内容\n\n**适用读者：** 内容',empty_fields):
            with self.subTest(body=body):
                result=self.export('wechat',body,options=('--require-intro',))
                self.assertNotEqual(result.returncode,0)
                self.assertIn('已启用公众号导读模板检查',result.stderr)
                self.assertFalse(self.output.exists())

    def test_required_intro_accepts_complete_template(self):
        result=self.export('wechat','正文。',include_intro=True,options=('--require-intro',))
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(sum('data-wechat-intro' in attrs for _,attrs in self.parsed().elements),1)

    def test_legacy_allow_no_intro_keeps_other_guards(self):
        result=self.export('wechat','直接开始正文。',options=('--allow-no-intro',))
        self.assertEqual(result.returncode,0,result.stderr)
        self.output.unlink()
        result=self.export('wechat','> '+'引'*301,options=('--allow-no-intro',))
        self.assertNotEqual(result.returncode,0)
        self.assertFalse(self.output.exists())

    def test_intro_options_reject_conflicts_duplicates_and_other_channels(self):
        for options in (('--require-intro','--allow-no-intro'),
                        ('--allow-no-intro','--require-intro'),
                        ('--require-intro','--require-intro'),
                        ('--allow-no-intro','--allow-no-intro')):
            with self.subTest(options=options):
                result=self.export('wechat','正文。',options=options)
                self.assertNotEqual(result.returncode,0)
                self.assertFalse(self.output.exists())
        for option in ('--require-intro','--allow-no-intro'):
            with self.subTest(channel='juejin',option=option):
                result=self.export('juejin','正文。',options=(option,))
                self.assertNotEqual(result.returncode,0)
                self.assertFalse(self.output.exists())

    def test_italic_prose_is_not_a_caption(self):
        result=self.export('wechat','*这一段是作者想强调的完整意思。*')
        self.assertEqual(result.returncode,0,result.stderr)
        content=self.parsed()
        paragraph=next(attrs for tag,attrs in content.elements if tag=='p')
        emphasis=next(attrs for tag,attrs in content.elements if tag=='em')
        self.assertIn('font-size:16px;',paragraph['style'])
        self.assertNotIn('font-size:12px;',paragraph['style'])
        self.assertNotIn('text-align:center;',paragraph['style'])
        self.assertNotIn('font-style:normal',emphasis.get('style',''))

    def test_marked_and_image_adjacent_captions_keep_caption_layout(self):
        examples=(('<p data-wechat-caption="true">示意图说明。</p>','示意图说明。'),
                  (self.image()+'\n*图片来源与说明。*','图片来源与说明。'))
        for body,caption in examples:
            with self.subTest(body=body):
                result=self.export('wechat',body)
                self.assertEqual(result.returncode,0,result.stderr)
                content=self.parsed()
                self.assertIn(caption,content.paragraphs)
                paragraph=next(attrs for tag,attrs in content.elements if tag=='p')
                self.assertIn('font-size:12px;',paragraph['style'])
                self.assertIn('text-align:center;',paragraph['style'])

    def test_italic_prose_separated_from_image_is_not_a_caption(self):
        result=self.export('wechat',self.image()+'\n普通正文。\n\n*需要强调的意思。*')
        self.assertEqual(result.returncode,0,result.stderr)
        paragraphs=[attrs for tag,attrs in self.parsed().elements if tag=='p']
        self.assertEqual(len(paragraphs),2)
        self.assertTrue(all('font-size:12px;' not in attrs['style'] for attrs in paragraphs))

    def test_real_quote_length_guard(self):
        result=self.export('wechat','> '+'引'*300)
        self.assertEqual(result.returncode,0,result.stderr)
        self.output.unlink()
        result=self.export('wechat','> '+'引'*301)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('引用块超过 300',result.stderr)
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
