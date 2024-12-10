import pandas as pd
import pyodbc
import os

# Configurações do banco de dados
DB_SERVER = os.getenv("DB_SERVER", "FAMILIA\\SQLJR")
DB_DATABASE = os.getenv("DB_DATABASE", "Projeto_Opcom")
DB_USER = os.getenv("DB_USER", "AgenteVirtual")
DB_PASSWORD = os.getenv("DB_PASSWORD", "cacula123")

# Conexão com o banco de dados


def conectar_banco():
    conn_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_SERVER};DATABASE={DB_DATABASE};UID={DB_USER};PWD={DB_PASSWORD}"
    return pyodbc.connect(conn_string)

# Função para obter as colunas existentes na tabela


def obter_colunas_tabela(cursor, tabela):
    query = f"""
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = '{tabela}'
    """
    cursor.execute(query)
    colunas = [row[0] for row in cursor.fetchall()]
    return colunas

# Função para adicionar colunas ausentes na tabela


def adicionar_colunas_ausentes(cursor, tabela, colunas_ausentes):
    for coluna in colunas_ausentes:
        # Ajuste o tipo de dado conforme necessário
        query = f"ALTER TABLE {tabela} ADD [{coluna}] NVARCHAR(MAX)"
        cursor.execute(query)
        print(f"Coluna '{coluna}' adicionada à tabela '{tabela}'.")

# Função para atualizar ou inserir os dados


def atualizar_dados_tabela(planilha_path, tabela):
    # Verificar se o arquivo da planilha existe
    if not os.path.isfile(planilha_path):
        raise FileNotFoundError(
            f"O arquivo da planilha não foi encontrado: {planilha_path}")

    # Ler os dados da planilha
    df = pd.read_excel(planilha_path)
    colunas_planilha = df.columns.tolist()

    # Conectar ao banco de dados
    conn = conectar_banco()
    cursor = conn.cursor()

    # Obter colunas existentes na tabela
    colunas_tabela = obter_colunas_tabela(cursor, tabela)

    # Verificar colunas ausentes e adicioná-las
    colunas_ausentes = [col for col in colunas_planilha if col not in colunas_tabela]
    if colunas_ausentes:
        adicionar_colunas_ausentes(cursor, tabela, colunas_ausentes)

    # Inserir ou atualizar os dados
    for _, row in df.iterrows():
        codigo = row['CÓDIGO']  # Identificador único
        valores = tuple(row[col] for col in colunas_planilha)

        # Verificar se o registro já existe
        query_verificar = f"SELECT COUNT(*) FROM {tabela} WHERE CÓDIGO = ?"
        cursor.execute(query_verificar, (codigo,))
        existe = cursor.fetchone()[0]

        if existe:
            # Atualizar o registro
            set_clause = ", ".join(
                [f"[{col}] = ?" for col in colunas_planilha if col != "CÓDIGO"])
            query_atualizar = f"UPDATE {tabela} SET {set_clause} WHERE CÓDIGO = ?"
            cursor.execute(query_atualizar, *valores[1:], codigo)
            print(f"Registro com CÓDIGO = {codigo} atualizado.")
        else:
            # Inserir novo registro
            colunas_str = ", ".join([f"[{col}]" for col in colunas_planilha])
            placeholders = ", ".join(["?" for _ in colunas_planilha])
            query_inserir = f"INSERT INTO {tabela} ({colunas_str}) VALUES ({placeholders})"
            cursor.execute(query_inserir, valores)
            print(f"Registro com CÓDIGO = {codigo} inserido.")

    # Commitar as alterações e fechar a conexão
    conn.commit()
    conn.close()
    print("Dados atualizados com sucesso!")


# Caminho para a planilha
planilha_path = r"C:\Users\andre\OneDrive\Desktop\Admat.xlsx"
tabela = "admat"

# Atualizar a tabela
try:
    atualizar_dados_tabela(planilha_path, tabela)
except FileNotFoundError as e:
    print(e)
except Exception as e:
    print(f"Ocorreu um erro: {e}")
