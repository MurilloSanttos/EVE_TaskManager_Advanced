"""Módulo da interface de linha de comando (CLI) para interagir com o TaskManager."""

import argparse
import datetime
from typing import List, Dict, Any, Optional, Set

# Adiciona o diretório pai ao sys.path para permitir importações relativas
import sys
import os
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core.task_manager import TaskManager
from core.task import Task
from storage.file_storage import FileStorage

# --- Funções Auxiliares da CLI (MODO INTERATIVO) ---

def print_tasks(tasks: List[Task]):
    """Imprime uma lista de tarefas de forma formatada."""
    if not tasks:
        print("Nenhuma tarefa encontrada.")
        return
    print("\n--- Lista de Tarefas ---")
    for task in tasks:
        print("-" * 20)
        print(task)
    print("-" * 20)
    print(f"Total: {len(tasks)} tarefa(s)")

def get_input(prompt: str, required: bool = True, input_type=str, default=None):
    """Solicita input do usuário com validação básica (MODO INTERATIVO)."""
    prompt_suffix = f" [Padrão: {default}]: " if default and not required else ": "
    while True:
        try:
            value = input(prompt + prompt_suffix).strip()
            if value:
                try: return input_type(value)
                except ValueError: print(f"Entrada inválida. Por favor, insira um valor do tipo {input_type.__name__}.")
            elif not required: return default
            else: print("Este campo é obrigatório.")
        except EOFError:
             print("\nEntrada interativa não disponível. Usando valor padrão ou falhando se obrigatório.")
             if required and default is None: raise ValueError(f"Entrada obrigatória '{prompt}' não fornecida em modo não interativo.")
             return default

def get_date_input(prompt: str, current_value: str | None = None) -> str | None:
    """Solicita input de data no formato AAAA-MM-DD (MODO INTERATIVO)."""
    prompt_suffix = f" (AAAA-MM-DD, atual: {current_value or 'N/A'}, deixe em branco para não alterar): "
    while True:
        try:
            date_str = input(prompt + prompt_suffix).strip()
            if not date_str: return None
            if date_str.upper() == 'N/A' or date_str == '-': return ''
            try:
                datetime.datetime.strptime(date_str, "%Y-%m-%d")
                return date_str
            except ValueError: print("Formato de data inválido. Use AAAA-MM-DD ou 'N/A' para remover.")
        except EOFError: print("\nEntrada interativa não disponível para data."); return None

def get_choice_input(prompt: str, choices: List[str], default: str | None = None, current_value: str | None = None, allow_none: bool = False) -> str | None:
    """Solicita que o usuário escolha uma opção de uma lista (MODO INTERATIVO)."""
    valid_choices = choices + ([ 'none' ] if allow_none else [])
    choices_lower = [str(c).lower() for c in valid_choices]
    prompt += f" ({'/'.join(map(str, valid_choices))})"
    current_display = f"Atual: {current_value}" if current_value is not None else ""
    default_display = f"Padrão: {default}" if default is not None else ""
    separator = ", " if current_display and default_display else ""
    prompt_suffix = f" [{current_display}{separator}{default_display}]: " if current_display or default_display else ": "
    prompt += prompt_suffix
    while True:
        try:
            value = input(prompt).strip().lower()
            if not value: return default if default is not None else None
            if value in choices_lower:
                idx = choices_lower.index(value)
                return None if allow_none and valid_choices[idx] == 'none' else valid_choices[idx]
            print(f"Opção inválida. Escolha entre: {', '.join(map(str, valid_choices))}")
        except EOFError: print(f"\nEntrada interativa não disponível para escolha. Usando padrão '{default}'."); return default

def confirm_action(prompt: str) -> bool:
    """Pede confirmação do usuário (S/N) (MODO INTERATIVO)."""
    while True:
        try:
            response = input(prompt + " [s/N]: ").strip().lower()
            if response == 's': return True
            elif response == 'n' or response == '': return False
            else: print("Resposta inválida. Por favor, digite 's' para sim ou 'n' para não.")
        except EOFError: print("\nEntrada interativa não disponível para confirmação. Assumindo 'Não'."); return False

