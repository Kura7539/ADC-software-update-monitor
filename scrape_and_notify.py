"""
AutomationDirect Software & Firmware Downloads ページの更新監視スクリプト
"""

import difflib
import os
import smtplib
import sys
from email.mime.text import MIMEText
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://www.automationdirect.com/support/software-downloads"
SNAPSHOT_FILE = Path(__file__).parent / "previous_content.txt"
TARGET_SELECTOR = "body"


def fetch_rendered_text() -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(3000)
        content = page.locator(TARGET_SELECTOR).inner_text()
        browser.close()
    return normalize(content)


def normalize(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def load_previous() -> str:
    if SNAPSHOT_FILE.exists():
        return SNAPSHOT_FILE.read_text(encoding="utf-8")
    return ""


def save_current(text: str) -> None:
    SNAPSHOT_FILE.write_text(text, encoding="utf-8")


def build_diff(old: str, new: str) -> str:
    diff = difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        fromfile="前回の内容",
        tofile="今回の内容",
        lineterm="",
    )
    return "\n".join(diff)


def send_email(diff_text: str) -> None:
    gmail_address = os.environ["GMAIL_ADDRESS"]
    gmail_app_password = os.environ["GMAIL_APP_PASSWORD"]
    notify_email = os.environ["NOTIFY_EMAIL"]

    subject = "【更新通知】AutomationDirect Software & Firmware Downloads"
    body = (
        "AutomationDirectのSoftware & Firmware Downloadsページに"
        "更新が検出されました。\n\n"
        f"ページURL: {URL}\n\n"
        "----- 変更差分 -----\n"
        f"{diff_text}\n"
        "--------------------\n"
    )

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = gmail_address
    msg["To"] = notify_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, gmail_app_password)
        server.sendmail(gmail_address, [notify_email], msg.as_string())


def main() -> int:
    current = fetch_rendered_text()
    previous = load_previous()

    if not previous:
        print("初回実行のため、今回の内容を保存して終了します。")
        save_current(current)
        return 0

    if current == previous:
        print("変更はありませんでした。")
        return 0

    print("変更を検出しました。メールを送信します。")
    diff_text = build_diff(previous, current)
    send_email(diff_text)
    save_current(current)
    return 0


if __name__ == "__main__":
    sys.exit(main())
