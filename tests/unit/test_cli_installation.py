"""跨目录运行与配置加载回归测试。"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(os.name != "nt", reason="Windows 启动器验证")
def test_project_launcher_from_other_directory(tmp_path: Path) -> None:
    """启动器自行定位仓库，转发参数并保留退出码。"""
    repo = Path(__file__).resolve().parents[2]
    launcher = repo / "scripts" / "wechat-cli.cmd"
    env = os.environ.copy()
    env["WECHAT_ASSISTANT_HOME"] = str(tmp_path / "错误目录")
    result = subprocess.run(
        [str(launcher), "doctor", "--json"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    assert json.loads(result.stdout)["details"]["home"] == str(repo)
    assert not (tmp_path / "错误目录").exists()
    result = subprocess.run(
        [str(launcher), "download", "--json"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "invalid_arguments"


def test_cli_uses_explicit_home_from_other_directory(tmp_path: Path) -> None:
    """相对 SQLite 和输出路径固定到应用目录，不读取调用方 .env。"""
    app_home = tmp_path / "应用数据"
    cwd = tmp_path / "另一个项目"
    app_home.mkdir()
    cwd.mkdir()
    (app_home / ".env").write_text(
        "DATABASE_URL=sqlite:///data/custom.db\nDOWNLOAD_DIR=articles\n", encoding="utf-8"
    )
    (cwd / ".env").write_text("DOWNLOAD_DIR=wrong\n", encoding="utf-8")
    env = os.environ.copy()
    for key in ("DATABASE_URL", "DOWNLOAD_DIR", "DOWNLOAD_PATH", "LOG_DIR", "SESSION_FILE"):
        env.pop(key, None)
    env["WECHAT_ASSISTANT_HOME"] = str(app_home)
    env["PYTHONUTF8"] = "1"
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2] / "src")
    result = subprocess.run(
        [sys.executable, "-m", "wechat_article_assistant.cli", "doctor", "--json"],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    details = json.loads(result.stdout)["details"]
    assert details["home"] == str(app_home)
    assert details["download_dir"] == str(app_home / "articles")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from wechat_article_assistant.config import config; print(config.DATABASE_URL)",
        ],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    assert str(app_home / "data" / "custom.db") in result.stdout
    assert not (cwd / "logs").exists()
