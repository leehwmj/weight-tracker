#!/usr/bin/env python3
"""
체중 기록 텔레그램 봇 - Google Sheets 연동
"""

import os
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import nest_asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# asyncio 이벤트 루프 문제 해결
nest_asyncio.apply()

# 환경 변수 로드
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN이 설정되지 않았습니다!")

# Google Sheets 설정
SHEET_ID = "1bQM58722NaTO3nLoXZcBk7Jpx_LDFz3alJoeWfqa15I"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_FILE = 'service-account.json'

# 사용자 정보
USER_HEIGHT = 168  # cm

# Google Sheets 클라이언트 초기화
def init_sheet():
    credentials = Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key(SHEET_ID)
    return sheet.sheet1

# Google Sheets에 데이터 저장
def save_weight(weight, date_str=None):
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    try:
        sheet = init_sheet()

        # 기존 데이터 읽기
        rows = sheet.get_all_values()

        # 새 행 찾기 또는 기존 행 업데이트
        found = False
        for i, row in enumerate(rows[1:], start=2):  # 헤더 제외
            if row and row[0] == date_str:
                # 기존 행 업데이트
                sheet.update_cell(i, 2, weight)
                found = True
                break

        if not found:
            # 새 행 추가
            sheet.append_row([date_str, weight])

        return date_str
    except Exception as e:
        print(f"❌ Google Sheets 저장 오류: {e}")
        raise

# Google Sheets에서 모든 데이터 읽기
def get_all_data():
    try:
        sheet = init_sheet()
        rows = sheet.get_all_values()

        data = []
        for row in rows[1:]:  # 헤더 제외
            if row and len(row) >= 2:
                try:
                    data.append({
                        'date': row[0],
                        'weight': float(row[1])
                    })
                except ValueError:
                    pass

        return sorted(data, key=lambda x: x['date'])
    except Exception as e:
        print(f"❌ Google Sheets 읽기 오류: {e}")
        return []

# BMI 계산
def calculate_bmi(weight_kg):
    height_m = USER_HEIGHT / 100
    return weight_kg / (height_m ** 2)

# 그래프 생성
def create_graph():
    data = get_all_data()

    if not data:
        return None

    dates = [d['date'] for d in data]
    weights = [d['weight'] for d in data]

    # Y축 범위 동적 설정
    min_weight = min(weights)
    max_weight = max(weights)
    margin = max(1, (max_weight - min_weight) * 0.1)
    y_min = min_weight - margin
    y_max = max_weight + margin

    # 그래프 생성
    plt.figure(figsize=(10, 6))
    plt.plot(dates, weights, 'o-', linewidth=2, markersize=8, color='#FF6B9D')
    plt.fill_between(range(len(dates)), weights, alpha=0.3, color='#FF6B9D')

    plt.title('체중 변화', fontsize=16, fontweight='bold')
    plt.xlabel('날짜', fontsize=12)
    plt.ylabel('체중 (kg)', fontsize=12)
    plt.ylim(y_min, y_max)
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    graph_file = 'weight_graph.png'
    plt.savefig(graph_file, dpi=100, bbox_inches='tight')
    plt.close()

    return graph_file

# BMI 그래프 생성
def create_bmi_graph():
    data = get_all_data()

    if not data:
        return None

    dates = [d['date'] for d in data]
    weights = [d['weight'] for d in data]
    bmis = [calculate_bmi(w) for w in weights]

    # Y축 범위 동적 설정
    min_bmi = min(bmis)
    max_bmi = max(bmis)
    margin = max(0.5, (max_bmi - min_bmi) * 0.1)
    y_min = min_bmi - margin
    y_max = max_bmi + margin

    # 그래프 생성
    plt.figure(figsize=(10, 6))
    plt.plot(dates, bmis, 'o-', linewidth=2, markersize=8, color='#4ECDC4')
    plt.fill_between(range(len(dates)), bmis, alpha=0.3, color='#4ECDC4')

    plt.title('BMI 변화', fontsize=16, fontweight='bold')
    plt.xlabel('날짜', fontsize=12)
    plt.ylabel('BMI', fontsize=12)
    plt.ylim(y_min, y_max)
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    graph_file = 'bmi_graph.png'
    plt.savefig(graph_file, dpi=100, bbox_inches='tight')
    plt.close()

    return graph_file

# Telegram 명령어 핸들러
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏋️ 체중 기록 봇에 오신 걸 환영합니다!\n\n"
        "📝 사용법 (영어 또는 한글 모두 가능):\n"
        "/weight 70.5 (또는 /무게 70.5) - 체중 입력\n"
        "/graph (또는 /그래프) - 체중 그래프\n"
        "/bmi (또는 /비엠아이) - BMI 그래프\n"
        "/stats (또는 /통계) - 통계\n"
        "/help (또는 /도움말) - 도움말\n\n"
        "☁️ 데이터는 Google Sheets에 저장됩니다!"
    )

