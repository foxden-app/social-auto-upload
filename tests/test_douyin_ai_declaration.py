import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, call

from sau_cli import build_parser
from uploader.douyin_uploader.main import (
    DOUYIN_AI_DECLARATION,
    DOUYIN_OPINION_DECLARATION,
    DouYinVideo,
)


class DouyinAiDeclarationTests(unittest.TestCase):
    def test_cli_exposes_explicit_ai_generated_flag(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            video = Path(tmp_dir) / "video.mp4"
            video.write_bytes(b"video")
            args = build_parser().parse_args(
                [
                    "douyin",
                    "upload-video",
                    "--account",
                    "test",
                    "--file",
                    str(video),
                    "--title",
                    "test",
                    "--ai-generated",
                ]
            )

        self.assertTrue(args.ai_generated)

    def test_video_keeps_ai_generated_intent(self):
        video = DouYinVideo(
            "title",
            "video.mp4",
            [],
            0,
            "cookie.json",
            ai_generated=True,
        )

        self.assertTrue(video.ai_generated)
        self.assertEqual("内容由AI生成", DOUYIN_AI_DECLARATION)
        self.assertEqual("内容为个人观点或见解", DOUYIN_OPINION_DECLARATION)

    def test_required_ai_declaration_fails_explicitly(self):
        video = DouYinVideo(
            "title",
            "video.mp4",
            [],
            0,
            "cookie.json",
            ai_generated=True,
        )
        page = MagicMock()
        entry = MagicMock()
        entry.wait_for.side_effect = RuntimeError("declaration entry missing")
        page.get_by_text.return_value.first = entry

        with self.assertRaisesRegex(RuntimeError, "内容由AI生成"):
            asyncio.run(
                video.set_self_declaration(
                    page,
                    DOUYIN_AI_DECLARATION,
                    required=True,
                )
            )

    def test_thumbnail_accepts_hidden_cover_modal(self):
        video = DouYinVideo(
            "title",
            "video.mp4",
            [],
            0,
            "cookie.json",
            thumbnail_portrait_path="cover.png",
        )
        page = MagicMock()
        page.evaluate = AsyncMock()
        page.wait_for_selector = AsyncMock()
        page.wait_for_timeout = AsyncMock()
        page.get_by_text.return_value.first.click = AsyncMock()

        cover = MagicMock()
        cover.locator.return_value.nth.return_value.set_input_files = AsyncMock()
        cover.get_by_text.return_value.first.click = AsyncMock()
        cover.get_by_role.return_value.first.click = AsyncMock()
        cover.wait_for = AsyncMock()
        page.locator.return_value.first = cover

        asyncio.run(video.set_thumbnail(page))

        cover.wait_for.assert_awaited_once_with(state="hidden", timeout=20000)

    def test_thumbnail_retries_confirmation_when_modal_stays_visible(self):
        video = DouYinVideo(
            "title",
            "video.mp4",
            [],
            0,
            "cookie.json",
            thumbnail_portrait_path="cover.png",
        )
        page = MagicMock()
        page.evaluate = AsyncMock()
        page.wait_for_selector = AsyncMock()
        page.wait_for_timeout = AsyncMock()
        page.get_by_text.return_value.first.click = AsyncMock()

        cover = MagicMock()
        cover.locator.return_value.nth.return_value.set_input_files = AsyncMock()
        cover.get_by_text.return_value.first.click = AsyncMock()
        complete_button = cover.get_by_role.return_value.first
        complete_button.click = AsyncMock()
        cover.wait_for = AsyncMock(side_effect=[RuntimeError("still visible"), None])
        cover.is_visible = AsyncMock(return_value=True)
        page.locator.return_value.first = cover

        asyncio.run(video.set_thumbnail(page))

        self.assertEqual(2, complete_button.click.await_count)
        self.assertEqual(
            [call(state="hidden", timeout=20000), call(state="hidden", timeout=30000)],
            cover.wait_for.await_args_list,
        )


if __name__ == "__main__":
    unittest.main()
