"""The review frame must not replace the HTML body that the CLI receives."""
from pathlib import Path
import subprocess
import tempfile
import unittest


class PreviewTests(unittest.TestCase):
    def test_preview_keeps_exported_body_and_image_layout(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            source=root/'sync.html'
            image=root/'assets/image with spaces.png'
            body='<section data-wechat-layout="editorial-v2"><p style="color:#383e47">正文 &amp; 来源</p>'
            body+=f'<img src="{image}" width="300" style="width:300px;max-width:100%;height:auto;"></section>'
            html=f'<html><head><title>审查 &amp; 同步</title></head><body>{body}</body></html>'
            source.write_text(html)
            result=subprocess.run(['node',str(Path(__file__).with_name('render_wechat_preview.mjs')),str(source)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            expected=body.replace(str(image),'assets/image%20with%20spaces.png')
            for name in ('wechat-review.html','wechat-mobile.html'):
                preview=(root/name).read_text()
                self.assertIn('<div data-wechat-preview-body="true">'+expected+'</div>',preview)
                self.assertIn('<title>审查 &amp; 同步</title>',preview)
            self.assertEqual(source.read_text(),html)

    def test_plain_html_is_not_misrepresented_as_wechat_export(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            source=root/'plain.html'
            source.write_text('<html><head><title>普通网页</title></head><body><p>正文</p></body></html>')
            result=subprocess.run(['node',str(Path(__file__).with_name('render_wechat_preview.mjs')),str(source)],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertFalse((root/'wechat-review.html').exists())


if __name__=='__main__':
    unittest.main()
