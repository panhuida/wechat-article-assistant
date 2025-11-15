@echo off
REM 微信公众号文章助手 - 命令行工具 (Windows批处理文件)
REM 使用方法:
REM   wechat-cli download <article_url>
REM   wechat-cli download --file <file_path>
REM   wechat-cli download <article_url> --output <output_dir>

python "%~dp0wechat-cli.py" %*
