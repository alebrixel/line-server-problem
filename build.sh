#!/bin/bash
# Build script - creates and prepares a virtual environment efficiently

# Se for executado com o argumento "clean", apaga o venv
if [ "$1" == "clean" ]; then
  echo "Cleaning old virtual environment..."
  rm -rf venv
fi

# Cria o ambiente virtual apenas se não existir
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
else
  echo "Virtual environment already exists, skipping creation."
fi

# Ativa o ambiente virtual
echo "Activating virtual environment..."
source venv/bin/activate

# Verifica versão atual do pip
PIP_VERSION=$(pip --version | awk '{print $2}')

# Atualiza o pip apenas se for muito antigo
if [[ "$PIP_VERSION" < "24.0" ]]; then
  echo "Upgrading pip..."
  pip install --upgrade pip
else
  echo "Pip is up to date ($PIP_VERSION)."
fi

# Instala dependências (sem reinstalar desnecessariamente)
echo "Installing dependencies..."
pip install -r requirements.txt --no-warn-script-location --disable-pip-version-check

echo "Build complete."
