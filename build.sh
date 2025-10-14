#!/usr/bin/env bash
# Build script - creates a virtual environment and installs dependencies.
# All output is logged to logs/build.log.

set -e # Exit immediately if a command fails.

# --- Logging Setup ---
LOG_DIR="logs"
LOG_FILE="$LOG_DIR/build.log"
mkdir -p "$LOG_DIR"

# --- Detect Python command ---
detect_python() {
    echo "Detectando comando Python..."
    if command -v python3 &> /dev/null; then
        PYTHON=python3
    elif command -v python &> /dev/null; then
        PYTHON=python
    elif command -v py &> /dev/null; then
        PYTHON=py
    else
        echo "Python não encontrado. Instale o Python 3 e tente novamente."
        exit 1
    fi
    echo "Usando interpretador: $($PYTHON --version 2>&1)"
}

# --- Check if venv module is available ---
check_venv_module() {
    echo "Verificando módulo venv..."
    if ! $PYTHON -m venv --help &> /dev/null; then
        echo "Módulo venv não encontrado. Tentando instalar..."
        if [ -f /etc/debian_version ]; then
            sudo apt update && sudo apt install -y python3-venv
        elif [ -f /etc/redhat-release ]; then
            sudo yum install -y python3-venv
        else
            echo "Não foi possível instalar automaticamente o módulo venv. Instale manualmente."
            exit 1
        fi
    fi
}

# --- Ensure pip exists inside venv ---
ensure_pip_in_venv() {
    echo "Verificando se o pip está disponível..."
    if [ -f "venv/bin/python" ]; then
        VENV_PYTHON="venv/bin/python"
    elif [ -f "venv/Scripts/python.exe" ]; then
        VENV_PYTHON="venv/Scripts/python.exe"
    else
        echo "Erro: não foi possível localizar o Python dentro do venv."
        exit 1
    fi

    if ! $VENV_PYTHON -m pip --version &> /dev/null; then
        echo "pip não encontrado dentro do venv. Instalando com ensurepip..."
        $VENV_PYTHON -m ensurepip --upgrade
    fi
}

# --- Main Logic ---
main() {
    detect_python
    check_venv_module

    if [ "$1" == "clean" ]; then
        echo "Limpando ambiente virtual antigo..."
        rm -rf venv
    fi

    if [ ! -d "venv" ]; then
        echo "Criando ambiente virtual..."
        $PYTHON -m venv venv
    else
        echo "Ambiente virtual já existe."
    fi

    echo "Ativando ambiente virtual..."
    if [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate  # Windows
    else
        source venv/bin/activate      # Linux / WSL
    fi

    ensure_pip_in_venv

    echo "Atualizando pip..."
    pip install --upgrade pip

    if [ -f "requirements.txt" ]; then
        echo "Instalando dependências..."
        pip install -r requirements.txt
    else
        echo "Aviso: arquivo requirements.txt não encontrado. Pulando instalação."
    fi

    echo "Build concluído com sucesso."
}

main "$@" | tee -a "$LOG_FILE"
