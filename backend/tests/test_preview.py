import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
from app.core.preview import PreviewService


class TestPreviewService:
    def test_build_command(self):
        svc = PreviewService(we_path="/steam/wallpaper_engine", we_exe="wallpaper32.exe")
        cmd = svc._build_command("/projects/1/project.json")
        assert "wallpaper32.exe" in cmd[0] or "wallpaper32.exe" in str(cmd)
        assert "openWallpaper" in cmd

    def test_we_not_installed(self):
        svc = PreviewService(we_path="/nonexistent/path")
        assert svc.is_available() is False

    def test_we_installed(self, tmp_path):
        exe = tmp_path / "wallpaper32.exe"
        exe.write_bytes(b"fake")
        svc = PreviewService(we_path=str(tmp_path))
        assert svc.is_available() is True

    @patch("app.core.preview.subprocess")
    def test_capture_preview(self, mock_subprocess, tmp_path):
        exe = tmp_path / "wallpaper32.exe"
        exe.write_bytes(b"fake")
        mock_subprocess.run.return_value = MagicMock(returncode=0)

        svc = PreviewService(we_path=str(tmp_path), screenshot_dir=str(tmp_path / "screenshots"))

        screenshot_path = tmp_path / "screenshots" / "1_preview.png"
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        screenshot_path.write_bytes(b"\x89PNG" + b"\x00" * 10)

        with patch.object(svc, "_capture_screenshot", return_value=str(screenshot_path)):
            result = svc.preview(project_path=str(tmp_path / "project.json"), project_id="1")
            assert result is not None
            assert "1_preview.png" in result

    def test_preview_unavailable_returns_none(self):
        svc = PreviewService(we_path="/nonexistent")
        result = svc.preview(project_path="/some/project.json", project_id="1")
        assert result is None

    def test_from_config(self):
        from app.config import AppConfig
        cfg = AppConfig()
        svc = PreviewService.from_config(cfg)
        assert svc.we_exe == cfg.wallpaper_engine.exe
