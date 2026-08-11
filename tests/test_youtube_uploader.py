import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from uploader.youtube_uploader.main import _done_button_ready
from uploader.youtube_uploader.main import _video_id_from_studio_url
from uploader.youtube_uploader.main import is_thumbnail_verification_text
from uploader.youtube_uploader.main import _set_not_for_kids
from uploader.youtube_uploader.main import _wait_for_studio_channel
from uploader.youtube_uploader.main import YOUTUBE_CONTEXT_OPTIONS


class YouTubeUploaderTests(unittest.TestCase):
    def test_browser_context_prefers_simplified_chinese(self):
        self.assertEqual("zh-CN", YOUTUBE_CONTEXT_OPTIONS["locale"])
        self.assertIn("zh-CN", YOUTUBE_CONTEXT_OPTIONS["extra_http_headers"]["Accept-Language"])

    def test_extracts_video_id_from_studio_draft_url(self):
        self.assertEqual(
            "abc_DEF-123",
            _video_id_from_studio_url("https://studio.youtube.com/video/abc_DEF-123/edit"),
        )

    def test_not_for_kids_uses_visible_dialog_option_and_verifies_selection(self):
        page = MagicMock()
        page.wait_for_timeout = AsyncMock()
        hidden = AsyncMock()
        hidden.is_visible.return_value = False
        visible = AsyncMock()
        visible.is_visible.return_value = True
        visible.get_attribute.return_value = "true"
        candidates = MagicMock()
        candidates.count = AsyncMock(return_value=2)
        candidates.nth.side_effect = lambda index: [hidden, visible][index]
        page.locator.return_value = candidates

        self.assertTrue(asyncio.run(_set_not_for_kids(page)))
        visible.click.assert_awaited_once()
        hidden.click.assert_not_awaited()

    def test_not_for_kids_forces_click_when_an_overlay_intercepts_it(self):
        page = MagicMock()
        page.wait_for_timeout = AsyncMock()
        option = AsyncMock()
        option.is_visible.return_value = True
        option.click.side_effect = [TimeoutError("covered"), None]
        option.get_attribute.return_value = "true"
        candidates = MagicMock()
        candidates.count = AsyncMock(return_value=1)
        candidates.nth.return_value = option
        page.locator.return_value = candidates

        self.assertTrue(asyncio.run(_set_not_for_kids(page)))
        self.assertEqual(option.click.await_count, 2)
        self.assertTrue(option.click.await_args_list[-1].kwargs["force"])

    def test_done_button_ready_requires_an_enabled_visible_button(self):
        page = MagicMock()
        button = AsyncMock()
        button.count.return_value = 1
        button.is_visible.return_value = True
        button.get_attribute.side_effect = lambda name, **_kwargs: None if name == "disabled" else "false"
        page.locator.return_value = MagicMock(first=button)

        self.assertTrue(asyncio.run(_done_button_ready(page)))

    def test_done_button_ready_rejects_aria_disabled_button(self):
        page = MagicMock()
        button = AsyncMock()
        button.count.return_value = 1
        button.is_visible.return_value = True
        button.get_attribute.side_effect = lambda name, **_kwargs: None if name == "disabled" else "true"
        page.locator.return_value = MagicMock(first=button)

        self.assertFalse(asyncio.run(_done_button_ready(page)))

    def test_waits_for_slow_studio_channel_redirect(self):
        page = AsyncMock()
        urls = iter(
            [
                "https://studio.youtube.com/?approve_browser_access=true",
                "https://studio.youtube.com/?approve_browser_access=true",
                "https://studio.youtube.com/channel/channel-id",
            ]
        )
        type(page).url = property(lambda _self: next(urls))

        with patch("uploader.youtube_uploader.main._continue_to_studio", new=AsyncMock()):
            result = asyncio.run(_wait_for_studio_channel(page, max_checks=3))

        self.assertTrue(result)
        self.assertEqual(page.wait_for_timeout.await_count, 2)

    def test_stops_when_studio_redirects_to_sign_in(self):
        page = AsyncMock()
        type(page).url = property(lambda _self: "https://accounts.google.com/signin")

        self.assertFalse(asyncio.run(_wait_for_studio_channel(page, max_checks=3)))
        page.wait_for_timeout.assert_not_awaited()

    def test_detects_current_english_thumbnail_verification_prompt(self):
        self.assertTrue(
            is_thumbnail_verification_text(
                "Unlock more on YouTube\nTo add custom thumbnails, verify your phone number."
            )
        )

    def test_does_not_treat_normal_thumbnail_copy_as_verification(self):
        self.assertFalse(
            is_thumbnail_verification_text(
                "Set a thumbnail that stands out and draws viewers' attention."
            )
        )


if __name__ == "__main__":
    unittest.main()
