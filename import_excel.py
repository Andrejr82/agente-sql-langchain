"""
Importa dados do arquivo Admat em Excel para um banco de dados SQL Server.
"""
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os


def importar_excel_para_sql():
    # Carrega variáveis de ambiente
    load_dotenv()

    # Configurações do banco
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_DATABASE")
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    # Lê o arquivo Excel Admat
    df = pd.read_excel('Admat.xlsx')

    # Cria string de conexão
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "TrustServerCertificate=yes"
    )

    # Cria engine SQLAlchemy
    quoted = quote_plus(conn_str)
    engine = create_engine(f'mssql+pyodbc:///?odbc_connect={quoted}')

    # Importa dados para SQL Server
    df.to_sql(
        'Admat',
        engine,
        if_exists='append',
        index=False,
        schema='dbo'
    )

    print("Dados do Admat importados com sucesso!")


if __name__ == "__main__":
    importar_excel_para_sql()
