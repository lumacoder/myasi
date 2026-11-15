"""Windows junction code paths, exercised with mocks on any OS."""
import os
from unittest import mock

from helpers import ROOT, Base, myasi


class FakeRun:
    def __init__(self, rc):
        self.rc, self.calls = rc, []

    def __call__(self, cmd, **kw):
        self.calls.append(cmd)
        if self.rc == 0:  # emulate mklink /J with a symlink so the rest of the flow is real
            os.symlink(cmd[5], cmd[4], target_is_directory=True)
        return mock.Mock(returncode=self.rc, stdout="", stderr="")


class WindowsTest(Base):
    def test_junction_command(self):
        fake = FakeRun(0)
        with mock.patch.object(myasi, "IS_WIN", True), mock.patch.object(myasi.subprocess, "run", fake):
            self.run_cli("get", "hello-myasi", "--agent", "claude", "--source", str(ROOT))
        (cmd,) = fake.calls
        self.assertEqual(cmd[:4], ["cmd", "/c", "mklink", "/J"])
        self.assertEqual(cmd[4], str(self.claude_dir / "hello-myasi"))
        self.assertEqual(cmd[5], str((ROOT / "skills" / "hello-myasi").resolve()))
        self.assertEqual(self.state()["installs"]["hello-myasi"]["targets"][0]["mode"], "link")

    def test_junction_failure_falls_back_to_copy(self):
        fake = FakeRun(1)
        with mock.patch.object(myasi, "IS_WIN", True), mock.patch.object(myasi.subprocess, "run", fake):
            out, _ = self.run_cli("get", "hello-myasi", "--agent", "claude", "--source", str(ROOT))
        self.assertIn("falling back to copy", out)
        p = self.claude_dir / "hello-myasi"
        self.assertTrue(p.is_dir() and not p.is_symlink())
        self.assertEqual(self.state()["installs"]["hello-myasi"]["targets"][0]["mode"], "copy")

    def test_remove_junction_uses_rmdir_when_unlink_fails(self):
        self.run_cli("get", "hello-myasi", "--agent", "claude", "--source", str(ROOT))
        p = self.claude_dir / "hello-myasi"
        real_unlink = os.unlink
        calls = []

        def unlink(path):
            calls.append(path)
            raise PermissionError("junctions are directories on Windows")

        with mock.patch.object(myasi.os, "unlink", unlink), \
                mock.patch.object(myasi.os, "rmdir", lambda path: real_unlink(path)):
            self.run_cli("remove", "hello-myasi", "--source", str(ROOT))
        self.assertEqual(calls, [str(p)])
        self.assertFalse(os.path.lexists(str(p)))
        self.assertTrue((ROOT / "skills" / "hello-myasi" / "SKILL.md").exists())

    def test_is_link_reparse_point(self):
        d = self.tmp / "plain"
        d.mkdir()
        st = mock.Mock(st_file_attributes=0x400)
        with mock.patch.object(myasi, "IS_WIN", True), mock.patch.object(myasi.os, "lstat", return_value=st), \
                mock.patch.object(myasi.os.path, "isjunction", return_value=False, create=True):
            self.assertTrue(myasi.is_link(d))
        self.assertFalse(myasi.is_link(d))

    def test_symlink_failure_falls_back_on_posix(self):
        with mock.patch.object(myasi.os, "symlink", side_effect=OSError("no privilege")):
            self.run_cli("get", "hello-myasi", "--agent", "claude", "--source", str(ROOT))
        self.assertEqual(self.state()["installs"]["hello-myasi"]["targets"][0]["mode"], "copy")
