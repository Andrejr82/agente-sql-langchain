"""
Módulo responsável pela configuração e execução de um agente de IA
que interage com um banco de dados SQL Server usando LangChain.
"""

import os
import logging
from typing import Any, Dict, List, Tuple
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from dotenv import load_dotenv
import pyodbc  # type: ignore[import]
from langchain.agents import initialize_agent, AgentType
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from sqlalchemy.exc import SQLAlchemyError


# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constantes
MAX_TENTATIVAS = 3


def formatar_nome_coluna_sql(nome: str) -> str:
    """
    Formata o nome da coluna para uso seguro em consultas SQL Server.

    Args:
        nome: Nome da coluna

    Returns:
        str: Nome da coluna formatado com colchetes se necessário
    """
    if ' ' in nome or '%' in nome or '[' in nome or ']' in nome:
        return f"[{nome}]"
    return nome


def criar_prompt_seguro() -> str:
    """
    Cria um prompt seguro para o agente SQL com instruções específicas
    e formato de resposta padronizado.

    Returns:
        str: Template do prompt com instruções e formato de resposta
    """
    return (
        "Você é um assistente SQL especializado em consultas ao banco de dados.\n\n"
        "INSTRUÇÕES IMPORTANTES:\n"
        "Para cada pergunta, você DEVE seguir EXATAMENTE esta sequência:\n\n"
        "1. Thought: Primeiro preciso ver as tabelas disponíveis\n"
        "   Action: sql_db_list_tables\n"
        "   Action Input: none\n\n"
        "2. Thought: Agora preciso entender a estrutura das tabelas relevantes\n"
        "   Action: sql_db_schema\n"
        "   Action Input: nome_da_tabela\n\n"
        "3. Thought: Com essas informações, posso fazer a consulta\n"
        "   Action: sql_db_query\n"
        "   Action Input: sua_query_sql\n\n"
        "REGRAS IMPORTANTES:\n"
        "- Use apenas SELECT nas queries\n"
        "- Limite resultados com TOP 5\n"
        "- Explique os resultados em português\n"
        "- Siga EXATAMENTE o formato Thought/Action/Action Input\n"
        "- Para colunas com espaços ou caracteres especiais, use [nome_da_coluna]\n"
        "- Exemplo: SELECT [PREÇO 38%] FROM tabela\n\n"
        "COLUNAS PRINCIPAIS:\n"
        "- Tabela Admat_OPCOM:\n"
        "  - [CÓDIGO]: Código do produto\n"
        "  - [NOME]: Nome do produto\n"
        "  - [PREÇO 38%]: Preço do produto\n"
        "  - [FABRICANTE]: Nome do fabricante\n"
        "  - [CATEGORIA]: Categoria do produto\n"
        "  - [GRUPO]: Grupo do produto\n"
        "  - [SUBGRUPO]: Subgrupo do produto\n"
        "  - [EMBALAGEM]: Tipo de embalagem\n"
        "  - [EST# UNE]: Estoque na unidade\n"
        "  - [ULTIMA_VENDA]: Data da última venda\n"
        "  - Histórico de Vendas:\n"
        "    - [mai-23]: Vendas em Maio/2023\n"
        "    - [jun-23]: Vendas em Junho/2023\n"
        "    - [jul-23]: Vendas em Julho/2023\n"
        "    - [ago-23]: Vendas em Agosto/2023\n"
        "    - [set-23]: Vendas em Setembro/2023\n"
        "    - [out-23]: Vendas em Outubro/2023\n"
        "    - [nov-23]: Vendas em Novembro/2023\n"
        "    - [dez-23]: Vendas em Dezembro/2023\n"
        "    - [jan-24]: Vendas em Janeiro/2024\n"
        "    - [fev-24]: Vendas em Fevereiro/2024\n"
        "    - [mar-24]: Vendas em Março/2024\n"
        "    - [abr-24]: Vendas em Abril/2024\n"
        "    - [mai/24]: Vendas em Maio/2024\n\n"
        "EXEMPLOS DE PERGUNTAS E RESPOSTAS:\n"
        "1. Pergunta: 'Qual o preço do produto 661912?'\n"
        "   Query: SELECT [CÓDIGO], [NOME], [PREÇO 38%] "
        "FROM Admat_OPCOM WHERE [CÓDIGO] = 661912\n\n"
        "2. Pergunta: 'Quais produtos da categoria TECIDOS?'\n"
        "   Query: SELECT TOP 5 [CÓDIGO], [NOME], [PREÇO 38%] "
        "FROM Admat_OPCOM WHERE [CATEGORIA] = 'TECIDOS'\n\n"
        "3. Pergunta: 'Qual o estoque do produto 661912?'\n"
        "   Query: SELECT [CÓDIGO], [NOME], [EST# UNE] "
        "FROM Admat_OPCOM WHERE [CÓDIGO] = 661912\n\n"
        "4. Pergunta: 'Qual o histórico de vendas do produto 661912\n"
        "   nos últimos 3 meses?'\n"
        "   Query: SELECT [CÓDIGO], [NOME], [mar-24], [abr-24], [mai/24] "
        "FROM Admat_OPCOM WHERE [CÓDIGO] = 661912\n\n"
        "5. Pergunta: 'Quais produtos venderam mais de 100 unidades em maio/2024?'\n"
        "   Query: SELECT TOP 5 [CÓDIGO], [NOME], [mai/24] "
        "FROM Admat_OPCOM WHERE [mai/24] > 100 ORDER BY [mai/24] DESC\n\n"
        "Human: {input}\n"
        "Assistant: Vou buscar essa informação seguindo os passos necessários.\n"
        "{agent_scratchpad}"
    )


