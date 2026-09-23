@echo off
rem Lance ton IA : installe ce qu'il faut au premier lancement, puis ouvre l'interface.
rem Exemples :  lancer.bat        (interface dans le navigateur)
rem             lancer.bat chat   (discussion dans le terminal)
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" goto run

set "PYTHON="
where py >nul 2>nul && set "PYTHON=py -3"
if not defined PYTHON where python >nul 2>nul && set "PYTHON=python"
if not defined PYTHON goto nopython
%PYTHON% -c "import sys; sys.exit(sys.version_info < (3, 10))" || goto oldpython
echo Premiere installation, une ou deux minutes...
%PYTHON% -m venv .venv || goto failed

:run
".venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -r requirements.txt || goto failed
".venv\Scripts\python.exe" -m mon_ia %*
if errorlevel 1 pause
exit /b

:nopython
echo Python n'est pas installe. Telecharge-le sur https://www.python.org/downloads/
echo Pendant l'installation, coche bien la case "Add python.exe to PATH", puis relance ce fichier.
pause
exit /b 1

:oldpython
echo Il faut Python 3.10 ou plus recent : https://www.python.org/downloads/
pause
exit /b 1

:failed
echo L'installation a echoue. Verifie ta connexion internet, puis relance ce fichier.
pause
exit /b 1
