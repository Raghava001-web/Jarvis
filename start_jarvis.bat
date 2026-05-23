@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    start "" /min cmd /c ".venv\Scripts\python.exe -u -m jarvis.gui.desktop_gui"
) else (
    echo Virtual environment not found. Using global python.
    start "" /min cmd /c "python -u -m jarvis.gui.desktop_gui"
)
exit
