import unittest

from uploader.youtube_uploader.main import is_thumbnail_verification_text


class YouTubeUploaderTests(unittest.TestCase):
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
