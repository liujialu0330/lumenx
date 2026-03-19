"""FFmpeg 自动下载安装工具 (Windows)"""
import os
import sys
import shutil
import zipfile
import tempfile
import urllib.request
import logging

logger = logging.getLogger(__name__)

FFMPEG_DOWNLOAD_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
INSTALL_DIR = os.path.join(os.path.expanduser("~"), ".lumen-x", "ffmpeg")

_install_status = {
    "status": "idle",
    "progress": 0,
    "message": "",
    "error": None,
}


def get_install_status() -> dict:
    return dict(_install_status)


def _reset_status():
    _install_status["status"] = "idle"
    _install_status["progress"] = 0
    _install_status["message"] = ""
    _install_status["error"] = None


def _update_status(status: str, progress: int = 0, message: str = "", error: str = None):
    _install_status["status"] = status
    _install_status["progress"] = progress
    _install_status["message"] = message
    _install_status["error"] = error


def install_ffmpeg():
    """下载并解压 FFmpeg 到 ~/.lumen-x/ffmpeg/bin/"""
    if sys.platform != "win32":
        _update_status("failed", error="仅支持 Windows 系统")
        return

    tmp_path = None
    try:
        _update_status("downloading", 0, "正在下载 FFmpeg...")

        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".zip")
        os.close(tmp_fd)

        def reporthook(block_num, block_size, total_size):
            if total_size > 0:
                downloaded = block_num * block_size
                percent = min(100, int(downloaded * 100 / total_size))
                _update_status("downloading", percent, f"正在下载... {percent}%")

        logger.info(f"开始下载 FFmpeg: {FFMPEG_DOWNLOAD_URL}")
        urllib.request.urlretrieve(FFMPEG_DOWNLOAD_URL, tmp_path, reporthook=reporthook)
        logger.info("FFmpeg 下载完成")

        _update_status("extracting", 100, "正在解压...")

        bin_dir = os.path.join(INSTALL_DIR, "bin")
        os.makedirs(bin_dir, exist_ok=True)

        with zipfile.ZipFile(tmp_path, "r") as zf:
            # gyan.dev zip 内部结构: ffmpeg-X.X.X-essentials_build/bin/ffmpeg.exe
            # 找到 bin/ 目录下的文件并提取
            bin_prefix = None
            for name in zf.namelist():
                # 匹配 .../bin/ffmpeg.exe 或 .../bin/ffprobe.exe
                parts = name.replace("\\", "/").split("/")
                if len(parts) >= 2 and parts[-2] == "bin" and parts[-1] in ("ffmpeg.exe", "ffprobe.exe"):
                    bin_prefix = "/".join(parts[:-1]) + "/"
                    break

            if not bin_prefix:
                _update_status("failed", error="zip 包中未找到 ffmpeg.exe")
                return

            extracted_count = 0
            for name in zf.namelist():
                normalized = name.replace("\\", "/")
                if normalized.startswith(bin_prefix) and not normalized.endswith("/"):
                    filename = normalized[len(bin_prefix):]
                    dest = os.path.join(bin_dir, filename)
                    with zf.open(name) as src, open(dest, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    extracted_count += 1

            logger.info(f"解压完成，提取了 {extracted_count} 个文件到 {bin_dir}")

        # 验证
        ffmpeg_exe = os.path.join(bin_dir, "ffmpeg.exe")
        if os.path.isfile(ffmpeg_exe):
            _update_status("completed", 100, "安装完成")
            logger.info(f"FFmpeg 安装成功: {ffmpeg_exe}")
        else:
            _update_status("failed", error="解压后未找到 ffmpeg.exe")

    except Exception as e:
        logger.error(f"FFmpeg 安装失败: {e}")
        _update_status("failed", error=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