def validar_variaveis_ambiente(variaveis: List[str]) -> None:
    """
    Valida se todas as variáveis de ambiente necessárias estão configuradas.

    Args:
        variaveis: Lista de variáveis de ambiente a serem validadas

    Raises:
        EnvironmentError: Se alguma variável não estiver configurada
    """
    if not all(variaveis):
        raise EnvironmentError(
            "Todas as variáveis de ambiente devem estar configuradas no .env"
        )


def testar_conexao_banco(
    servidor: str,
    banco: str,
    usuario: str,
    senha: str
) -> bool:
    """
    Testa a conexão com o banco de dados.

    Args:
        servidor: Endereço do servidor
        banco: Nome do banco de dados
        usuario: Nome do usuário
        senha: Senha do usuário

    Returns:
        bool: True se a conexão for bem sucedida, False caso contrário
    """
    string_conexao = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={servidor};"
        f"DATABASE={banco};"
        f"UID={usuario};"
        f"PWD={senha};"
        "TrustServerCertificate=yes;"
    )

    try:
        conexao = pyodbc.connect(string_conexao)  # type: ignore[import]
        logging.info("Conexão com o banco validada com sucesso!")
        conexao.close()
        return True
    except pyodbc.Error as erro:
        logging.error("Erro na conexão com o banco: %s", erro)
        return False


def verificar_query_segura(query: str) -> Tuple[bool, str]:
    """
    Verifica se a query SQL é segura para execução.

    Args:
        query: Query SQL a ser verificada

    Returns:
        Tuple[bool, str]: (True, mensagem) se a query for segura,
                         (False, mensagem) caso contrário
    """
    operacoes_proibidas: Dict[str, List[str]] = {
        'modificacao': ['DELETE', 'DROP', 'UPDATE', 'INSERT'],
        'estrutura': ['ALTER', 'CREATE', 'RENAME'],
        'execucao': ['EXEC', 'EXECUTE', 'SP_', 'XP_'],
        'acesso': ['GRANT', 'REVOKE', 'DENY'],
        'sistema': ['SHUTDOWN', 'KILL', 'BACKUP']
    }

    query_upper = query.upper()
    for categoria, comandos in operacoes_proibidas.items():
        for comando in comandos:
            if comando in query_upper:
                return False, f"Operação proibida: {comando} ({categoria})"
    return True, "Query válida"


def validar_entrada(texto: str) -> str:
    """
    Valida e sanitiza a entrada do usuário.

    Args:
        texto: Texto a ser validado

    Returns:
        str: Texto sanitizado
    """
    caracteres_proibidos = [';', '--', '/*', '*/', 'xp_', 'sp_']
    texto_validado = texto
    for char in caracteres_proibidos:
        texto_validado = texto_validado.replace(char, '')
    return texto_validado


def formatar_resposta(resposta: Any) -> str:
    """
    Formata a resposta do agente para melhor legibilidade.

    Args:
        resposta: Resposta do agente

    Returns:
        str: Resposta formatada
    """
    if isinstance(resposta, dict):
        output = resposta.get("output", "")
        # Remove informações técnicas desnecessárias
        output = output.replace("Thought:", "\n📝 Análise:")
        output = output.replace("Action:", "\n🔍 Ação:")
        output = output.replace("Action Input:", "\n💻 Comando:")
        output = output.replace("Observation:", "\n📊 Resultado:")
        output = output.replace("Final Answer:", "\n✨ Resposta Final:")
        output = output.replace("Error:", "\n❌ Erro:")

        # Adiciona separadores para melhor legibilidade
        output = output.replace("\n\n", "\n")
        output = output.replace("```sql", "\n```sql")
        output = output.replace("```", "```\n")

        return output
    return str(resposta)


