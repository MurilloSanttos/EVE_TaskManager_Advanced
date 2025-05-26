"""Módulo para persistência de tarefas em arquivo JSON."""

import json
import os
from typing import List, Dict

# Adiciona o diretório pai ao sys.path para permitir importações relativas
# Isso pode ser necessário dependendo de como o projeto é executado.
# Alternativamente, estruture como um pacote instalável.
import sys
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core.task import Task

class FileStorage:
    """Gerencia o carregamento e salvamento de tarefas em um arquivo JSON."""

    def __init__(self, filepath: str = "tasks.json"):
        """Inicializa o gerenciador de armazenamento.

        Args:
            filepath: O caminho para o arquivo JSON onde as tarefas serão armazenadas.
                      Por padrão, usa 'tasks.json' no diretório 'storage'.
        """
        # Garante que o caminho seja relativo ao diretório 'storage'
        storage_dir = os.path.dirname(__file__)
        self.filepath = os.path.join(storage_dir, filepath)
        # Cria o diretório 'storage' se ele não existir
        os.makedirs(storage_dir, exist_ok=True)

    def load_tasks(self) -> List[Task]:
        """Carrega as tarefas do arquivo JSON.

        Returns:
            Uma lista de objetos Task carregados do arquivo.
            Retorna uma lista vazia se o arquivo não existir ou estiver vazio/inválido.
        """
        tasks = []
        try:
            if os.path.exists(self.filepath) and os.path.getsize(self.filepath) > 0:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    tasks_data = json.load(f)
                    for task_data in tasks_data:
                        try:
                            tasks.append(Task.from_dict(task_data))
                        except (ValueError, KeyError) as e:
                            print(f"Erro ao carregar tarefa: {e}. Dados: {task_data}")
                            # Pode-se optar por pular a tarefa inválida ou parar
        except FileNotFoundError:
            print(f"Arquivo de tarefas '{self.filepath}' não encontrado. Um novo será criado ao salvar.")
        except json.JSONDecodeError:
            print(f"Erro ao decodificar JSON do arquivo '{self.filepath}'. O arquivo pode estar corrompido.")
            # Considerar fazer backup do arquivo corrompido e iniciar com um vazio
        except Exception as e:
            print(f"Erro inesperado ao carregar tarefas: {e}")
        return tasks

    def save_tasks(self, tasks: List[Task]):
        """Salva a lista de tarefas no arquivo JSON.

        Args:
            tasks: A lista de objetos Task a serem salvos.
        """
        try:
            tasks_data = [task.to_dict() for task in tasks]
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Erro de I/O ao salvar tarefas em '{self.filepath}': {e}")
        except Exception as e:
            print(f"Erro inesperado ao salvar tarefas: {e}")


