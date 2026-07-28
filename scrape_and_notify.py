name: Monitor ADC Software Downloads Page

on:
  schedule:
    # 毎日 JST 9:00 に実行 (UTC 0:00 = JST 9:00)
    - cron: "0 0 * * *"
  workflow_dispatch: {}
    # ↑ GitHubの「Actions」タブから手動実行するためのトリガー

permissions:
  contents: write
  # previous_content.txt をリポジトリにコミットし直すために必要

jobs:
  check-update:
    runs-on: ubuntu-latest
    steps:
      - name: リポジトリをチェックアウト
        uses: actions/checkout@v4

      - name: Python セットアップ
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: 依存パッケージインストール
        run: |
          pip install -r requirements.txt
          playwright install --with-deps chromium

      - name: 更新チェック & 通知
        env:
          GMAIL_ADDRESS: ${{ secrets.GMAIL_ADDRESS }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
          NOTIFY_EMAIL: ${{ secrets.NOTIFY_EMAIL }}
        run: python scrape_and_notify.py

      - name: 取得内容をコミット(次回比較用)
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "Update snapshot [skip ci]"
          file_pattern: previous_content.txt