def executar_com_timeout(agent: Any, entrada: str, timeout: int = 30) -> Any:
    """
    Executa a consulta com um timeout.

    Args:
        agent: Agente LangChain
        entrada: Pergunta do usuário
        timeout: Tempo máximo em segundos

    Returns:
        Any: Resposta do agente ou mensagem de timeout
    """
    with ThreadPoolExecutor() as executor:
        future = executor.submit(
            agent.invoke,
            {"input": entrada},
            handle_parsing_errors=True
        )
        try:
            return future.result(timeout=timeout)
        except FuturesTimeoutError:
            return "Tempo limite excedido. Por favor, reformule sua pergunta."


def executar_query_com_retry(
    db: SQLDatabase,
    query: str,
    max_tentativas: int = MAX_TENTATIVAS
) -> Any:
    """
    Executa uma query SQL com tentativas em caso de erro.

    Args:
        db: Instância do SQLDatabase
        query: Query SQL a ser executada
        max_tentativas: Número máximo de tentativas

    Returns:
        Any: Resultado da query ou mensagem de erro
    """
    erro = None
    for tentativa in range(max_tentativas):
        try:
            return db.run(query)
        except SQLAlchemyError as e:
            erro = e
            logging.warning(
                "Tentativa %d de %d falhou: %s",
                tentativa + 1,
                max_tentativas,
                str(e)
            )
            if "invalid column name" in str(e).lower():
                # Tenta corrigir nomes de colunas
                query = query.replace('"', '[').replace('"', ']')
                continue
    return f"Erro após {max_tentativas} tentativas: {erro}"


def main() -> None:
    """Função principal que configura e executa o agente."""
    # Carregamento de configurações
    load_dotenv()

    # Variáveis de ambiente
    db_server = os.getenv("DB_SERVER", "")
    db_database = os.getenv("DB_DATABASE", "")
    db_user = os.getenv("DB_USER", "")
    db_password = os.getenv("DB_PASSWORD", "")
    openai_api_key = os.getenv("OPENAI_API_KEY", "")

    # Validação das variáveis
    validar_variaveis_ambiente(
        [db_server, db_database, db_user, db_password, openai_api_key]
    )

    # Teste de conexão
    if not testar_conexao_banco(db_server, db_database, db_user, db_password):
        raise ConnectionError("Falha na conexão com o banco de dados")

    # Configuração do OpenAI
    os.environ["OPENAI_API_KEY"] = openai_api_key
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

    # String de conexão para SQLAlchemy
    string_conexao_db = (
        "mssql+pyodbc:///?odbc_connect=" +
        quote_plus(
            f"DRIVER=ODBC Driver 17 for SQL Server;"
            f"SERVER={db_server};"
            f"DATABASE={db_database};"
            f"UID={db_user};PWD={db_password};"
            "TrustServerCertificate=yes"
        )
    )

    try:
        # Configuração do banco de dados
        db = SQLDatabase.from_uri(
            string_conexao_db,
            include_tables=['Admat_OPCOM', 'Opcom'],  # Especifica as tabelas permitidas
            sample_rows_in_table_info=3
        )

        # Configuração do toolkit
        toolkit = SQLDatabaseToolkit(db=db, llm=llm)

        # Configuração do agente
        agent = initialize_agent(
            tools=toolkit.get_tools(),
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
            early_stopping_method="generate",
            agent_kwargs={
                "prefix": criar_prompt_seguro()
            }
        )

        # Loop principal
        print("\n🤖 Assistente SQL iniciado! Digite 'sair' para encerrar.\n")

        while True:
            try:
                # Entrada do usuário
                pergunta = input("\n💭 Sua pergunta: ").strip()

                if pergunta.lower() in ['sair', 'exit', 'quit']:
                    print("\n👋 Até logo!")
                    break

                if not pergunta:
                    continue

                # Validação da entrada
                pergunta_validada = validar_entrada(pergunta)

                # Execução com timeout
                resposta = executar_com_timeout(agent, pergunta_validada)

                # Formatação e exibição da resposta
                print("\n" + formatar_resposta(resposta))

            except KeyboardInterrupt:
                print("\n\n⚠️ Operação cancelada pelo usuário.")
                break

            except (SQLAlchemyError, ValueError, RuntimeError) as erro:
                logging.error("Erro inesperado: %s", erro)
                print(f"\n❌ Erro: {str(erro)}")
                print("Por favor, tente novamente com uma pergunta diferente.")

    except Exception as erro:
        logging.error("Erro fatal: %s", erro)
        raise


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Programa encerrado pelo usuário.")
    except (SQLAlchemyError, ValueError, RuntimeError) as erro:
        logging.error("Erro fatal: %s", erro)
        print(f"\n❌ Erro fatal: {str(erro)}")
        print("O programa será encerrado.")
