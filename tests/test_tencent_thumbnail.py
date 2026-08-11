import asyncio
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from uploader.tencent_uploader.main import TencentVideo
from uploader.tencent_uploader.main import _build_launch_kwargs


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
    def test_launch_kwargs_accept_explicit_browser_proxy(self):
        with patch.dict(os.environ, {"SAU_BROWSER_PROXY": "http://172.29.96.1:17897"}):
            launch_kwargs = _build_launch_kwargs(headless=True)

        self.assertEqual(launch_kwargs["proxy"], {"server": "http://172.29.96.1:17897"})

    def test_portrait_thumbnail_clicks_the_cover_image(self):
        uploader = make_uploader()
        page = MagicMock()
        page.wait_for_timeout = AsyncMock()
        entry = MagicMock()
        entry.count = AsyncMock(return_value=1)
        entry.wait_for = AsyncMock()
        entry.click = AsyncMock()
        cover_image = MagicMock()
        cover_image.click = AsyncMock()
        entry.locator.return_value = MagicMock(first=cover_image)
        entry_locator = MagicMock(first=entry)
        dialog = MagicMock()
        dialog.count = AsyncMock(side_effect=[0, 1])
        dialog_locator = MagicMock(first=dialog)
        dialog_base = MagicMock()
        dialog_base.filter.return_value = dialog_locator

        def locate(selector):
            if selector == "div.weui-desktop-dialog:visible":
                return dialog_base
            return entry_locator

        page.locator.side_effect = locate
        found = asyncio.run(
            uploader.open_thumbnail_dialog(
                page,
                ['div.vertical-cover-wrap:has-text("3:4")'],
                ["编辑个人主页卡片"],
                "portrait-image",
            )
        )

        self.assertIs(found, dialog)
        entry.locator.assert_called_once_with("img.vertical-img-size")
        cover_image.click.assert_awaited_once()
        entry.click.assert_not_awaited()
        page.wait_for_timeout.assert_awaited_once_with(500)

    def test_landscape_thumbnail_uses_direct_edit_popover(self):
        uploader = make_uploader()
        page = MagicMock()
        entry = MagicMock()
        entry.count = AsyncMock(return_value=1)
        entry.wait_for = AsyncMock()
        cover_image = MagicMock()
        cover_image.click = AsyncMock()
        entry.locator.return_value = MagicMock(first=cover_image)
        dialog = MagicMock()
        dialog.count = AsyncMock(return_value=1)
        dialog_base = MagicMock()
        dialog_base.filter.return_value = MagicMock(first=dialog)

        def locate(selector):
            if selector == "div.weui-desktop-dialog:visible":
                return dialog_base
            return MagicMock(first=entry)

        page.locator.side_effect = locate
        direct_edit = MagicMock()
        direct_edit.wait_for = AsyncMock()
        direct_edit.click = AsyncMock()
        page.get_by_text.return_value = MagicMock(first=direct_edit)

        found = asyncio.run(
            uploader.open_thumbnail_dialog(
                page,
                ['div.horizon-cover-wrap:has-text("4:3")'],
                ["编辑分享卡片"],
                "landscape-direct-edit",
            )
        )

        self.assertIsNotNone(found)
        cover_image.click.assert_awaited_once()
        direct_edit.click.assert_awaited_once()

    def test_landscape_cover_uses_actual_horizon_selector(self):
        uploader = make_uploader()
        page = AsyncMock()

        with patch.object(uploader, "set_single_thumbnail", new=AsyncMock()) as set_thumbnail:
            asyncio.run(uploader.set_thumbnail(page))

        landscape_selectors = set_thumbnail.await_args_list[1].args[2]
        landscape_dialog_titles = set_thumbnail.await_args_list[1].args[3]
        portrait_mode = set_thumbnail.await_args_list[0].args[5]
        landscape_mode = set_thumbnail.await_args_list[1].args[5]
        self.assertIn('div.horizon-cover-wrap:has-text("4:3")', landscape_selectors)
        self.assertIn("编辑分享卡片", landscape_dialog_titles)
        self.assertEqual(portrait_mode, "portrait-image")
        self.assertEqual(landscape_mode, "landscape-direct-edit")
        self.assertEqual(set_thumbnail.await_count, 2)

    def test_cover_upload_uses_current_generic_image_input(self):
        uploader = make_uploader()
        page = AsyncMock()
        cover_dialog = MagicMock()
        cover_dialog.wait_for = AsyncMock()
        file_input = AsyncMock()
        confirm_button = AsyncMock()
        cover_dialog.locator.side_effect = [
            MagicMock(first=file_input),
            MagicMock(first=confirm_button),
        ]

        with patch.object(uploader, "confirm_thumbnail_crop", new=AsyncMock()):
            asyncio.run(uploader.upload_thumbnail_in_dialog(page, cover_dialog, "landscape.png"))

        self.assertEqual(
            cover_dialog.locator.call_args_list[0].args[0],
            'input[type="file"][accept*="image"]',
        )
        file_input.set_input_files.assert_awaited_once_with("landscape.png")
        self.assertEqual(cover_dialog.wait_for.await_args_list[-1].kwargs["state"], "hidden")

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
                        "landscape-direct-edit",
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
                            "landscape-direct-edit",
                        )
                    )

    def test_upload_error_stops_after_retry_limit(self):
        uploader = make_uploader()
        page = MagicMock()
        publish_button = MagicMock()
        publish_button.get_attribute = AsyncMock(return_value="weui-desktop-btn_disabled")
        page.get_by_role.return_value = MagicMock(first=publish_button)
        upload_error = MagicMock()
        upload_error.count = AsyncMock(return_value=1)
        upload_error.inner_text = AsyncMock(return_value="网络出错，请重新上传。")
        delete_button = MagicMock()
        delete_button.count = AsyncMock(return_value=1)

        def locate(selector):
            if selector == "div.status-msg.error:visible":
                return MagicMock(first=upload_error)
            return delete_button

        page.locator.side_effect = locate
        with patch.dict(os.environ, {"SAU_TENCENT_UPLOAD_MAX_RETRIES": "0"}):
            with self.assertRaisesRegex(RuntimeError, "最大重试次数"):
                asyncio.run(uploader.wait_for_upload_complete(page))

    def test_upload_file_does_not_depend_on_locator_count(self):
        uploader = make_uploader()
        page = MagicMock()
        file_input = MagicMock()
        file_input.wait_for = AsyncMock()
        file_input.set_input_files = AsyncMock()
        file_input_locator = MagicMock(first=file_input)
        frame = MagicMock()
        frame.locator.return_value = file_input_locator
        page.frames = [frame]

        asyncio.run(uploader.upload_video_file(page, "video.mp4"))

        file_input.wait_for.assert_awaited_once_with(state="attached", timeout=200)
        file_input.set_input_files.assert_awaited_once_with("video.mp4")
        file_input.count.assert_not_called()


if __name__ == "__main__":
    unittest.main()
