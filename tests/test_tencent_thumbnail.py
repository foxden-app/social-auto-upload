import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from uploader.tencent_uploader.main import TencentVideo


def make_uploader() -> TencentVideo:
    return TencentVideo(
        title="测试视频",
        file_path="video.mp4",
        tags=[],
        publish_date=0,
        account_file="account.json",
        thumbnail_landscape_path="landscape.png",
        thumbnail_portrait_path="portrait.png",
    )


class TencentThumbnailTests(unittest.TestCase):
    def test_landscape_cover_uses_actual_horizon_selector(self):
        uploader = make_uploader()
        page = AsyncMock()

        with patch.object(uploader, "set_single_thumbnail", new=AsyncMock()) as set_thumbnail:
            asyncio.run(uploader.set_thumbnail(page))

        landscape_selectors = set_thumbnail.await_args_list[0].args[2]
        self.assertIn('div.horizon-cover-wrap:has-text("4:3")', landscape_selectors)
        self.assertEqual(set_thumbnail.await_count, 2)

    def test_missing_cover_entry_stops_publish(self):
        uploader = make_uploader()
        page = AsyncMock()

        with patch.object(uploader, "open_thumbnail_dialog", new=AsyncMock(return_value=None)):
            with self.assertRaisesRegex(RuntimeError, "已中止发布"):
                asyncio.run(
                    uploader.set_single_thumbnail(
                        page,
                        "landscape.png",
                        ['div.horizon-cover-wrap:has-text("4:3")'],
                        ["编辑视频号动态封面"],
                        "4:3 横版",
                    )
                )

    def test_cover_upload_error_stops_publish(self):
        uploader = make_uploader()
        page = AsyncMock()
        dialog = AsyncMock()

        with patch.object(uploader, "open_thumbnail_dialog", new=AsyncMock(return_value=dialog)):
            with patch.object(
                uploader,
                "upload_thumbnail_in_dialog",
                new=AsyncMock(side_effect=TimeoutError("确认按钮超时")),
            ):
                with self.assertRaisesRegex(RuntimeError, "封面设置失败"):
                    asyncio.run(
                        uploader.set_single_thumbnail(
                            page,
                            "landscape.png",
                            ['div.horizon-cover-wrap:has-text("4:3")'],
                            ["编辑视频号动态封面"],
                            "4:3 横版",
                        )
                    )


if __name__ == "__main__":
    unittest.main()