# --- Funções de Comando da CLI ---

def handle_add_task(task_manager: TaskManager, args: argparse.Namespace):
    """Lida com o comando 'add'."""
    print("\n--- Adicionar Nova Tarefa ---")
    try:
        new_task = task_manager.add_task(
            title=args.title,
            description=args.description if args.description is not None else "",
            due_date_str=args.due_date,
            priority=args.priority,
            category=args.category,
            eisenhower_quadrant=args.eisenhower,
            depends_on_ids=args.depends_on,
            projects=args.projects, # Novo
            contexts=args.contexts  # Novo
        )
        print("\nTarefa adicionada com sucesso!")
        print(new_task)
    except ValueError as e:
        print(f"\nErro ao adicionar tarefa: {e}")

def handle_list_tasks(task_manager: TaskManager, args: argparse.Namespace):
    """Lida com o comando 'list'."""
    filters: Dict[str, Any] = {}
    if args.status: filters["status"] = args.status
    if args.priority: filters["priority"] = args.priority
    if args.category: filters["category"] = args.category
    if args.due: filters["due_date"] = args.due
    if args.eisenhower: filters["eisenhower"] = args.eisenhower
    if args.project: filters["project"] = args.project # Novo filtro
    if args.context: filters["context"] = args.context # Novo filtro

    sort_by = args.sort_by if args.sort_by else 'due_date'

    valid_eisenhower = list(Task.EISENHOWER_QUADRANTS.keys()) + ['None']
    if args.eisenhower and args.eisenhower not in valid_eisenhower:
        print(f"Filtro Eisenhower inválido: {args.eisenhower}. Use Q1, Q2, Q3, Q4 ou None.")
        return

    tasks = task_manager.list_tasks(filters=filters, sort_by=sort_by)
    print(f"\n(Ordenado por: {sort_by})")
    print_tasks(tasks)

def handle_edit_task(task_manager: TaskManager, args: argparse.Namespace):
    """Lida com o comando 'edit'."""
    task_id = args.id
    task = task_manager.get_task_by_id(task_id)
    if not task: print(f"Erro: Tarefa com ID '{task_id}' não encontrada."); return

    print(f"\n--- Editando Tarefa ID: {task.task_id} ---")
    updates: Dict[str, Any] = {}
    if args.title is not None: updates["title"] = args.title
    if args.description is not None: updates["description"] = args.description
    if args.due_date is not None: updates["due_date_str"] = args.due_date
    if args.priority is not None: updates["priority"] = args.priority
    if args.category is not None: updates["category"] = args.category
    if args.status is not None: updates["status"] = args.status
    if args.eisenhower is not None:
        quadrant = None if args.eisenhower.lower() in ['none', 'clear', ''] else args.eisenhower
        updates["eisenhower_quadrant"] = quadrant
    # Edição de dependências, projetos, contextos é feita por comandos específicos

    if not updates:
        print("Nenhuma alteração fornecida via argumentos.")
        return

    try:
        updated_task = task_manager.update_task(task_id, **updates)
        if updated_task: print("\nTarefa atualizada com sucesso!"); print(updated_task)
    except ValueError as e:
        print(f"\nErro ao atualizar tarefa: {e}")

def handle_delete_task(task_manager: TaskManager, args: argparse.Namespace):
    """Lida com o comando 'delete'."""
    task_id = args.id
    task = task_manager.get_task_by_id(task_id)
    if not task: print(f"Erro: Tarefa com ID '{task_id}' não encontrada."); return

    print("\n--- Excluir Tarefa ---")
    print("Tarefa a ser excluída:"); print(task); print("-"*20)

    confirmed = args.yes or confirm_action("Tem certeza que deseja excluir esta tarefa?")
    if confirmed:
        if task_manager.delete_task(task_id):
            print(f"Tarefa ID '{task_id}' excluída com sucesso.")
    else:
        print("Exclusão cancelada.")

