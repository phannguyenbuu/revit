import json
import unittest
from unittest.mock import patch, mock_open

import prompt_normalizer as n


class NormalizerTests(unittest.TestCase):
    def command(self, text):
        return n.parse_prompt(text)["command"]

    def test_default_closed_and_explicit_caps(self):
        for text, caps in (("tạo cylinder fit z", False),
                           ("tạo cylinder fit z không nắp", "both"),
                           ("tạo cylinder fit z không nắp trên/dưới", "both"),
                           ("tạo cylinder fit z không nắp trên", "top"),
                           ("tạo cylinder fit z không nắp dưới", "bottom"),
                           ("tạo cylinder trên trục z không nắp", "both"),
                           ("tạo cylinder fit z không có nắp", "both"),
                           ("tao cylider fit x khong nap", "both")):
            self.assertEqual(self.command(text)["params"]["remove_caps"], caps)

    def test_shapes_flags_and_validation(self):
        c = self.command("vẽ nửa hình trụ trục y 64 cạnh giữ khối gốc")
        self.assertEqual(c["action"], "fit_half_cylinder")
        self.assertEqual(c["params"]["axis"], "Y")
        self.assertEqual(c["params"]["sides"], 64)
        self.assertFalse(c["params"]["delete_source"])
        self.assertEqual(self.command("box từ bbox")["action"], "box_from_bbox")
        self.assertEqual(self.command("bỏ nắp trên")["params"], {"caps": "top"})
        self.assertIn("error", n.parse_prompt("cylinder fit X Y"))
        self.assertIsNone(self.command("cylinder là gì"))
        self.assertIsNone(self.command("kiểm tra"))

    def test_model_cannot_invent_cap_removal_or_axis(self):
        result = n._command("tao cylinder fit z", "fit_cylinder", "X")
        self.assertEqual(result["command"]["params"]["axis"], "Z")
        self.assertFalse(result["command"]["params"]["remove_caps"])
        self.assertIsNone(n._command("tao cylinder fit z", "remove_caps", "Z")["command"])

    def test_short_box_commands(self):
        for text in ('tạo box', 'tao box', 'vẽ box', 'create box', 'tạo hộp', 'box từ bbox'):
            self.assertEqual(self.command(text)['action'], 'box_from_bbox')
            self.assertFalse(self.command(text)['params']['remove_caps'])
        self.assertIsNone(self.command('mở hộp thoại import'))
        self.assertIsNone(self.command('box là gì'))
        with patch.object(n, '_endpoint', side_effect=AssertionError('Should not call VPS')):
            self.assertEqual(n.normalize_prompt('tạo box')['command']['action'], 'box_from_bbox')

    def test_qwen_failure_uses_rules(self):
        with patch("builtins.open", mock_open(read_data='{"enabled":true}')), \
                patch.object(n, "_endpoint", side_effect=ConnectionError()):
            result = n.normalize_prompt("tao cylider fit z khong nap")
        self.assertEqual(result["source"], "rules")
        self.assertIn("warning", result)
        self.assertEqual(result["command"]["params"]["remove_caps"], "both")

    def test_local_endpoint_does_not_start_ssh(self):
        with patch.object(n, '_port_ready', side_effect=AssertionError('Should not start SSH')):
            self.assertEqual(n._endpoint({'base_url':'http://127.0.0.1:11434'}),
                             'http://127.0.0.1:11434/api/chat')
        with self.assertRaises(ValueError):
            n._endpoint({'base_url':'http://example.com:11434'})

    def test_valid_qwen_json_and_reject_generated_code(self):
        for answer, expected_source in (({"action": "fit_cylinder", "axis": "Z"}, "qwen"),
                                        ({"action": "execute", "axis": "Z", "code": "delete objects"}, "rules")):
            with patch("builtins.open", mock_open(read_data='{"enabled":true}')), \
                    patch.object(n, "_endpoint", return_value="http://127.0.0.1/api/chat"), \
                    patch.object(n.urllib.request, "urlopen") as response:
                response.return_value.__enter__.return_value.read.return_value = json.dumps(
                    {"message": {"content": json.dumps(answer)}}).encode()
                result = n.normalize_prompt("tao cylider fit z")
            self.assertEqual(result["source"], expected_source)
            self.assertEqual(result["command"]["action"], "fit_cylinder")


if __name__ == "__main__":
    unittest.main()
