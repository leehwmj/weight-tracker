import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, render_template, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import plotly.graph_objects as go
from dotenv import load_dotenv
import threading

# 환경 변수 로드
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE = 'weight_data.db'

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN 환경 변수가 설정되지 않았습니다!")

app = Flask(__name__)
application = None

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS weights
                 (id INTEGER PRIMARY KEY,
                  date TEXT UNIQUE,
                  weight REAL,
                  timestamp TEXT)''')
    conn.commit()
    conn.close()

# 체중 저장
def save_weight(date_str, weight):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    try:
        c.execute("INSERT OR REPLACE INTO weights (date, weight, timestamp) VALUES (?, ?, ?)",
                 (date_str, weight, datetime.now().isoformat()))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving weight: {e}")
        return False
    finally:
        conn.close()

# 모든 체중 데이터 조회
def get_all_weights():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT date, weight FROM weights ORDER BY date")
    data = c.fetchall()
    conn.close()
    return data

# Telegram 명령어 핸들러
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "안녕하세요! 체중 기록 봇입니다.\n\n"
        "사용법:\n"
        "/weight 70.5 - 체중 입력 (예: /weight 70.5)\n"
        "/stats - 통계 보기\n"
        "/link - 대시보드 링크"
    )

async def handle_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("사용법: /weight 70.5")
            return

        weight = float(context.args[0])
        date_str = datetime.now().strftime("%Y-%m-%d")

        if save_weight(date_str, weight):
            await update.message.reply_text(f"✅ {date_str} 체중: {weight}kg 저장되었습니다!")
        else:
            await update.message.reply_text("❌ 저장 실패")
    except ValueError:
        await update.message.reply_text("❌ 숫자를 입력해주세요 (예: /weight 70.5)")

async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_all_weights()

    if not data:
        await update.message.reply_text("아직 기록된 데이터가 없습니다.")
        return

    weights = [w[1] for w in data]

    stats = f"""
📊 체중 통계
━━━━━━━━━━━━
현재 체중: {weights[-1]:.1f}kg
평균: {sum(weights)/len(weights):.1f}kg
최고: {max(weights):.1f}kg
최저: {min(weights):.1f}kg
기록 수: {len(weights)}일
변화: {weights[-1] - weights[0]:+.1f}kg
    """

    await update.message.reply_text(stats)

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = os.getenv('DASHBOARD_URL', 'https://your-domain.com/dashboard')
    await update.message.reply_text(f"대시보드: {link}")

# Flask 웹 서버
@app.route('/')
def index():
    return "Weight Tracker Bot is running!"

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/data')
def get_data():
    data = get_all_weights()
    return jsonify({
        'dates': [d[0] for d in data],
        'weights': [d[1] for d in data]
    })

@app.route('/api/graph')
def get_graph():
    data = get_all_weights()

    if not data:
        return jsonify({'error': 'No data'}), 404

    dates = [d[0] for d in data]
    weights = [d[1] for d in data]

    fig = go.Figure(data=go.Scatter(
        x=dates,
        y=weights,
        mode='lines+markers',
        name='체중',
        line=dict(color='#FF6B9D', width=3),
        marker=dict(size=8)
    ))

    fig.update_layout(
        title='체중 변화',
        xaxis_title='날짜',
        yaxis_title='체중 (kg)',
        template='plotly_white',
        hovermode='x unified',
        height=500
    )

    return jsonify({'html': fig.to_html(include_plotlyjs='cdn')})

# 봇 초기화
def init_bot():
    global application
    init_db()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("weight", handle_weight))
    application.add_handler(CommandHandler("stats", handle_stats))
    application.add_handler(CommandHandler("link", handle_link))
    return application

# 봇 시작
def start_bot():
    global application
    application = init_bot()
    application.run_polling()

if __name__ == '__main__':
    # Flask를 별도 스레드에서 실행
    def run_flask():
        port = int(os.getenv('PORT', 5000))
        print(f"Flask 서버 시작: http://localhost:{port}")
        app.run(host='0.0.0.0', port=port, debug=False)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Telegram 봇 시작
    print("Telegram 봇 시작...")
    start_bot()
