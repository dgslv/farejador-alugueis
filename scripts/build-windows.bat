@echo off
rem Gera Farejador.exe em dist\. Usado localmente e pelo workflow Release.
rem Requer Python 3.11+ no PATH.
setlocal
cd /d "%~dp0.."

for /f "delims=" %%v in ('python -c "from version import __version__; print(__version__)"') do set "VERSION=%%v"
if not defined VERSION (
  echo Nao consegui ler a versao em version.py
  exit /b 1
)

echo ==^> Instalando dependencias de empacotamento...
python -m pip install -r requirements-desktop.txt || exit /b 1

echo ==^> Gerando Farejador.exe (v%VERSION%)...
pyinstaller farejador-windows.spec --clean --noconfirm || exit /b 1

move /y "dist\Farejador.exe" "dist\Farejador-%VERSION%-Windows-x64.exe" >nul || exit /b 1

echo.
echo Pronto: dist\Farejador-%VERSION%-Windows-x64.exe
echo Usuarios: copiar o .exe para qualquer pasta e executar.
