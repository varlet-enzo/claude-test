@echo off
rem Cree un lien public (Cloudflare Tunnel) vers ton IA pour la partager avec tes potes.
rem Lance d'abord ton IA avec lancer.bat, puis ce fichier dans une autre fenetre.
setlocal
cd /d "%~dp0"

findstr /r /b /c:"IA_MOT_DE_PASSE=." .env >nul 2>nul || goto nopassword
where cloudflared >nul 2>nul || goto nocloudflared

set "PORT=8000"
for /f "tokens=1,* delims==" %%a in ('findstr /b /c:"IA_PORT=" .env 2^>nul') do set "PORT=%%b"

echo Creation du lien de partage...
echo Envoie a tes potes l'adresse en https://...trycloudflare.com qui va s'afficher dans un cadre.
echo Garde cette fenetre ET celle de lancer.bat ouvertes : les fermer coupe le partage.
echo.
cloudflared tunnel --url http://localhost:%PORT%
pause
exit /b

:nopassword
echo Le mode partage n'est pas active : il faut d'abord proteger ton IA par un mot de passe.
echo 1. Copie le fichier .env.exemple et renomme la copie en .env
echo 2. Dans .env, remplis IA_MOT_DE_PASSE et IA_AMIS, en enlevant le # au debut des lignes
echo 3. Relance lancer.bat, puis ce fichier.
pause
exit /b 1

:nocloudflared
echo cloudflared n'est pas installe. Installe-le avec cette commande, puis relance ce fichier :
echo     winget install --id Cloudflare.cloudflared
echo Apres l'installation, ferme puis rouvre la fenetre.
pause
exit /b 1
