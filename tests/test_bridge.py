import json
import os
import socket
import threading
import unittest
from unittest.mock import patch

from agentic_blender.bridge import BridgeError, request


class BridgeTests(unittest.TestCase):
    def _serve(self, response):
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        captured = {}

        def worker():
            try:
                connection, _ = listener.accept()
                with connection:
                    with connection.makefile("rb") as reader:
                        captured.update(json.loads(reader.readline()))
                    connection.sendall(response)
            finally:
                listener.close()

        thread = threading.Thread(target=worker)
        thread.start()
        return port, captured, thread

    def test_success(self):
        port, captured, thread = self._serve(b'{"ok":true,"result":{"objects":[]}}\n')
        with patch.dict(os.environ, {"AGENTIC_BLENDER_TOKEN": "secret", "AGENTIC_BLENDER_PORT": str(port)}):
            result = request("scene_info")
        thread.join(timeout=5)
        self.assertEqual(result, {"objects": []})
        self.assertEqual(captured["token"], "secret")
        self.assertEqual(captured["operation"], "scene_info")

    def test_remote_host_rejected(self):
        with patch.dict(os.environ, {"AGENTIC_BLENDER_TOKEN": "secret", "AGENTIC_BLENDER_HOST": "0.0.0.0"}):
            with self.assertRaisesRegex(BridgeError, "loopback"):
                request("scene_info")

    def test_missing_token(self):
        with patch.dict(os.environ, {"AGENTIC_BLENDER_TOKEN": ""}):
            with self.assertRaisesRegex(BridgeError, "AGENTIC_BLENDER_TOKEN"):
                request("scene_info")

    def test_error_from_blender(self):
        port, _, thread = self._serve(b'{"ok":false,"error":"Object not found"}\n')
        with patch.dict(os.environ, {"AGENTIC_BLENDER_TOKEN": "secret", "AGENTIC_BLENDER_PORT": str(port)}):
            with self.assertRaisesRegex(BridgeError, "Object not found"):
                request("delete_object", {"name": "missing"})
        thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
