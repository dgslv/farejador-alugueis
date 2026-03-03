@echo off
echo =^> Installing desktop dependencies...
pip install -r requirements-desktop.txt

echo =^> Building Aluguel.exe...
pyinstaller aluguel_windows.spec --clean --noconfirm

echo.
echo Done! Distributable: dist\Aluguel.exe
echo Users: copy Aluguel.exe anywhere and run it.
