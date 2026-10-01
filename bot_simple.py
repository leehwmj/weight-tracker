#!/usr/bin/env python3
"""
간단한 체중 기록 텔레그램 봇
로컬 컴퓨터에서 실행
"""

import os
import csv
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
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

# 데이터 파일
DATA_FILE = 'weight_data.csv'

# 한글 폰트 설정
plt.rcParams['font.sans-serif'] = ['Helvetica', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

# CSV 초기화
def init_csv():
    if not Path(DATA_FILE).exists():
        with open(DATA_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['날짜', '체중(kg)'])

# 체중 데이터 저장
def save_weight(weight, date_str=None):
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # 기존 데이터 읽기
    data = {}
    if Path(DATA_FILE).exists():
        with open(DATA_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['날짜']:
                    data[row['날짜']] = row['체중(kg)']

    # 새 데이터 추가/갱신
    data[date_str] = str(weight)

    # 저장
    with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['날짜', '체중(kg)'])
        writer.writeheader()
        for date, weight_val in sorted(data.items()):
            writer.writerow({'날짜': date, '체중(kg)': weight_val})

    return date_str

# 모든 데이터 읽기
def get_all_data():
    data = []
    if Path(DATA_FILE).exists():
        with open(DATA_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['날짜']:
                    try:
                        data.append({
                            'date': row['날짜'],
                            'weight': float(row['체중(kg)'])
                        })
                    except ValueError:
                        pass
    return sorted(data, key=lambda x: x['date'])

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

    # 범위에 마진 추가 (상하 1kg씩)
    margin = max(1, (max_weight - min_weight) * 0.1)  # 최소 1kg, 또는 범위의 10%
    y_min = min_weight - margin
    y_max = max_weight + margin

    # 그래프 생성
    plt.figure(figsize=(10, 6))
    plt.plot(dates, weights, 'o-', linewidth=2, markersize=8, color='#FF6B9D')
    plt.fill_between(range(len(dates)), weights, alpha=0.3, color='#FF6B9D')

    plt.title('체중 변화', fontsize=16, fontweight='bold')
    plt.xlabel('날짜', fontsize=12)
    plt.ylabel('체중 (kg)', fontsize=12)
    plt.ylim(y_min, y_max)  # Y축 범위 동적 설정
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    # 이미지 저장
    graph_file = 'weight_graph.png'
    plt.savefig(graph_file, dpi=100, bbox_inches='tight')
    plt.close()

    return graph_file

# Telegram 명령어 핸들러
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏋️ 체중 기록 봇에 오신 걸 환영합니다!\n\n"
        "📝 사용법 (영어 또는 한글 모두 가능):\n"
        "/weight 70.5 (또는 /무게 70.5) - 체중 입력\n"
        "/graph (또는 /그래프) - 그래프 보기\n"
        "/stats (또는 /통계) - 통계\n"
        "/help (또는 /도움말) - 도움말"
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

        # 날짜와 체중 파싱
        date_str = None
        weight = None

        if len(context.args) == 1:
            # /weight 70.5 형식
            weight = float(context.args[0])
            date_str = datetime.now().strftime("%Y-%m-%d")

        elif len(context.args) == 2:
            # /weight [날짜] [체중] 형식
            date_input = context.args[0]
            weight = float(context.args[1])

            # 날짜 포맷 확인
            if len(date_input) == 10 and date_input[4] == '-' and date_input[7] == '-':
                # YYYY-MM-DD 형식
                date_str = date_input
            elif len(date_input) == 5 and date_input[2] == '-':
                # MM-DD 형식 → YYYY-MM-DD로 변환
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

            # 날짜 유효성 확인
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

        # 저장
        save_weight(weight, date_str)

        await update.message.reply_text(
            f"✅ 저장 완료!\n"
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

    # 그래프 이미지 전송
    with open(graph_file, 'rb') as f:
        await update.message.reply_photo(photo=f, caption="📈 체중 변화")

async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_all_data()

    if not data:
        await update.message.reply_text("❌ 아직 기록된 데이터가 없습니다.")
        return

    weights = [d['weight'] for d in data]

    stats_text = (
        f"📊 체중 통계\n"
        f"━━━━━━━━━━━━\n"
        f"현재: {weights[-1]:.1f}kg\n"
        f"평균: {sum(weights)/len(weights):.1f}kg\n"
        f"최고: {max(weights):.1f}kg\n"
        f"최저: {min(weights):.1f}kg\n"
        f"변화: {weights[-1] - weights[0]:+.1f}kg\n"
        f"기록: {len(weights)}일"
    )

    await update.message.reply_text(stats_text)

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💡 도움말\n\n"
        "📝 체중 입력:\n"
        "/weight 70.5 (또는 /무게 70.5)\n"
        "/weight 2024-01-15 70.5\n"
        "/weight 01-15 70.5\n\n"
        "📈 그래프 보기:\n"
        "/graph (또는 /그래프)\n\n"
        "📊 통계 조회:\n"
        "/stats (또는 /통계)\n\n"
        "ℹ️ 도움말:\n"
        "/help (또는 /도움말)\n\n"
        "💾 모든 데이터는 weight_data.csv에 저장됩니다."
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
        # 한글 무게 명령 처리
        args = text[4:].split()
        context.args = args
        await handle_weight(update, context)

    elif text == '/그래프':
        await handle_graph(update, context)

    elif text == '/통계':
        await handle_stats(update, context)

    elif text == '/도움말':
        await handle_help(update, context)

# 봇 시작
async def main():
    init_csv()

    print("🤖 체중 기록 봇 시작...")
    print(f"📝 데이터 파일: {DATA_FILE}")

    application = Application.builder().token(BOT_TOKEN).build()

    # 명령어 핸들러 등록 (영어만 공식 지원)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("weight", handle_weight))
    application.add_handler(CommandHandler("graph", handle_graph))
    application.add_handler(CommandHandler("stats", handle_stats))
    application.add_handler(CommandHandler("help", handle_help))

    # 한글 메시지 핸들러 (한글 명령어 처리)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_korean_text))

    # 봇 시작
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "This event loop is already running" in str(e):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
        else:
            raise
