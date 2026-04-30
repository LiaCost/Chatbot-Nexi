from dotenv import load_dotenv
load_dotenv()

from ia.interpretador import interpretar_mensagem

mensagens = [
    "Quantos cadernos temos no estoque?",
    "Registrar venda de 3 canetas para João",
    "Quais produtos estão acabando?",
    "Quem fornece o produto arroz?"
]

for msg in mensagens:
    print(f"Mensagem: {msg}")
    print(f"Resposta: {interpretar_mensagem(msg)}")
    print("---")