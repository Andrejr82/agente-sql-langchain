import pyodbc
import os
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

DB_SERVER = os.getenv("DB_SERVER")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

connection_string = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={DB_SERVER};"
    f"DATABASE={DB_DATABASE};"
    f"UID={DB_USER};"
    f"PWD={DB_PASSWORD};"
    "TrustServerCertificate=yes"
)

try:
    connection = pyodbc.connect(connection_string)
    print("Conexão bem-sucedida com o banco de dados!")
    connection.close()
except Exception as e:
    print(f"Erro ao conectar ao banco de dados: {e}")
