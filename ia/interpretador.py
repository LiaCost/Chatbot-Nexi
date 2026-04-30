import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def interpretar_mensagem(mensagem):
    resposta = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": """Você é um assistente de controle de estoque.
Interprete a mensagem do usuário e responda APENAS com um JSON no formato:
{
  "acao": "consultar_estoque" | "registrar_venda" | "alerta_estoque" | "consultar_fornecedor" | "historico_cliente" | "desconhecido",
  "produto": "nome do produto ou null",
  "quantidade": número ou null,
  "cliente": "nome do cliente ou null"
}
Sem explicações, apenas o JSON."""
            },
            {
                "role": "user",
                "content": mensagem
            }
        ]
    )
    return resposta.choices[0].message.content