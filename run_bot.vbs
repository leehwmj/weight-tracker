Set objShell = CreateObject("WScript.Shell")
objShell.Run "pythonw.exe -X utf8 bot_google_sheets.py >> bot.log 2>&1", 0, False