def handle_complete_task(task_manager: TaskManager, args: argparse.Namespace):
    """Lida com o comando 'complete'."""
    task_id = args.id
    updated_task = task_manager.mark_task_complete(task_id)
    if updated_task: print(f"\nTarefa ID '{task_id}' marcada como concluída!"); print(updated_task)

def handle_undo_task(task_manager: TaskManager, args: argparse.Namespace):
    """Lida com o comando 'undo' (marca como pendente)."""
    task_id = args.id
    updated_task = task_manager.mark_task_pending(task_id)
    if updated_task: print(f"\nTarefa ID '{task_id}' marcada como pendente (conclusão desfeita)!"); print(updated_task)

# --- Funções para Dependências --- 

def handle_add_dependency(task_manager: TaskManager, args: argparse.Namespace):
    """Lida com o comando 'add-dep'."""
    task_id = args.task_id
    dependency_id = args.dependency_id
    print(f"\n--- Adicionar Dependência: Tarefa '{task_id}' depende de '{dependency_id}' ---")
    success = task_manager.add_dependency(task_id, dependency_id)
    if success:
        updated_task = task_manager.get_task_by_id(task_id)
        if updated_task: print("\nEstado atual da tarefa:"); print(updated_task)

def handle_remove_dependency(task_manager: TaskManager, args: argparse.Namespace):
    """Lida com o comando 'remove-dep'."""
    task_id = args.task_id
    dependency_id = args.dependency_id
    print(f"\n--- Remover Dependência: Tarefa '{task_id}' não dependerá mais de '{dependency_id}' ---")
    success = task_manager.remove_dependency(task_id, dependency_id)
    if success:
        updated_task = task_manager.get_task_by_id(task_id)
        if updated_task: print("\nEstado atual da tarefa:"); print(updated_task)

# --- Novas Funções para Projetos e Contextos --- 

def handle_add_project(task_manager: TaskManager, args: argparse.Namespace):
    """Lida com o comando 'add-project'."""
    task_id = args.task_id
    project_name = args.project_name
    print(f"\n--- Adicionar Projeto '{project_name}' à Tarefa '{task_id}' ---")
    success = task_manager.add_project_to_task(task_id, project_name)
    if success:
        updated_task = task_manager.get_task_by_id(task_id)
        if updated_task: print("\nEstado atual da tarefa:"); print(updated_task)

def handle_remove_project(task_manager: TaskManager, args: argparse.Namespace):
    """Lida com o comando 'remove-project'."""
    task_id = args.task_id
    project_name = args.project_name
    print(f"\n--- Remover Projeto '{project_name}' da Tarefa '{task_id}' ---")
    success = task_manager.remove_project_from_task(task_id, project_name)
    if success:
        updated_task = task_manager.get_task_by_id(task_id)
        if updated_task: print("\nEstado atual da tarefa:"); print(updated_task)

def handle_add_context(task_manager: TaskManager, args: argparse.Namespace):
    """Lida com o comando 'add-context'."""
    task_id = args.task_id
    context_name = args.context_name
    print(f"\n--- Adicionar Contexto '{context_name}' à Tarefa '{task_id}' ---")
    success = task_manager.add_context_to_task(task_id, context_name)
    if success:
        updated_task = task_manager.get_task_by_id(task_id)
        if updated_task: print("\nEstado atual da tarefa:"); print(updated_task)

def handle_remove_context(task_manager: TaskManager, args: argparse.Namespace):
    """Lida com o comando 'remove-context'."""
    task_id = args.task_id
    context_name = args.context_name
    print(f"\n--- Remover Contexto '{context_name}' da Tarefa '{task_id}' ---")
    success = task_manager.remove_context_from_task(task_id, context_name)
    if success:
        updated_task = task_manager.get_task_by_id(task_id)
        if updated_task: print("\nEstado atual da tarefa:"); print(updated_task)

