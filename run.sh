#!/bin/bash
# Run script - starts the Flask/Gunicorn server efficiently

set -e  # Para o script se algo falhar

# Verifica se um nome de ficheiro foi fornecido
if [ -z "$1" ]; then
  echo "Uso: $0 <filename>"
  exit 1
fi

FILE_TO_SERVE="$1"
HOST="0.0.0.0"
PORT="8080"
WORKERS=4  # Número de processos de trabalho Gunicorn

# Verifica se o ficheiro existe
if [ ! -f "$FILE_TO_SERVE" ]; then
  echo "Erro: o ficheiro '$FILE_TO_SERVE' não existe."
  exit 1
fi

# Verifica se o venv existe, caso contrário cria automaticamente
if [ ! -d "venv" ]; then
  echo "Virtual environment not found. Creating it..."
  python3 -m venv venv
fi

# Ativa o ambiente virtual
echo "Activating virtual environment..."
source venv/bin/activate

# Garante que o Gunicorn está instalado no ambiente
if ! python3 -m gunicorn --version >/dev/null 2>&1; then
  echo "Gunicorn not found, installing..."
  pip install gunicorn --no-warn-script-location --disable-pip-version-check
fi

# Inicia o servidor com Gunicorn
echo "Starting Gunicorn server for file '$FILE_TO_SERVE' on $HOST:$PORT..."
exec gunicorn --workers "$WORKERS" --bind "$HOST:$PORT" "app:create_app('$FILE_TO_SERVE')"
