#!/usr/bin/env bash
# Lance ton IA : installe ce qu'il faut au premier lancement, puis ouvre l'interface.
# Exemples :  ./lancer.sh        (interface dans le navigateur)
#             ./lancer.sh chat   (discussion dans le terminal)
set -e
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  PYTHON=""
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then PYTHON="$candidate"; break; fi
  done
  if [ -z "$PYTHON" ]; then
    echo "Python n'est pas installé : télécharge-le sur https://www.python.org/downloads/ (version 3.10 ou plus récente)."
    exit 1
  fi
  if ! "$PYTHON" -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
    echo "Il faut Python 3.10 ou plus récent : https://www.python.org/downloads/"
    exit 1
  fi
  echo "Première installation (une ou deux minutes)…"
  "$PYTHON" -m venv .venv
fi

.venv/bin/python -m pip install --quiet --disable-pip-version-check -r requirements.txt
exec .venv/bin/python -m mon_ia "$@"
