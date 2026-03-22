import subprocess
import time
import logging
from pathlib import Path
from app.config import AppConfig

logger = logging.getLogger(__name__)


class PreviewService:
    def __init__(self, we_path: str = "", we_exe: str = "wallpaper32.exe",
                 screenshot_dir: str = "./data/screenshots", timeout: int = 10):
        self.we_path = Path(we_path)
        self.we_exe = we_exe
        self.screenshot_dir = Path(screenshot_dir)
        self.timeout = timeout

    @classmethod
    def from_config(cls, cfg: AppConfig) -> "PreviewService":
        return cls(
            we_path=cfg.wallpaper_engine.path,
            we_exe=cfg.wallpaper_engine.exe,
            timeout=cfg.storage.preview_timeout_seconds,
        )

    def is_available(self) -> bool:
        exe_path = self.we_path / self.we_exe
        return exe_path.exists()

    def _build_command(self, project_json_path: str) -> list[str]:
        exe_path = str(self.we_path / self.we_exe)
        return [
            exe_path, "-control",
            "openWallpaper",
            "-file", project_json_path,
            "-playback", "play",
        ]

    def preview(self, project_path: str, project_id: str) -> str | None:
        if not self.is_available():
            logger.warning("Wallpaper Engine not available at %s", self.we_path)
            return None

        cmd = self._build_command(project_path)
        try:
            subprocess.run(cmd, timeout=self.timeout, check=False)
            time.sleep(3)
            return self._capture_screenshot(project_id)
        except subprocess.TimeoutExpired:
            logger.warning("Preview timed out for project %s", project_id)
            return None
        except Exception as e:
            logger.error("Preview failed: %s", e)
            return None

    def _capture_screenshot(self, project_id: str) -> str:
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = self.screenshot_dir / f"{project_id}_preview.png"
        try:
            import mss
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                img = sct.grab(monitor)
                from PIL import Image
                pil_img = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
                pil_img.save(str(screenshot_path))
        except ImportError:
            logger.warning("mss not installed, cannot capture screenshot")
            return ""
        return str(screenshot_path)
