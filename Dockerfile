# Pythonイメージを指定
FROM python:3.10-slim

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係をコピーしてインストール
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# ポートを指定
EXPOSE 8080

# Flaskアプリを起動
CMD ["python", "main.py"]
