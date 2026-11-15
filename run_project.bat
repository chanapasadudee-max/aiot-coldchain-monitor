@echo off
chcp 65001 > nul
echo ========================================================
echo   🏭 AIoT Industrial Cold Chain - One-Click Launcher
echo ========================================================
echo.
echo [1/2] กำลังเปิดบริการ Backend & Web Dashboard (:5000)...
start "AIoT Backend Service" cmd /k "cd /d %~dp0backend && py app.py"

echo [2/2] กำลังเปิดเว็บไซต์คู่มือบทเรียน MkDocs (:8000)...
start "AIoT Documentation Site" cmd /k "cd /d %~dp0 && py -m mkdocs serve"

echo.
echo ✅ เปิดระบบทั้ง 2 ส่วนเรียบร้อยแล้ว!
echo --------------------------------------------------------
echo 🌐 เว็บไซต์สอน AIoT (Docs)   : http://127.0.0.1:8000
echo 📊 หน้าเว็บ Dashboard & TMA   : http://localhost:5000
echo --------------------------------------------------------
echo.
pause
