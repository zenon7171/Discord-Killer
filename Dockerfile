# Pythonベースの公式イメージを使用
FROM python:3.10-slim

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係ファイルをコピー
COPY requirements.txt requirements.txt

# 必要なライブラリをインストール
RUN pip install --no-cache-dir -r requirements.txt

# プロジェクトファイルをコピー
COPY . .

# 必要なポートを公開
EXPOSE 8080

# アプリケーションを実行
CMD ["python", "killer_bot.py"]
