"""
API para integração do agente SQL com Typebot.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
from agent import main as agent_main

app = FastAPI(
    title="Agente SQL API",
    description="API para consultas SQL via LangChain",
    version="1.0.0"
)

class Query(BaseModel):
    """Modelo para receber queries do Typebot."""
    pergunta: str
    api_key: Optional[str] = None

@app.post("/consulta")
async def consulta(query: Query):
    """Endpoint para processar consultas do Typebot."""
    try:
        if not query.pergunta:
            raise HTTPException(
                status_code=400,
                detail="Pergunta não pode estar vazia"
            )

        # Aqui você pode adicionar validação da api_key

        # Processa a pergunta usando o agente
        resposta = agent_main(query.pergunta)

        return {
            "status": "success",
            "resposta": resposta
        }

    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar consulta: {str(erro)}"
        )

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)