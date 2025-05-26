"""Módulo contendo o gerenciador de tarefas (TaskManager) com funcionalidades avançadas."""

import datetime
import re # Para limpar nomes de projetos/contextos
import uuid # Import faltante
from typing import List, Optional, Dict, Any, Set

# Adiciona o diretório pai ao sys.path para permitir importações relativas
import sys
import os
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from core.task import Task
from storage.file_storage import FileStorage

class TaskManager:
    """Gerencia as operações relacionadas às tarefas (CRUD e avançadas)."""

    def __init__(self, storage: FileStorage):
        """Inicializa o TaskManager com um mecanismo de armazenamento."""
        self.storage = storage
        self.tasks: List[Task] = self.storage.load_tasks()
        self._task_map: Dict[str, Task] = {task.task_id: task for task in self.tasks}

    def _update_task_map(self):
        """Helper interno para atualizar o mapa de IDs."""
        self._task_map = {task.task_id: task for task in self.tasks}

    def _check_circular_dependency(self, task_id: str, dependency_id: str, visited: Optional[Set[str]] = None) -> bool:
        """Verifica se adicionar a dependência cria um ciclo (DFS)."""
        if visited is None: visited = set()
        task = self.get_task_by_id(dependency_id)
        if not task: return False
        visited.add(dependency_id)
        for dep_of_dep_id in task.depends_on_ids:
            if dep_of_dep_id == task_id: return True
            if dep_of_dep_id in visited: continue
            if self._check_circular_dependency(task_id, dep_of_dep_id, visited.copy()): return True
        return False
        
    def _normalize_tag(self, tag: str) -> str:
        """Normaliza um nome de projeto/contexto (lowercase, sem espaços extras)."""
        return re.sub(r'\s+', ' ', tag).strip().lower()

    def add_task(self, title: str, description: str = "", due_date_str: str | None = None,
                 priority: str = "Média", category: str = "Geral",
                 eisenhower_quadrant: str | None = None,
                 depends_on_ids: Optional[List[str] | Set[str]] = None,
                 projects: Optional[List[str] | Set[str]] = None,
                 contexts: Optional[List[str] | Set[str]] = None) -> Task:
        """Cria e adiciona uma nova tarefa à lista.

        Raises:
            ValueError: Se os dados da tarefa forem inválidos ou dependências não existirem/criarem ciclo.
        """
        temp_task_id = str(uuid.uuid4())
        if depends_on_ids:
            for dep_id in depends_on_ids:
                if dep_id not in self._task_map: raise ValueError(f"Tarefa dependente com ID '{dep_id}' não encontrada.")
                if self._check_circular_dependency(temp_task_id, dep_id): raise ValueError(f"Adicionar dependência de '{dep_id}' criaria um ciclo.")

        try:
            # Normaliza projetos e contextos ao criar
            normalized_projects = {self._normalize_tag(p) for p in projects if p} if projects else set()
            normalized_contexts = {self._normalize_tag(c) for c in contexts if c} if contexts else set()
            
            new_task = Task(
                task_id=temp_task_id,
                title=title, description=description, due_date_str=due_date_str,
                priority=priority, category=category, status="Pendente",
                eisenhower_quadrant=eisenhower_quadrant,
                depends_on_ids=depends_on_ids,
                projects=normalized_projects,
                contexts=normalized_contexts
            )
            self.tasks.append(new_task)
            self._task_map[new_task.task_id] = new_task
            self.save_tasks()
            return new_task
        except ValueError as e:
            print(f"Erro ao criar tarefa: {e}")
            raise

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """Busca uma tarefa pelo seu ID usando o mapa."""
        return self._task_map.get(task_id)

    def list_tasks(self, filters: Dict[str, Any] = None, sort_by: str = 'due_date') -> List[Task]:
        """Lista tarefas, aplicando filtros e ordenação."""
        filtered_tasks = list(self.tasks)

        if filters:
            if 'status' in filters: filtered_tasks = [t for t in filtered_tasks if t.status == filters['status']]
            if 'priority' in filters: filtered_tasks = [t for t in filtered_tasks if t.priority == filters['priority']]
            if 'category' in filters: filtered_tasks = [t for t in filtered_tasks if t.category.lower() == filters['category'].lower()]
            if 'due_date' in filters:
                today = datetime.date.today()
                filter_type = filters['due_date']
                if filter_type == 'vencidas': filtered_tasks = [t for t in filtered_tasks if t.due_date and t.due_date < today and t.status == 'Pendente']
                elif filter_type == 'hoje': filtered_tasks = [t for t in filtered_tasks if t.due_date and t.due_date == today]
                elif filter_type == 'futuras': filtered_tasks = [t for t in filtered_tasks if t.due_date and t.due_date > today]
            if 'eisenhower' in filters:
                quadrant_filter = filters['eisenhower']
                if quadrant_filter == 'None': filtered_tasks = [t for t in filtered_tasks if t.eisenhower_quadrant is None]
                elif quadrant_filter in Task.EISENHOWER_QUADRANTS: filtered_tasks = [t for t in filtered_tasks if t.eisenhower_quadrant == quadrant_filter]
            # Filtros por projeto/contexto (case-insensitive)
            if 'project' in filters:
                project_filter = self._normalize_tag(filters['project'])
                filtered_tasks = [t for t in filtered_tasks if project_filter in {self._normalize_tag(p) for p in t.projects}]
            if 'context' in filters:
                context_filter = self._normalize_tag(filters['context'])
                filtered_tasks = [t for t in filtered_tasks if context_filter in {self._normalize_tag(c) for c in t.contexts}]

        # Ordenação
        reverse_sort = False
        if sort_by == 'due_date': key_func = lambda t: t.due_date if t.due_date else datetime.date.max
        elif sort_by == 'priority': key_func = lambda t: Task.VALID_PRIORITIES.index(t.priority)
        elif sort_by == 'eisenhower':
            quadrant_order = {q: i for i, q in enumerate(Task.EISENHOWER_QUADRANTS.keys())}
            key_func = lambda t: quadrant_order.get(t.eisenhower_quadrant, len(quadrant_order))
        elif sort_by == 'creation_date':
             key_func = lambda t: t.creation_date
             reverse_sort = True
        else: key_func = lambda t: t.due_date if t.due_date else datetime.date.max

        filtered_tasks.sort(key=key_func, reverse=reverse_sort)
        if sort_by != 'priority': filtered_tasks.sort(key=lambda t: Task.VALID_PRIORITIES.index(t.priority))
        if sort_by != 'due_date' and sort_by != 'creation_date': filtered_tasks.sort(key=lambda t: t.due_date if t.due_date else datetime.date.max)

        return filtered_tasks

    def update_task(self, task_id: str, **updates: Any) -> Optional[Task]:
        """Atualiza atributos básicos de uma tarefa. 
           Para dependências, projetos, contextos, use métodos específicos.
        """
        task = self.get_task_by_id(task_id)
        if not task: print(f"Erro: Tarefa com ID '{task_id}' não encontrada para atualização."); return None

        if updates.get('status') == 'Concluída' and task.status == 'Pendente':
            if not self.can_complete_task(task_id): return None
            
        # Não permitir update de depends_on_ids, projects, contexts via este método
        updates.pop('depends_on_ids', None)
        updates.pop('projects', None)
        updates.pop('contexts', None)

        try:
            task.update(**updates)
            self.save_tasks()
            return task
        except ValueError as e:
            print(f"Erro ao atualizar tarefa: {e}")
            raise

    def delete_task(self, task_id: str) -> bool:
        """Deleta uma tarefa pelo ID e remove dependências relacionadas."""
        task_to_delete = self.get_task_by_id(task_id)
        if not task_to_delete: print(f"Erro: Tarefa com ID '{task_id}' não encontrada para exclusão."); return False

        blocking_tasks = []
        for task in self.tasks:
             if task_id in task.depends_on_ids: blocking_tasks.append(task.task_id)
        if blocking_tasks:
             print(f"Erro: Não é possível excluir a tarefa '{task_to_delete.title}' (ID: {task_id}) porque as seguintes tarefas dependem dela:")
             for blocked_id in blocking_tasks:
                  blocked_task = self.get_task_by_id(blocked_id)
                  print(f"- '{blocked_task.title if blocked_task else 'Desconhecida'}' (ID: {blocked_id})")
             print("Remova essas dependências primeiro.")
             return False

        self.tasks.remove(task_to_delete)
        del self._task_map[task_id]
        self.save_tasks()
        return True

    def can_complete_task(self, task_id: str) -> bool:
        """Verifica se todas as dependências de uma tarefa estão concluídas."""
        task = self.get_task_by_id(task_id)
        if not task: print(f"Erro: Tarefa com ID '{task_id}' não encontrada para verificação."); return False
        if not task.depends_on_ids: return True

        incomplete_deps = []
        missing_deps = []
        for dep_id in list(task.depends_on_ids):
            dependency_task = self.get_task_by_id(dep_id)
            if not dependency_task: missing_deps.append(dep_id)
            elif dependency_task.status == 'Pendente': incomplete_deps.append(f"'{dependency_task.title}' (ID: {dep_id})")
        if missing_deps:
             print(f"Aviso: As seguintes dependências da tarefa '{task.title}' (ID: {task_id}) não foram encontradas e serão removidas:")
             for mid in missing_deps: print(f"- ID: {mid}"); task.depends_on_ids.remove(mid)
             self.save_tasks()
        if incomplete_deps:
            print(f"Erro: Não é possível concluir a tarefa '{task.title}' (ID: {task_id}).")
            print("As seguintes dependências ainda estão pendentes:")
            for dep_info in incomplete_deps: print(f"- {dep_info}")
            return False
        return True

    def mark_task_complete(self, task_id: str) -> Optional[Task]:
        """Marca uma tarefa como concluída, APÓS verificar dependências."""
        if not self.can_complete_task(task_id): return None
        task = self.get_task_by_id(task_id)
        if task and task.status == 'Pendente':
            task.mark_complete()
            self.save_tasks()
            return task
        elif task: print(f"Tarefa '{task_id}' já está concluída.")
        return None

    def mark_task_pending(self, task_id: str) -> Optional[Task]:
        """Marca uma tarefa como pendente. Verifica se isso bloqueia outras tarefas."""
        task = self.get_task_by_id(task_id)
        if not task: print(f"Erro: Tarefa com ID '{task_id}' não encontrada."); return None
        if task.status == 'Pendente': print(f"Tarefa '{task_id}' já está pendente."); return None

        blocked_completed_tasks = []
        for other_task in self.tasks:
             if task_id in other_task.depends_on_ids and other_task.status == 'Concluída':
                  blocked_completed_tasks.append(f"'{other_task.title}' (ID: {other_task.task_id})")
        if blocked_completed_tasks:
             print(f"Erro: Não é possível marcar '{task.title}' (ID: {task_id}) como pendente.")
             print("As seguintes tarefas concluídas dependem dela e se tornariam inválidas:")
             for blocked_info in blocked_completed_tasks: print(f"- {blocked_info}")
             print("Marque essas tarefas como pendentes primeiro, se necessário.")
             return None

        task.mark_pending()
        self.save_tasks()
        return task

    # --- Métodos para Gerenciar Dependências --- 

    def add_dependency(self, task_id: str, dependency_id: str) -> bool:
        """Adiciona dependency_id como uma dependência para task_id."""
        task = self.get_task_by_id(task_id)
        dependency_task = self.get_task_by_id(dependency_id)
        if not task: print(f"Erro: Tarefa com ID '{task_id}' não encontrada."); return False
        if not dependency_task: print(f"Erro: Tarefa dependente com ID '{dependency_id}' não encontrada."); return False
        if task_id == dependency_id: print("Erro: Uma tarefa não pode depender de si mesma."); return False
        if dependency_id in task.depends_on_ids: print(f"Tarefa '{task_id}' já depende de '{dependency_id}'."); return True
        if self._check_circular_dependency(task_id, dependency_id): print(f"Erro: Adicionar esta dependência criaria um ciclo entre '{task_id}' e '{dependency_id}'."); return False
        task.depends_on_ids.add(dependency_id)
        self.save_tasks()
        print(f"Dependência de '{dependency_task.title}' (ID: {dependency_id}) adicionada a '{task.title}' (ID: {task_id}).")
        return True

    def remove_dependency(self, task_id: str, dependency_id: str) -> bool:
        """Remove dependency_id da lista de dependências de task_id."""
        task = self.get_task_by_id(task_id)
        if not task: print(f"Erro: Tarefa com ID '{task_id}' não encontrada."); return False
        if dependency_id not in task.depends_on_ids: print(f"Erro: Tarefa '{task_id}' não depende de '{dependency_id}'. Nenhuma dependência removida."); return False
        task.depends_on_ids.remove(dependency_id)
        self.save_tasks()
        dependency_task_title = self.get_task_by_id(dependency_id).title if self.get_task_by_id(dependency_id) else dependency_id
        print(f"Dependência de '{dependency_task_title}' removida de '{task.title}' (ID: {task_id}).")
        return True

    # --- Métodos para Gerenciar Projetos/Contextos --- 

    def _add_tag_to_task(self, task_id: str, tag: str, tag_type: str) -> bool:
        """Adiciona um projeto ou contexto a uma tarefa."""
        task = self.get_task_by_id(task_id)
        if not task: print(f"Erro: Tarefa com ID '{task_id}' não encontrada."); return False
        
        normalized_tag = self._normalize_tag(tag)
        if not normalized_tag: print(f"Erro: Nome de {tag_type} inválido ou vazio."); return False
        
        tag_set = task.projects if tag_type == "projeto" else task.contexts
        if normalized_tag in tag_set: print(f"Tarefa '{task_id}' já está no {tag_type} '{normalized_tag}'."); return True
        
        tag_set.add(normalized_tag)
        self.save_tasks()
        print(f"{tag_type.capitalize()} '{normalized_tag}' adicionado à tarefa '{task.title}' (ID: {task_id}).")
        return True

    def _remove_tag_from_task(self, task_id: str, tag: str, tag_type: str) -> bool:
        """Remove um projeto ou contexto de uma tarefa."""
        task = self.get_task_by_id(task_id)
        if not task: print(f"Erro: Tarefa com ID '{task_id}' não encontrada."); return False
        
        normalized_tag = self._normalize_tag(tag)
        tag_set = task.projects if tag_type == "projeto" else task.contexts
        
        if normalized_tag not in tag_set:
            print(f"Erro: Tarefa '{task_id}' não pertence ao {tag_type} '{normalized_tag}'.")
            return False
            
        tag_set.remove(normalized_tag)
        self.save_tasks()
        print(f"{tag_type.capitalize()} '{normalized_tag}' removido da tarefa '{task.title}' (ID: {task_id}).")
        return True

    def add_project_to_task(self, task_id: str, project_name: str) -> bool:
        """Adiciona um projeto a uma tarefa."""
        return self._add_tag_to_task(task_id, project_name, "projeto")

    def remove_project_from_task(self, task_id: str, project_name: str) -> bool:
        """Remove um projeto de uma tarefa."""
        return self._remove_tag_from_task(task_id, project_name, "projeto")

    def add_context_to_task(self, task_id: str, context_name: str) -> bool:
        """Adiciona um contexto a uma tarefa."""
        return self._add_tag_to_task(task_id, context_name, "contexto")

    def remove_context_from_task(self, task_id: str, context_name: str) -> bool:
        """Remove um contexto de uma tarefa."""
        return self._remove_tag_from_task(task_id, context_name, "contexto")

    def save_tasks(self):
        """Salva o estado atual das tarefas usando o storage."""
        self.storage.save_tasks(self.tasks)

