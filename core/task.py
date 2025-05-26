# -*- coding: utf-8 -*-
"""Módulo contendo a classe Task para representar uma tarefa com funcionalidades avançadas."""

import datetime
import uuid
from typing import List, Optional, Set, Any # Usar Set para IDs de dependência e grupos

class Task:
    """Representa uma tarefa no sistema EVE, com suporte a funcionalidades avançadas.

    Attributes:
        task_id (str): Identificador único da tarefa.
        title (str): Título da tarefa (obrigatório).
        description (str): Descrição detalhada da tarefa.
        due_date (datetime.date | None): Data de vencimento da tarefa.
        priority (str): Prioridade da tarefa ("Alta", "Média", "Baixa").
        category (str): Categoria geral da tarefa (ex: "Trabalho", "Pessoal").
        status (str): Status atual da tarefa ("Pendente", "Concluída").
        creation_date (datetime.datetime): Data e hora de criação da tarefa.
        completion_date (datetime.datetime | None): Data e hora de conclusão.
        # Novos atributos para funcionalidades avançadas
        eisenhower_quadrant (str | None): Quadrante da Matriz de Eisenhower.
        depends_on_ids (Set[str]): Conjunto de IDs de tarefas das quais esta tarefa depende.
        # blocks_ids (Set[str]): Conjunto de IDs de tarefas que dependem desta (gerenciado pelo TaskManager).
        projects (Set[str]): Conjunto de nomes de projetos aos quais a tarefa pertence.
        contexts (Set[str]): Conjunto de nomes de contextos aos quais a tarefa pertence.
    """

    VALID_PRIORITIES = ["Alta", "Média", "Baixa"]
    VALID_STATUSES = ["Pendente", "Concluída"]
    # Quadrantes da Matriz de Eisenhower
    EISENHOWER_QUADRANTS = {
        "Q1": "Urgente e Importante",
        "Q2": "Importante, mas Não Urgente",
        "Q3": "Urgente, mas Não Importante",
        "Q4": "Nem Urgente Nem Importante",
    }
    VALID_EISENHOWER_KEYS = list(EISENHOWER_QUADRANTS.keys()) + [None] # Permite não classificar

    def __init__(self, title: str, description: str = "", due_date_str: str | None = None,
                 priority: str = "Média", category: str = "Geral", status: str = "Pendente",
                 task_id: str | None = None, creation_date: datetime.datetime | None = None,
                 completion_date: datetime.datetime | None = None,
                 # Novos args
                 eisenhower_quadrant: str | None = None,
                 depends_on_ids: Optional[List[str] | Set[str]] = None, # Aceita lista ou set
                 projects: Optional[List[str] | Set[str]] = None,
                 contexts: Optional[List[str] | Set[str]] = None):
        """Inicializa uma nova instância de Tarefa.

        Args:
            # ... (argumentos anteriores) ...
            eisenhower_quadrant: Quadrante da matriz (Q1, Q2, Q3, Q4) ou None.
            depends_on_ids: Lista ou Set de IDs de tarefas predecessoras.
            projects: Lista ou Set de nomes de projetos.
            contexts: Lista ou Set de nomes de contextos.

        Raises:
            ValueError: Se dados inválidos forem fornecidos (título, prioridade, status, data, quadrante).
        """
        # Validações básicas
        if not title:
            raise ValueError("O título da tarefa não pode ser vazio.")
        if priority not in self.VALID_PRIORITIES:
            raise ValueError(f"Prioridade inválida: {priority}. Use uma de {self.VALID_PRIORITIES}")
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Status inválido: {status}. Use um de {self.VALID_STATUSES}")
        if eisenhower_quadrant is not None and eisenhower_quadrant not in self.EISENHOWER_QUADRANTS:
             # Permite None, mas se fornecido, deve ser uma chave válida (Q1-Q4)
             valid_keys_str = ", ".join(self.EISENHOWER_QUADRANTS.keys())
             raise ValueError(f"Quadrante Eisenhower inválido: {eisenhower_quadrant}. Use um de {valid_keys_str} ou deixe em branco.")

        # Atributos básicos
        self.task_id = task_id if task_id else str(uuid.uuid4())
        self.title = title
        self.description = description
        self.priority = priority
        self.category = category
        self.status = status
        self.creation_date = creation_date if creation_date else datetime.datetime.now()
        self.completion_date = completion_date

        # Processa data de vencimento
        self.due_date = None
        if due_date_str:
            try:
                self.due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Formato de data inválido. Use AAAA-MM-DD.")

        # Ajusta data de conclusão com base no status inicial
        if self.status == "Concluída" and self.completion_date is None:
            self.completion_date = datetime.datetime.now()
        elif self.status == "Pendente":
            self.completion_date = None

        # Novos atributos (inicializa como sets vazios se None)
        self.eisenhower_quadrant = eisenhower_quadrant
        self.depends_on_ids = set(depends_on_ids) if depends_on_ids else set()
        self.projects = set(projects) if projects else set()
        self.contexts = set(contexts) if contexts else set()

    def mark_complete(self):
        """Marca a tarefa como concluída e registra a data de conclusão."""
        # Validação de dependências deve ser feita no TaskManager antes de chamar este método
        if self.status == "Pendente":
            self.status = "Concluída"
            self.completion_date = datetime.datetime.now()

    def mark_pending(self):
        """Marca a tarefa como pendente e remove a data de conclusão."""
        if self.status == "Concluída":
            self.status = "Pendente"
            self.completion_date = None

    def update(self, **updates: Any):
        """Atualiza os atributos da tarefa com base nos argumentos fornecidos.

        Args:
            updates: Dicionário chave-valor com os atributos a serem atualizados.
                     Campos suportados: title, description, due_date_str, priority,
                     category, status, eisenhower_quadrant, depends_on_ids,
                     projects, contexts.
                     Para listas/sets (depends_on_ids, projects, contexts), passar a nova lista/set completo.

        Raises:
            ValueError: Se algum dos novos valores for inválido.
        """
        if "title" in updates:
            title = updates["title"]
            if not title:
                raise ValueError("O título da tarefa não pode ser vazio.")
            self.title = title
        if "description" in updates:
            # Permite string vazia para limpar descrição
            self.description = updates["description"]
        if "due_date_str" in updates:
            due_date_str = updates["due_date_str"]
            if due_date_str == "" or due_date_str is None or str(due_date_str).upper() == "N/A":
                self.due_date = None
            else:
                try:
                    self.due_date = datetime.datetime.strptime(str(due_date_str), "%Y-%m-%d").date()
                except ValueError:
                    raise ValueError("Formato de data inválido. Use AAAA-MM-DD ou N/A para remover.")
        if "priority" in updates:
            priority = updates["priority"]
            if priority not in self.VALID_PRIORITIES:
                raise ValueError(f"Prioridade inválida: {priority}. Use uma de {self.VALID_PRIORITIES}")
            self.priority = priority
        if "category" in updates:
            self.category = updates["category"]
        if "status" in updates:
            status = updates["status"]
            if status not in self.VALID_STATUSES:
                raise ValueError(f"Status inválido: {status}. Use um de {self.VALID_STATUSES}")
            # Atualiza status e data de conclusão de forma consistente
            if status == "Concluída" and self.status == "Pendente":
                # A validação de dependência deve ocorrer ANTES de chamar update com status="Concluída"
                self.mark_complete()
            elif status == "Pendente" and self.status == "Concluída":
                self.mark_pending()
            # else: self.status = status # Caso não haja mudança ou seja definição inicial

        # Atualização dos novos campos
        if "eisenhower_quadrant" in updates:
            quadrant = updates["eisenhower_quadrant"]
            # Permite definir como None para remover a classificação
            if quadrant is not None and quadrant not in self.EISENHOWER_QUADRANTS:
                 valid_keys_str = ", ".join(self.EISENHOWER_QUADRANTS.keys())
                 raise ValueError(f"Quadrante Eisenhower inválido: {quadrant}. Use um de {valid_keys_str} ou deixe em branco/None.")
            self.eisenhower_quadrant = quadrant
        if "depends_on_ids" in updates:
            # Espera receber um set ou lista de IDs válidos (validação de existência no TaskManager)
            self.depends_on_ids = set(updates["depends_on_ids"] or [])
        if "projects" in updates:
            self.projects = set(updates["projects"] or [])
        if "contexts" in updates:
            self.contexts = set(updates["contexts"] or [])

    def to_dict(self) -> dict:
        """Converte a tarefa para um dicionário serializável."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "priority": self.priority,
            "category": self.category,
            "status": self.status,
            "creation_date": self.creation_date.isoformat(),
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
            # Novos campos (converte sets para listas para JSON)
            "eisenhower_quadrant": self.eisenhower_quadrant,
            "depends_on_ids": list(self.depends_on_ids),
            "projects": list(self.projects),
            "contexts": list(self.contexts),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Cria uma instância de Tarefa a partir de um dicionário."""
        # Usa .get para compatibilidade com tarefas salvas anteriormente sem os novos campos
        return cls(
            task_id=data.get("task_id"),
            title=data["title"], # Título é essencial
            description=data.get("description", ""),
            due_date_str=data.get("due_date"),
            priority=data.get("priority", "Média"),
            category=data.get("category", "Geral"),
            status=data.get("status", "Pendente"),
            creation_date=datetime.datetime.fromisoformat(data["creation_date"]) if data.get("creation_date") else None,
            completion_date=datetime.datetime.fromisoformat(data["completion_date"]) if data.get("completion_date") else None,
            # Novos campos
            eisenhower_quadrant=data.get("eisenhower_quadrant"), # Será None se não existir
            depends_on_ids=data.get("depends_on_ids", []), # Usa lista vazia como default
            projects=data.get("projects", []),
            contexts=data.get("contexts", []),
        )

    def __str__(self) -> str:
        """Retorna uma representação em string da tarefa, incluindo novos campos."""
        due_date_str = self.due_date.strftime("%d/%m/%Y") if self.due_date else "N/A"
        status_str = f"{self.status}"
        if self.status == "Concluída" and self.completion_date:
            status_str += f" em {self.completion_date.strftime('%d/%m/%Y %H:%M')}"

        eisenhower_str = f"  Matriz: {self.eisenhower_quadrant} ({self.EISENHOWER_QUADRANTS.get(self.eisenhower_quadrant, 	'Não classificado')})\n" if self.eisenhower_quadrant else ""
        depends_str = f"  Depende de: {', '.join(self.depends_on_ids)}\n" if self.depends_on_ids else ""
        projects_str = f"  Projetos: {', '.join(self.projects)}\n" if self.projects else ""
        contexts_str = f"  Contextos: {', '.join(self.contexts)}\n" if self.contexts else ""

        return (
            f"ID: {self.task_id}\n"
            f"  Título: {self.title}\n"
            f"  Status: {status_str}\n"
            f"  Prioridade: {self.priority}\n"
            f"  Categoria: {self.category}\n"
            f"  Vencimento: {due_date_str}\n"
            f"{eisenhower_str}"
            f"{depends_str}"
            f"{projects_str}"
            f"{contexts_str}"
            f"  Descrição: {self.description or 'Nenhuma'}"
        )

    def __repr__(self) -> str:
        """Retorna uma representação detalhada do objeto Tarefa."""
        return (
            f"Task(task_id=	'{self.task_id}	', title=	'{self.title}	', "
            f"status=	'{self.status}	', priority=	'{self.priority}	', "
            f"due_date=	'{self.due_date}	', category=	'{self.category}	', "
            f"eisenhower=	'{self.eisenhower_quadrant}	', depends_on={len(self.depends_on_ids)}, "
            f"projects={len(self.projects)}, contexts={len(self.contexts)})"
        )


