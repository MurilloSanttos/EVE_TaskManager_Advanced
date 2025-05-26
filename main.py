"""Ponto de entrada principal para a aplicação EVE Task Manager."""

import sys
import os

# Garante que o diretório raiz do projeto esteja no sys.path
# para que as importações funcionem corretamente quando executado de qualquer lugar.
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importa a função main da interface CLI
from cli.interface import main

if __name__ == "__main__":
    # Executa a interface de linha de comando
    main()

