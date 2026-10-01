# Windows 설정 가이드

## 📋 필요한 것
- Python 3.9 이상
- weight-tracker 폴더의 모든 파일
- service-account.json (Google Sheets API 키)

## 🚀 설치 단계

### 1️⃣ Python 설치
- https://www.python.org/downloads/ 에서 최신 Python 설치
- **중요**: 설치 시 "Add Python to PATH" 반드시 체크 ✅

### 2️⃣ 패키지 설치
weight-tracker 폴더를 열어서 `cmd` 실행:

```bash
pip install -r requirements.txt
```

### 3️⃣ 필수 파일 확인
weight-tracker 폴더에 다음 파일들이 있는지 확인:
- ✅ bot_google_sheets.py
- ✅ service-account.json
- ✅ requirements.txt
- ✅ run_bot.bat
- ✅ .env

### 4️⃣ .env 파일 만들기

`notepad .env` 실행해서 다음 추가:

```
BOT_TOKEN=8752903714:AAFu23GDrz6S0CpQ0J2XYykXHVHFsckbWf4
```

### 5️⃣ 봇 실행

**방법 A: 배치 파일 클릭 (가장 간단)**
- `run_bot.bat` 더블클릭
- 실행 완료!

**방법 B: CMD에서 직접 실행**
```bash
python bot_google_sheets.py
```

## ✅ 테스트

Telegram에서 봇에 `/무게 70.5` 입력해보세요!

## 🔄 자동 시작 설정 (Optional)

Windows가 켜질 때 자동으로 봇이 실행되도록:

1. `Windows + R` → `taskschd.msc` 입력
2. "기본 작업 만들기"
3. 이름: `WeightTrackerBot`
4. 트리거: "컴퓨터 시작할 때"
5. 작업: `run_bot.bat` 실행

## 🆘 문제 해결

**"'python' is not recognized"**
→ Python이 PATH에 추가되지 않음. Python 재설치 시 "Add Python to PATH" 체크

**"ModuleNotFoundError"**
→ `pip install -r requirements.txt` 다시 실행

**"No such file or directory: 'service-account.json'"**
→ service-account.json이 같은 폴더에 있는지 확인

## 📞 지원
문제가 있으면 알려주세요!