# --- Configuração do argparse e Função Principal ---

def main():
    """Função principal que configura o argparse e executa a CLI."""
    storage = FileStorage()
    task_manager = TaskManager(storage)

    parser = argparse.ArgumentParser(description="EVE - Sua Assistente Pessoal de Tarefas", prog="eve")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # --- Comando 'add' ---
    parser_add = subparsers.add_parser("add", help="Adicionar uma nova tarefa")
    parser_add.add_argument("-t", "--title", required=True, help="Título da tarefa")
    parser_add.add_argument("-d", "--description", default=None, help="Descrição")
    parser_add.add_argument("--due-date", default=None, help="Data de vencimento (AAAA-MM-DD)")
    parser_add.add_argument("-p", "--priority", choices=Task.VALID_PRIORITIES, default="Média", help="Prioridade")
    parser_add.add_argument("-c", "--category", default="Geral", help="Categoria")
    parser_add.add_argument("-e", "--eisenhower", choices=list(Task.EISENHOWER_QUADRANTS.keys()), default=None, help="Quadrante Eisenhower (Q1-Q4)")
    parser_add.add_argument("--depends-on", nargs='+', default=None, help="IDs das tarefas das quais esta depende")
    parser_add.add_argument("--projects", nargs='+', default=None, help="Projetos associados (ex: Casa Trabalho)") # Novo
    parser_add.add_argument("--contexts", nargs='+', default=None, help="Contextos associados (ex: @email @casa)") # Novo
    parser_add.set_defaults(func=handle_add_task)

    # --- Comando 'list' ---
    parser_list = subparsers.add_parser("list", help="Listar tarefas existentes")
    parser_list.add_argument("-s", "--status", choices=Task.VALID_STATUSES, help="Filtrar por status")
    parser_list.add_argument("-p", "--priority", choices=Task.VALID_PRIORITIES, help="Filtrar por prioridade")
    parser_list.add_argument("-c", "--category", help="Filtrar por categoria")
    parser_list.add_argument("--due", choices=["vencidas", "hoje", "futuras"], help="Filtrar por data de vencimento")
    parser_list.add_argument("-e", "--eisenhower", choices=list(Task.EISENHOWER_QUADRANTS.keys()) + ['None'], help="Filtrar por quadrante Eisenhower (Q1-Q4 ou 'None')")
    parser_list.add_argument("--project", help="Filtrar por nome do projeto (case-insensitive)") # Novo
    parser_list.add_argument("--context", help="Filtrar por nome do contexto (case-insensitive)") # Novo
    parser_list.add_argument("--sort-by", choices=['due_date', 'priority', 'eisenhower', 'creation_date'], default='due_date', help="Critério de ordenação")
    parser_list.set_defaults(func=handle_list_tasks)

    # --- Comando 'edit' ---
    parser_edit = subparsers.add_parser("edit", help="Editar atributos básicos de uma tarefa")
    parser_edit.add_argument("id", help="ID da tarefa a ser editada")
    parser_edit.add_argument("-t", "--title", default=None, help="Novo título")
    parser_edit.add_argument("-d", "--description", nargs='?', const='', default=None, help="Nova descrição (use sem valor para limpar)")
    parser_edit.add_argument("--due-date", default=None, help="Nova data de vencimento (AAAA-MM-DD ou 'N/A')")
    parser_edit.add_argument("-p", "--priority", choices=Task.VALID_PRIORITIES, default=None, help="Nova prioridade")
    parser_edit.add_argument("-c", "--category", default=None, help="Nova categoria")
    parser_edit.add_argument("-s", "--status", choices=Task.VALID_STATUSES, default=None, help="Novo status (cuidado com dependências!)")
    parser_edit.add_argument("-e", "--eisenhower", default=None, help="Novo quadrante Eisenhower (Q1-Q4, ou 'None'/'clear')")
    parser_edit.set_defaults(func=handle_edit_task)

    # --- Comando 'delete' ---
    parser_delete = subparsers.add_parser("delete", help="Excluir uma tarefa (impede se for dependência de outra)")
    parser_delete.add_argument("id", help="ID da tarefa a ser excluída")
    parser_delete.add_argument("-y", "--yes", action="store_true", help="Confirmar exclusão sem perguntar")
    parser_delete.set_defaults(func=handle_delete_task)

    # --- Comando 'complete' ---
    parser_complete = subparsers.add_parser("complete", help="Marcar uma tarefa como concluída (verifica dependências)")
    parser_complete.add_argument("id", help="ID da tarefa a ser marcada como concluída")
    parser_complete.set_defaults(func=handle_complete_task)

    # --- Comando 'undo' ---
    parser_undo = subparsers.add_parser("undo", help="Marcar uma tarefa concluída como pendente (verifica bloqueios)")
    parser_undo.add_argument("id", help="ID da tarefa a ser marcada como pendente")
    parser_undo.set_defaults(func=handle_undo_task)

    # --- Comandos de Dependência ---
    parser_add_dep = subparsers.add_parser("add-dep", help="Adicionar uma dependência (tarefa A depende da tarefa B)")
    parser_add_dep.add_argument("task_id", help="ID da tarefa que terá a dependência (A)")
    parser_add_dep.add_argument("dependency_id", help="ID da tarefa da qual ela depende (B)")
    parser_add_dep.set_defaults(func=handle_add_dependency)

    parser_remove_dep = subparsers.add_parser("remove-dep", help="Remover uma dependência")
    parser_remove_dep.add_argument("task_id", help="ID da tarefa da qual remover a dependência")
    parser_remove_dep.add_argument("dependency_id", help="ID da tarefa que deixará de ser dependência")
    parser_remove_dep.set_defaults(func=handle_remove_dependency)

    # --- Comandos de Projeto --- 
    parser_add_proj = subparsers.add_parser("add-project", help="Adicionar um projeto a uma tarefa")
    parser_add_proj.add_argument("task_id", help="ID da tarefa")
    parser_add_proj.add_argument("project_name", help="Nome do projeto a adicionar")
    parser_add_proj.set_defaults(func=handle_add_project)

    parser_remove_proj = subparsers.add_parser("remove-project", help="Remover um projeto de uma tarefa")
    parser_remove_proj.add_argument("task_id", help="ID da tarefa")
    parser_remove_proj.add_argument("project_name", help="Nome do projeto a remover")
    parser_remove_proj.set_defaults(func=handle_remove_project)

    # --- Comandos de Contexto --- 
    parser_add_ctx = subparsers.add_parser("add-context", help="Adicionar um contexto a uma tarefa")
    parser_add_ctx.add_argument("task_id", help="ID da tarefa")
    parser_add_ctx.add_argument("context_name", help="Nome do contexto a adicionar (ex: @casa)")
    parser_add_ctx.set_defaults(func=handle_add_context)

    parser_remove_ctx = subparsers.add_parser("remove-context", help="Remover um contexto de uma tarefa")
    parser_remove_ctx.add_argument("task_id", help="ID da tarefa")
    parser_remove_ctx.add_argument("context_name", help="Nome do contexto a remover")
    parser_remove_ctx.set_defaults(func=handle_remove_context)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        # Validação extra para edição de quadrante Eisenhower
        if args.command == 'edit' and args.eisenhower is not None and args.eisenhower.lower() not in ['q1', 'q2', 'q3', 'q4', 'none', 'clear', '']:
             valid_keys_str = ", ".join(list(Task.EISENHOWER_QUADRANTS.keys()) + ['None', 'clear'])
             parser.error(f"Argumento --eisenhower inválido: '{args.eisenhower}'. Use {valid_keys_str}.")
        
        args.func(task_manager, args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