async def handle_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text(
                "❌ 사용법:\n"
                "/weight 70.5 - 오늘 날짜로 입력\n"
                "/weight 2024-01-15 70.5 - 지정 날짜로 입력\n"
                "/weight 01-15 70.5 - 올해의 지정 날짜로 입력"
            )
            return

        date_str = None
        weight = None

        if len(context.args) == 1:
            weight = float(context.args[0])
            date_str = datetime.now().strftime("%Y-%m-%d")

        elif len(context.args) == 2:
            date_input = context.args[0]
            weight = float(context.args[1])

            if len(date_input) == 10 and date_input[4] == '-' and date_input[7] == '-':
                date_str = date_input
            elif len(date_input) == 5 and date_input[2] == '-':
                current_year = datetime.now().year
                date_str = f"{current_year}-{date_input}"
            else:
                await update.message.reply_text(
                    "❌ 날짜 형식이 잘못되었습니다.\n"
                    "올바른 형식:\n"
                    "- 2024-01-15 (YYYY-MM-DD)\n"
                    "- 01-15 (MM-DD, 올해)"
                )
                return

            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                await update.message.reply_text("❌ 유효하지 않은 날짜입니다.")
                return

        else:
            await update.message.reply_text(
                "❌ 사용법: /weight [날짜(선택)] 체중\n"
                "예: /weight 70.5\n"
                "예: /weight 2024-01-15 70.5"
            )
            return

        # Google Sheets에 저장
        save_weight(weight, date_str)

        await update.message.reply_text(
            f"✅ Google Sheets에 저장되었습니다!\n"
            f"📅 {date_str}\n"
            f"⚖️ {weight}kg"
        )

    except ValueError as e:
        await update.message.reply_text(
            f"❌ 오류: {str(e)}\n"
            "체중은 숫자여야 합니다. (예: 70.5)"
        )

async def handle_graph(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 그래프를 생성 중입니다...")

    graph_file = create_graph()

    if not graph_file:
        await update.message.reply_text("❌ 아직 기록된 데이터가 없습니다.")
        return

    with open(graph_file, 'rb') as f:
        await update.message.reply_photo(photo=f, caption="📈 체중 변화")

async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_all_data()

    if not data:
        await update.message.reply_text("❌ 아직 기록된 데이터가 없습니다.")
        return

    weights = [d['weight'] for d in data]
    bmis = [calculate_bmi(w) for w in weights]

    stats_text = (
        f"📊 체중 통계\n"
        f"━━━━━━━━━━━━\n"
        f"현재: {weights[-1]:.1f}kg\n"
        f"평균: {sum(weights)/len(weights):.1f}kg\n"
        f"최고: {max(weights):.1f}kg\n"
        f"최저: {min(weights):.1f}kg\n"
        f"변화: {weights[-1] - weights[0]:+.1f}kg\n"
        f"기록: {len(weights)}일\n\n"
        f"📈 BMI 통계 (키: {USER_HEIGHT}cm)\n"
        f"━━━━━━━━━━━━\n"
        f"현재: {bmis[-1]:.1f}\n"
        f"평균: {sum(bmis)/len(bmis):.1f}\n"
        f"최고: {max(bmis):.1f}\n"
        f"최저: {min(bmis):.1f}\n"
        f"변화: {bmis[-1] - bmis[0]:+.1f}"
    )

    await update.message.reply_text(stats_text)

async def handle_bmi_graph(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 BMI 그래프를 생성 중입니다...")

    graph_file = create_bmi_graph()

    if not graph_file:
        await update.message.reply_text("❌ 아직 기록된 데이터가 없습니다.")
        return

    with open(graph_file, 'rb') as f:
        await update.message.reply_photo(photo=f, caption="📈 BMI 변화")

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💡 도움말\n\n"
        "📝 체중 입력:\n"
        "/weight 70.5 (또는 /무게 70.5)\n"
        "/weight 2024-01-15 70.5\n"
        "/weight 01-15 70.5\n\n"
        "📈 체중 그래프:\n"
        "/graph (또는 /그래프)\n\n"
        "📊 BMI 그래프:\n"
        "/bmi (또는 /비엠아이)\n\n"
        "📋 통계 조회:\n"
        "/stats (또는 /통계)\n\n"
        "ℹ️ 도움말:\n"
        "/help (또는 /도움말)\n\n"
        "☁️ 모든 데이터는 Google Sheets에 자동 저장됩니다!"
    )

# 한글 메시지 핸들러
async def handle_korean_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == '/무게':
        await update.message.reply_text(
            "❌ 사용법:\n"
            "/무게 70.5 - 오늘 날짜로 입력\n"
            "/무게 2024-01-15 70.5 - 지정 날짜로 입력"
        )
    elif text.startswith('/무게 '):
        args = text[4:].split()
        context.args = args
        await handle_weight(update, context)

    elif text == '/그래프':
        await handle_graph(update, context)

    elif text == '/bmi' or text == '/비엠아이':
        await handle_bmi_graph(update, context)

    elif text == '/통계':
        await handle_stats(update, context)

    elif text == '/도움말':
        await handle_help(update, context)

# 봇 시작
async def main():
    log_msg = f"[{datetime.now()}] 🤖 체중 기록 봇 시작 (Google Sheets 연동)...\n"
    with open('bot.log', 'a', encoding='utf-8') as f:
        f.write(log_msg)
    print("🤖 체중 기록 봇 시작 (Google Sheets 연동)...")
    print("📊 Sheet ID:", SHEET_ID)

    application = Application.builder().token(BOT_TOKEN).build()

    # 명령어 핸들러
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("weight", handle_weight))
    application.add_handler(CommandHandler("graph", handle_graph))
    application.add_handler(CommandHandler("bmi", handle_bmi_graph))
    application.add_handler(CommandHandler("stats", handle_stats))
    application.add_handler(CommandHandler("help", handle_help))

    # 한글 메시지 핸들러
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_korean_text))

    # 봇 시작
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    try:
        asyncio.run(main())
    except Exception as e:
        with open('bot.log', 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.now()}] ❌ 에러: {str(e)}\n")
        raise
