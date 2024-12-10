# Agente SQL LangChain

Agente de IA que consulta banco de dados SQL Server usando LangChain e OpenAI.

## Funcionalidades

- Consulta preços de produtos
- Verifica estoque
- Analisa histórico de vendas
- Responde em português
- Tratamento de caracteres especiais em colunas SQL
- API REST para integração com Typebot

## Requisitos

- Python 3.8+
- SQL Server
- Driver ODBC 17 para SQL Server
- Chave API OpenAI

## Configuração

1. Clone o repositório:
```bash
git clone https://github.com/Andrejr82/agente-sql-langchain.git
cd agente-sql-langchain
```

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

## Uso Local

Execute o agente no terminal:
```bash
python agent.py
```

## API e Typebot

### Executando a API

1. Inicie o servidor:
```bash
python api.py
```

2. Acesse a documentação:
```
http://localhost:8000/docs
```

### Endpoint

POST `/consulta`
```json
{
    "pergunta": "Qual o preço do produto 661912?",
    "api_key": "sua_chave_opcional"
}
```

### Configuração no Typebot

1. No Typebot, crie um novo bot
2. Adicione um bloco "Webhook"
3. Configure o webhook:
   - URL: `http://seu-servidor/consulta`
   - Método: POST
   - Body:
   ```json
   {
       "pergunta": "{{input.message}}",
       "api_key": "sua_chave"
   }
   ```
4. Adicione um bloco de resposta para exibir o resultado

## Deploy

### Heroku
```bash
heroku create seu-app
git push heroku main
```

### Railway
```bash
railway init
railway up
```

## Segurança

- Validação de queries SQL
- Sanitização de entradas
- Tratamento de erros
- Timeout em consultas longas
- Autenticação via API key (opcional)

## Contribuição

1. Faça um Fork
2. Crie uma branch (`git checkout -b feature/sua-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona feature'`)
4. Push para a branch (`git push origin feature/sua-feature`)
5. Abra um Pull Request
