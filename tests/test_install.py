"""scripts/install.sh against a local HTTP server (MYASI_RAW_URL), then the README quickstart flow."""
import functools
import http.server
import os
import shutil
import subprocess
import threading
import unittest

from helpers import HAS_GIT, ROOT, Base


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


@unittest.skipUnless(shutil.which("sh") and shutil.which("curl") and os.name != "nt", "needs sh + curl")
class InstallShTest(Base):
    def setUp(self):
        super().setUp()
        handler = functools.partial(QuietHandler, directory=str(ROOT))
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)

    def sh(self, cmd, **env):
        e = dict(os.environ, **env)
        return subprocess.run(["sh", "-c", cmd], env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              universal_newlines=True)

    def test_install_and_quickstart(self):
        url = "http://127.0.0.1:%d" % self.httpd.server_address[1]
        r = self.sh("curl -fsSL %s/scripts/install.sh | sh" % url, MYASI_RAW_URL=url)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("myasi 0.", r.stdout)
        b = self.home / ".myasi" / "bin"
        self.assertEqual(sorted(os.listdir(str(b))), ["myasi", "myasi.py"])  # no clone
        if not HAS_GIT:
            return
        tree = self.make_tree()
        _, src = self.make_bare(tree)
        r = self.sh('export PATH="$HOME/.myasi/bin:$PATH"; myasi get hello-myasi && myasi list --installed'
                    ' && myasi remove hello-myasi', MYASI_SOURCE=src)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("hello-myasi", r.stdout)
        self.assertFalse(os.path.lexists(str(self.agents_dir / "hello-myasi")))
