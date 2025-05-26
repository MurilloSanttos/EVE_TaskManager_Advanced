# EVE - Assistente Pessoal de Tarefas

EVE é uma assistente virtual de linha de comando (CLI) focada em gerenciamento pessoal de tarefas. Desenvolvida em Python, ela permite criar, listar, editar, excluir e gerenciar o status de suas tarefas de forma organizada e eficiente.

## Funcionalidades Implementadas

*   **Criação de Tarefas:** Adicione novas tarefas com título, descrição, data de vencimento, prioridade e categoria.
*   **Listagem Flexível:** Visualize suas tarefas com filtros dinâmicos por status (Pendente, Concluída), prioridade (Alta, Média, Baixa), categoria ou data de vencimento (vencidas, hoje, futuras).
*   **Edição Detalhada:** Atualize qualquer campo de uma tarefa existente.
*   **Exclusão Segura:** Remova tarefas com confirmação prévia (ou use `-y` para pular).
*   **Gerenciamento de Status:** Marque tarefas como "Concluída" (registrando a data) ou reverta para "Pendente" (desfazer).
*   **Persistência:** As tarefas são salvas automaticamente em um arquivo JSON (`storage/tasks.json`) para que você não perca seus dados.
*   **Interface de Linha de Comando (CLI):** Interaja com a EVE usando comandos simples e intuitivos.

## Estrutura do Projeto

O projeto está organizado de forma modular para facilitar a manutenção e futuras expansões:

```
eve_assistant/
├── core/                 # Lógica principal da aplicação
│   ├── __init__.py
│   ├── task.py           # Define a classe Task (Tarefa)
│   └── task_manager.py   # Gerencia as operações CRUD das tarefas
├── storage/              # Módulos relacionados ao armazenamento de dados
│   ├── __init__.py
│   └── file_storage.py   # Implementa a persistência em arquivo JSON
│   └── tasks.json        # Arquivo onde as tarefas são salvas (criado automaticamente)
├── cli/                  # Interface de linha de comando
│   ├── __init__.py
│   └── interface.py      # Define os comandos da CLI e a interação com o usuário
├── main.py               # Ponto de entrada da aplicação
└── README.md             # Este arquivo
```

## Requisitos

*   Python 3.11 ou superior.

## Instalação e Execução

1.  **Clone o repositório (ou copie os arquivos):**
    ```bash
    git clone https://github.com/MurilloSanttos/EVE_TaskManager_Advanced.git
    cd eve_assistant
    ```
    Certifique-se de que todos os arquivos e diretórios listados na estrutura do projeto estejam presentes.

2.  **Execute a aplicação:**
    Navegue até o diretório raiz do projeto (`eve_assistant`) e use o Python para executar o `main.py` seguido do comando desejado:
    ```bash
    cd /path/to/eve_assistant
    python3.11 main.py <comando> [opções]
    ```
    Para facilitar, você pode criar um alias ou adicionar o diretório ao seu PATH.

## Como Usar (Comandos da CLI)

O ponto de entrada é `main.py`. Use `python3.11 main.py --help` para ver todos os comandos e opções.

**Nome do programa para a CLI:** `eve` (definido no `argparse`)

**Exemplos:**

*   **Adicionar uma tarefa:**
    ```bash
    # Adicionar com todos os detalhes
    python3.11 main.py add --title "Preparar apresentação" --description "Criar slides para reunião de sexta" --due-date "2025-06-10" --priority Alta --category Trabalho

    # Adicionar tarefa simples (prioridade Média e categoria Geral por padrão)
    python3.11 main.py add --title "Ligar para o banco"

    # Adicionar com descrição vazia explicitamente
    python3.11 main.py add --title "Agendar médico" --description ""
    ```

*   **Listar tarefas:**
    ```bash
    # Listar todas as tarefas
    python3.11 main.py list

    # Listar tarefas pendentes
    python3.11 main.py list --status Pendente

    # Listar tarefas de trabalho com prioridade alta
    python3.11 main.py list --category Trabalho --priority Alta

    # Listar tarefas vencidas
    python3.11 main.py list --due vencidas
    ```

*   **Editar uma tarefa (substitua `<ID_DA_TAREFA>` pelo ID real):**
    ```bash
    # Ver a tarefa primeiro para pegar o ID
    python3.11 main.py list

    # Editar prioridade e data de vencimento
    python3.11 main.py edit <ID_DA_TAREFA> --priority Baixa --due-date 2025-06-15

    # Limpar a descrição
    python3.11 main.py edit <ID_DA_TAREFA> --description ""

    # Remover a data de vencimento
    python3.11 main.py edit <ID_DA_TAREFA> --due-date N/A
    ```

*   **Marcar como concluída:**
    ```bash
    python3.11 main.py complete <ID_DA_TAREFA>
    ```

*   **Desfazer conclusão (marcar como pendente):**
    ```bash
    python3.11 main.py undo <ID_DA_TAREFA>
    ```

*   **Excluir uma tarefa:**
    ```bash
    # Excluir com confirmação (será perguntado s/N)
    python3.11 main.py delete <ID_DA_TAREFA>

    # Excluir diretamente sem confirmação
    python3.11 main.py delete <ID_DA_TAREFA> --yes
    ```

## Armazenamento de Dados

As tarefas são armazenadas no arquivo `storage/tasks.json`. Este arquivo é criado e atualizado automaticamente. Você pode fazer backup deste arquivo se desejar.

## Futuras Melhorias

*   **Banco de Dados:** Substituir o armazenamento em JSON por um banco de dados local como SQLite para melhor performance e escalabilidade.
*   **Interface Gráfica (GUI):** Desenvolver uma interface gráfica para uma experiência de usuário mais visual.
*   **Lembretes/Notificações:** Adicionar funcionalidades de lembrete para datas de vencimento.
*   **Subtarefas:** Permitir a criação de subtarefas vinculadas a uma tarefa principal.
*   **Testes Unitários:** Implementar uma suíte de testes unitários mais robusta.

