"""Offline export checks. Set ARTICLE_RENDER_PROJECT to an installed Astro project."""
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
        self.links = []
        self.text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'img':
            self.images.append(attrs)
        elif tag == 'a':
            self.links.append(attrs.get('href'))

    def handle_data(self, data):
        self.text.append(data)


@unittest.skipUnless(os.environ.get('ARTICLE_RENDER_PROJECT'), 'Set ARTICLE_RENDER_PROJECT to an installed Astro project')
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

    def export(self, channel, body):
        source = self.article / 'draft.md'
        source.write_text('# Export check\n\n' + body)
        result = subprocess.run([
            'node', str(Path(__file__).with_name('prepare_channel_sync.mjs')),
            channel, str(source), str(self.output), '--project', os.environ['ARTICLE_RENDER_PROJECT'],
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


if __name__ == '__main__':
    unittest.main()
