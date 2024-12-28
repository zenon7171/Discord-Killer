import discord
from discord.ext import commands
from collections import defaultdict
import asyncio
from flask import Flask
from threading import Thread

# Botのトークンを設定
# Botのトークンを環境変数から取得
TOKEN = os.getenv("TOKEN")

# Intentsを設定
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True

# Botの接頭辞を設定
bot = commands.Bot(command_prefix='!', intents=intents)

# メッセージ履歴を保存する辞書
message_history = defaultdict(list)
processing_users = set()  # 処理中のユーザーを追跡

# スパム判定基準
SPAM_THRESHOLD = 10  # 5秒間でのメッセージ数
TIME_WINDOW = 5      # 秒
REPEATED_MESSAGE_THRESHOLD = 5  # 同一メッセージの繰り返し回数

# ログを送るチャンネル名
LOG_CHANNEL_NAME = "bot-logs"

# Flaskを使ったセッション維持用のWebサーバー
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

@bot.event
async def on_ready():
    print(f'Botがログインしました: {bot.user}')

async def send_log_message(guild, message):
    log_channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
    if log_channel:
        await log_channel.send(message)

@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Botのメッセージは無視

    # メッセージ履歴を記録
    user_id = message.author.id
    now = message.created_at.timestamp()
    message_history[user_id].append((now, message))

    # 古いメッセージを削除
    message_history[user_id] = [
        (timestamp, msg) for timestamp, msg in message_history[user_id]
        if now - timestamp <= TIME_WINDOW
    ]

    # スパムチェック: 短時間での大量メッセージ
    if len(message_history[user_id]) > SPAM_THRESHOLD or check_repeated_messages(user_id):
        if user_id not in processing_users:
            processing_users.add(user_id)
            await handle_spam(message, user_id)
        return  # 処理終了

    await bot.process_commands(message)

def check_repeated_messages(user_id):
    """同一内容のメッセージ繰り返しをチェック"""
    recent_messages = [msg.content for _, msg in message_history[user_id]]
    repeated_count = max(recent_messages.count(msg) for msg in set(recent_messages))
    return repeated_count >= REPEATED_MESSAGE_THRESHOLD

async def handle_spam(message, user_id):
    """スパム処理を共通化"""
    try:
        await message.channel.send(f"🚨{message.author.mention} 駆除対象発見しました。")
        username = message.author.name

        # スパムメッセージを即時削除
        delete_tasks = [msg.delete() for _, msg in message_history[user_id]]
        delete_results = await asyncio.gather(*delete_tasks, return_exceptions=True)
        for result in delete_results:
            if isinstance(result, Exception):
                print(f"メッセージ削除エラー: {result}")

        # ユーザーをキック
        await message.author.kick(reason="スパム行為")

        # 駆除完了後のメッセージを削除
        remaining_messages = [msg for _, msg in message_history[user_id]]
        delete_remaining_tasks = [msg.delete() for msg in remaining_messages]
        remaining_delete_results = await asyncio.gather(*delete_remaining_tasks, return_exceptions=True)
        for result in remaining_delete_results:
            if isinstance(result, Exception):
                print(f"メッセージ削除エラー (駆除後): {result}")

        # ログチャンネルに記録
        await send_log_message(
            message.guild,
            f"🚨 ユーザー {username} がスパム行為のため退出させられました。"
        )
        await message.channel.send(f"ユーザー **{username}** 駆除完了です🫶")
        del message_history[user_id]  # 履歴を削除
    except discord.Forbidden:
        await message.channel.send(f"{message.author.mention} をキックできません。Botの権限を確認してください。")
    except Exception as e:
        print(f"エラー: {e}")
    finally:
        # 処理完了後にユーザーを解除
        processing_users.discard(user_id)

# Webサーバーを開始してセッションを維持
keep_alive()

# Botを起動
bot.run(TOKEN)
