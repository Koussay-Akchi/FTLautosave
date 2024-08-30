del /s /q build\*
del /s /q dist\*
rmdir /s /q build dist
pyinstaller --onefile --windowed --add-data="bg.ico;." --add-data="bg.jpg;." autosave.py

