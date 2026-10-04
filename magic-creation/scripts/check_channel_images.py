#!/usr/bin/env python3
"""Compare saved-platform image measurements with an approved HTML/Markdown draft.

Read-only. Does not access a browser, upload files, or publish anything.
"""
import argparse
import json
import math
import re
from html.parser import HTMLParser
from pathlib import Path


class DraftImages(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag != 'img':
            return
        attrs = dict(attrs)
        width = attrs.get('width', '')
        if not re.fullmatch(r'\d+(?:\.\d+)?(?:px)?', width):
            match = re.search(r'(?:^|;)\s*width\s*:\s*(\d+(?:\.\d+)?)px\s*(?:;|$)', attrs.get('style', ''))
            width = match.group(1) if match else ''
        self.images.append({'alt': attrs.get('alt', ''), 'width': float(width.removesuffix('px')) if width else None})


def positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def check(source, measurements):
    parser = DraftImages()
    parser.feed(source)
    expected = parser.images
    issues = []
    # Plain Markdown images have no approved display width for this check.
    if re.search(r'!\[[^\]]*\]\(', source):
        issues.append('源稿包含未声明显示宽度的 Markdown 图片；先补齐尺寸基准。')
    if not expected:
        issues.append('源稿中没有带尺寸的 HTML 图片，无法验证。')
    if measurements.get('savedAndReloaded') is not True:
        issues.append('缺少平台保存后重新打开的测量结果。')
    content_width = measurements.get('contentWidth')
    if not positive(content_width):
        issues.append('缺少有效的正文栏宽度。')
    actual = measurements.get('images')
    if not isinstance(actual, list):
        actual = []
        issues.append('缺少正文图片测量列表。')
    if len(actual) != len(expected):
        issues.append(f'正文图片数量不符：源稿 {len(expected)}，平台 {len(actual)}。')
    for index, target in enumerate(expected):
        name = f'第 {index + 1} 张图（{target["alt"] or "无说明"}）'
        if not positive(target['width']):
            issues.append(f'{name}：源稿没有有效显示宽度。')
        if index >= len(actual):
            continue
        image = actual[index]
        if not isinstance(image, dict):
            issues.append(f'{name}：测量数据无效。')
            continue
        width, height = image.get('width'), image.get('height')
        natural_width, natural_height = image.get('naturalWidth'), image.get('naturalHeight')
        if image.get('complete') is not True or not all(positive(v) for v in (width, height, natural_width, natural_height)):
            issues.append(f'{name}：未加载完成或尺寸无效。')
            continue
        if positive(target['width']) and positive(content_width):
            wanted = min(target['width'], content_width)
            if abs(width - wanted) > 2:
                issues.append(f'{name}：应显示约 {wanted:g}px，实际 {width:g}px。')
        ratio = (width / height) / (natural_width / natural_height)
        if abs(ratio - 1) > 0.02:
            issues.append(f'{name}：显示比例与图片比例不符。')
    return {'passed': not issues, 'expectedImages': len(expected), 'actualImages': len(actual), 'issues': issues}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--source', required=True, type=Path, help='已审查渠道稿，HTML 或包含 HTML 图片的 Markdown')
    cli.add_argument('--measurements', required=True, type=Path, help='实际平台正文测量 JSON；不包含图片 URL 或令牌')
    args = cli.parse_args()
    try:
        data = json.loads(args.measurements.read_text())
        if not isinstance(data, dict):
            raise ValueError('测量 JSON 顶层必须是对象')
        result = check(args.source.read_text(), data)
    except (OSError, ValueError, TypeError) as error:
        print(json.dumps({'passed': False, 'issues': [str(error)]}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
