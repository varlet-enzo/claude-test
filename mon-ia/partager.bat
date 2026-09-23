@echo off
rem Cree un lien public (Cloudflare Tunnel) vers ton IA pour la partager avec tes potes.
rem Lance d'abord ton IA avec lancer.bat, puis ce fichier dans une autre fenetre.
setlocal
cd /d "%~dp0"

if not exist ".env" goto noenv
rem Tolere les espaces en debut de ligne (quand on enleve le # mais pas l'espace qui suit).
findstr /r /c:"^ *IA_MOT_DE_PASSE=." .env >nul 2>nul || goto nopassword
where cloudflared >nul 2>nul || goto nocloudflared

set "PORT=8000"
for /f "tokens=1,* delims== " %%a in ('findstr /r /c:"^ *IA_PORT=" .env 2^>nul') do set "PORT=%%b"

echo Creation du lien de partage...
echo Envoie a tes potes l'adresse en https://...trycloudflare.com qui va s'afficher dans un cadre.
echo Garde cette fenetre ET celle de lancer.bat ouvertes : les fermer coupe le partage.
echo.
rem http2 plutot que quic (UDP), souvent bloque par les box, antivirus et reseaux d'ecole.
cloudflared tunnel --protocol http2 --url http://localhost:%PORT%
pause
exit /b

:noenv
echo Le fichier .env est introuvable dans ce dossier.
echo 1. Copie le fichier .env.exemple et renomme la copie en .env
echo    Attention : Windows cache souvent les extensions. Si ton fichier s'appelle en realite
echo    .env.txt, renomme-le en .env - dans l'Explorateur, menu Affichage, Afficher,
echo    coche Extensions de noms de fichiers pour le voir.
echo 2. Dans .env, remplis IA_MOT_DE_PASSE et IA_AMIS, puis relance lancer.bat et ce fichier.
pause
exit /b 1

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
