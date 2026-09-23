#!/usr/bin/env bash
# Crée un lien public (Cloudflare Tunnel) vers ton IA pour la partager avec tes potes.
# Lance d'abord ton IA avec ./lancer.sh, puis ce script dans un autre terminal.
set -e
cd "$(dirname "$0")"

if ! grep -qE '^IA_MOT_DE_PASSE=.+' .env 2>/dev/null; then
  echo "Le mode partage n'est pas activé : il faut d'abord protéger ton IA par un mot de passe."
  echo "Copie .env.exemple en .env, remplis IA_MOT_DE_PASSE et IA_AMIS, puis relance ./lancer.sh et ce script."
  exit 1
fi
if ! command -v cloudflared >/dev/null 2>&1; then
  echo "cloudflared n'est pas installé : https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
  echo "(sur Mac : brew install cloudflared)"
  exit 1
fi

PORT=$(grep -E '^IA_PORT=' .env | cut -d= -f2)
echo "Envoie à tes potes l'adresse en https://…trycloudflare.com qui va s'afficher."
echo "Garde ce terminal et celui de lancer.sh ouverts : les fermer coupe le partage."
exec cloudflared tunnel --url "http://localhost:${PORT:-8000}"
