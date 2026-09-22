@echo off
rem Builds Farejador.exe into dist\ (at the repo root). Used locally and by the Release workflow.
rem Requires Python 3.11+ on PATH.
setlocal
cd /d "%~dp0.."

echo ==^> Installing the package and the packaging dependencies...
python -m pip install -e ".[desktop]" || exit /b 1

for /f "delims=" %%v in ('python -c "from farejador import __version__; print(__version__)"') do set "VERSION=%%v"
if not defined VERSION (
  echo Could not read the package version
  exit /b 1
)

echo ==^> Building Farejador.exe (v%VERSION%)...
pyinstaller packaging\farejador-windows.spec --clean --noconfirm || exit /b 1

move /y "dist\Farejador.exe" "dist\Farejador-%VERSION%-Windows-x64.exe" >nul || exit /b 1

echo.
echo Done: dist\Farejador-%VERSION%-Windows-x64.exe
echo Users: copy the .exe anywhere and run it.
