import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

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


if __name__ == "__main__":
    unittest.main()
