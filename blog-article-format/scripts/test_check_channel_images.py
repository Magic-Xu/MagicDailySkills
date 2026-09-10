import unittest
from check_channel_images import check

SOURCE = '<img src="phone.png" alt="手机截图" width="280"><img src="console.png" alt="后台截图" width="520">'


def measurements(column=720):
    return {'savedAndReloaded': True, 'contentWidth': column, 'images': [
        {'width': min(280, column), 'height': min(280, column)*2, 'naturalWidth': 840, 'naturalHeight': 1680, 'complete': True},
        {'width': min(520, column), 'height': min(520, column)/2, 'naturalWidth': 1040, 'naturalHeight': 520, 'complete': True},
    ]}


class ImageLayoutChecks(unittest.TestCase):
    def test_desktop_and_mobile_clamping(self):
        self.assertTrue(check(SOURCE, measurements())['passed'])
        self.assertTrue(check(SOURCE, measurements(348))['passed'])

    def test_full_width_phone_is_rejected(self):
        data = measurements()
        data['images'][0].update(width=720, height=1440)
        self.assertFalse(check(SOURCE, data)['passed'])

    def test_small_but_distorted_image_is_rejected(self):
        data = measurements()
        data['images'][0]['height'] = 100
        self.assertFalse(check(SOURCE, data)['passed'])

    def test_missing_or_failed_image_is_rejected(self):
        data = measurements()
        data['images'].pop()
        self.assertFalse(check(SOURCE, data)['passed'])
        data = measurements()
        data['images'][0].update(complete=True, naturalWidth=0)
        self.assertFalse(check(SOURCE, data)['passed'])

    def test_local_only_preview_is_not_platform_verification(self):
        data = measurements()
        data['savedAndReloaded'] = False
        self.assertFalse(check(SOURCE, data)['passed'])

    def test_unknown_baseline_and_invalid_numbers_are_rejected(self):
        self.assertFalse(check('![手机](phone.png)', measurements())['passed'])
        self.assertFalse(check('<img src="phone.png">', measurements())['passed'])
        data = measurements()
        data['images'][0]['width'] = float('nan')
        self.assertFalse(check(SOURCE, data)['passed'])


if __name__ == '__main__':
    unittest.main()
