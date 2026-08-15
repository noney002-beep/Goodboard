@echo off
rem กรอก URL Apps Script web app ที่ได้รับหลังจาก deploy
rem ตัวอย่าง: https://script.google.com/macros/s/XXXX/exec
rem (ไม่ใช่ URL ของ Google Sheet edit)
set APPS_SCRIPT_URL=https://script.google.com/macros/s/AKfycbxLMb5i44x4Wzwr4HFA6AraPE5jdze67BwF_iSbrHiIAoYwz1Qqt9jNdh6vSOptzptqcQ/exec
set PORT=8001
python "%~dp0app.py"