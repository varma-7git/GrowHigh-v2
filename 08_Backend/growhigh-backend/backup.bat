@echo off
rem Daily backup: double-click this file, or schedule it in Windows Task Scheduler.
rem Saves the database and uploaded files into the backups folder and keeps the latest 14.
cd /d "%~dp0"
call venv\Scripts\activate
python manage.py backup_db --with-media --keep 14
if errorlevel 1 (echo Backup FAILED, see the message above. & pause & exit /b 1)
echo Backup finished.
pause
