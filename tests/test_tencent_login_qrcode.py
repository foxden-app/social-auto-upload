import asyncio
import base64
import unittest
from unittest.mock import AsyncMock, Mock

from uploader.tencent_uploader import main as tencent


class TencentLoginQrcodeTests(unittest.TestCase):
    def test_title_sanitizer_preserves_hotspot_words(self):
        title = "二零二六世界人工智能大会｜王坚谈科学基础模型（科技相声版）"

        cleaned = tencent.sanitize_tencent_title(title)

        self.assertEqual(cleaned, "二零二六世界人工智能大会：王坚谈科学基础模型 科技相声版")

    def test_title_sanitizer_removes_unsupported_hyphen(self):
        cleaned = tencent.sanitize_tencent_title("Kimi-K3让美国AI圈坐不住，不是因为拿了第一")

        self.assertEqual(cleaned, "Kimi K3让美国AI圈坐不住 不是因为拿了第一")

    def test_remote_qrcode_is_converted_to_data_url(self):
        locator = AsyncMock()
        locator.get_attribute.return_value = "https://open.weixin.qq.com/connect/qrcode/demo"
        locator.screenshot.return_value = b"png-bytes"

        data_url = asyncio.run(tencent._qrcode_locator_data_url(locator))

        expected = base64.b64encode(b"png-bytes").decode("ascii")
        self.assertEqual(data_url, f"data:image/png;base64,{expected}")

    def test_extract_qrcode_searches_cross_origin_frames(self):
        missing = AsyncMock()
        missing.count.return_value = 0
        missing.first = missing
        qrcode = AsyncMock()
        qrcode.count.return_value = 1
        qrcode.is_visible.return_value = True
        qrcode.get_attribute.return_value = "/connect/qrcode/demo"
        qrcode.screenshot.return_value = b"qr-image"
        qrcode.nth = Mock(return_value=qrcode)

        main_frame = Mock()
        main_frame.locator.return_value = missing
        login_frame = Mock()
        login_frame.locator.side_effect = lambda selector: qrcode if selector == "img.js_qrcode_img" else missing
        page = AsyncMock()
        page.frames = [main_frame, login_frame]

        data_url = asyncio.run(tencent._extract_tencent_qrcode_src(page))

        expected = base64.b64encode(b"qr-image").decode("ascii")
        self.assertEqual(data_url, f"data:image/png;base64,{expected}")

    def test_upload_access_rejects_login_redirect(self):
        page = AsyncMock()
        page.url = "https://channels.weixin.qq.com/login.html"
        page.frames = []

        self.assertFalse(asyncio.run(tencent._has_tencent_upload_access(page, max_checks=1)))

    def test_upload_access_requires_a_real_publish_marker(self):
        missing = AsyncMock()
        missing.count.return_value = 0
        missing.first = missing
        upload_input = AsyncMock()
        upload_input.count.return_value = 1
        frame = Mock()
        frame.locator.side_effect = lambda selector: upload_input if selector == 'input[type="file"]' else missing
        frame.get_by_text.return_value = missing
        page = AsyncMock()
        page.url = "https://channels.weixin.qq.com/platform/post/create"
        page.frames = [frame]

        self.assertTrue(asyncio.run(tencent._has_tencent_upload_access(page, max_checks=1)))


if __name__ == "__main__":
    unittest.main()
