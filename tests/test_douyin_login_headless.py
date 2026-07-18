import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from uploader.douyin_uploader import main as douyin


class DouyinLoginHeadlessTests(unittest.TestCase):
    def test_setup_passes_headless_to_cookie_check(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            account_file = Path(tmp_dir) / "account.json"
            account_file.write_text("{}", encoding="utf-8")
            with patch.object(douyin, "cookie_auth", new=AsyncMock(return_value=True)) as auth:
                result = asyncio.run(
                    douyin.douyin_setup(
                        str(account_file),
                        return_detail=True,
                        headless=True,
                    )
                )

        self.assertTrue(result["success"])
        auth.assert_awaited_once_with(str(account_file), headless=True)

    def test_cookie_generation_rechecks_with_requested_headless_mode(self):
        context = AsyncMock()
        context.storage_state = AsyncMock()
        page = AsyncMock()
        page.url = "https://creator.douyin.com/creator-micro/home"
        context.new_page = AsyncMock(return_value=page)
        browser = AsyncMock()
        browser.new_context = AsyncMock(return_value=context)
        playwright = AsyncMock()
        playwright.chromium.launch = AsyncMock(return_value=browser)
        manager = AsyncMock()
        manager.__aenter__.return_value = playwright
        manager.__aexit__.return_value = False

        with (
            patch.object(douyin, "async_playwright", return_value=manager),
            patch.object(douyin, "set_init_script", new=AsyncMock(return_value=context)),
            patch.object(douyin, "_save_douyin_qrcode", new=AsyncMock(return_value={})),
            patch.object(
                douyin,
                "_wait_for_douyin_login",
                new=AsyncMock(
                    return_value=douyin._build_login_result(
                        True,
                        "success",
                        "ok",
                        "account.json",
                        current_url=page.url,
                    )
                ),
            ),
            patch.object(douyin, "cookie_auth", new=AsyncMock(return_value=True)) as auth,
            patch.object(douyin.asyncio, "sleep", new=AsyncMock()),
        ):
            result = asyncio.run(douyin.douyin_cookie_gen("account.json", headless=True))

        self.assertTrue(result["success"])
        auth.assert_awaited_once_with("account.json", headless=True)


if __name__ == "__main__":
    unittest.main()
