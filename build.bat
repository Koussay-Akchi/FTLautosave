del /s /q build\*
del /s /q dist\*
rmdir /s /q build dist
pip install pyinstaller
pip install PyQt6
pyinstaller --onefile --windowed --icon=bg.ico --add-data="bg.ico;." --add-data="bg.jpg;." autosave.py