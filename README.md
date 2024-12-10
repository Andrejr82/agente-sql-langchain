# Agente SQL LangChain

Agente de IA que consulta banco de dados SQL Server usando LangChain e OpenAI.

## Funcionalidades

- Consulta preços de produtos
- Verifica estoque
- Analisa histórico de vendas
- Responde em português
- Tratamento de caracteres especiais em colunas SQL

## Requisitos

- Python 3.8+
- SQL Server
- Driver ODBC 17 para SQL Server
- Chave API OpenAI

## Configuração

1. Clone o repositório
2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure o arquivo `.env`:
```env
DB_SERVER=seu_servidor
DB_DATABASE=seu_banco
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
OPENAI_API_KEY=sua_chave_api
```

## Uso

Execute o agente:
```bash
python agent.py
```

## Integração com Typebot

Para configurar no Typebot:

1. Deploy da API
2. Configure webhook no Typebot
3. Adicione autenticação
4. Configure respostas

## Segurança

- Validação de queries SQL
- Sanitização de entradas
- Tratamento de erros
- Timeout em consultas longas
