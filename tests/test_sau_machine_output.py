import contextlib
import io
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import AsyncMock, patch

import sau_cli


class MachineOutputTests(unittest.TestCase):
    def test_machine_result_includes_remote_work_id(self):
        payload = sau_cli.build_machine_result(
            Namespace(
                platform="youtube",
                action="upload-video",
                account="wuya-youtube",
                file=None,
                schedule=None,
                remote_work_id="https://youtu.be/example",
            ),
            0,
        )

        self.assertEqual(payload["remote_work_id"], "https://youtu.be/example")

    def test_json_output_is_one_clean_document(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            result_file = Path(tmp_dir) / "result.json"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch("sau_cli.dispatch", new=AsyncMock(return_value=0)):
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    exit_code = sau_cli.main(
                        [
                            "douyin",
                            "check",
                            "--account",
                            "wuya",
                            "--json",
                            "--result-file",
                            str(result_file),
                        ]
                    )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["schema_version"], 1)
            self.assertTrue(payload["success"])
            self.assertEqual(payload["platform"], "douyin")
            self.assertEqual(payload["account"], "wuya")
            self.assertEqual(json.loads(result_file.read_text(encoding="utf-8")), payload)

    def test_failure_is_written_to_result_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            result_file = Path(tmp_dir) / "nested" / "result.json"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch("sau_cli.dispatch", new=AsyncMock(side_effect=RuntimeError("upload failed"))):
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    exit_code = sau_cli.main(
                        [
                            "tencent",
                            "check",
                            "--account",
                            "xiangsheng",
                            "--json",
                            "--result-file",
                            str(result_file),
                        ]
                    )

            self.assertEqual(exit_code, 1)
            payload = json.loads(stdout.getvalue())
            self.assertFalse(payload["success"])
            self.assertEqual(payload["error"], "upload failed")
            self.assertIn("upload failed", stderr.getvalue())
            self.assertEqual(json.loads(result_file.read_text(encoding="utf-8")), payload)


if __name__ == "__main__":
    unittest.main()
