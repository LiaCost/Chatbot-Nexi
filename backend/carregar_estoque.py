import openpyxl

def carregar_estoque():
    wb = openpyxl.load_workbook("pivot (5).xlsx")
    ws = wb.active

    estoque = {}

    for row in ws.iter_rows(min_row=3, values_only=True):
        descricao = row[0]
        codigo = row[2]
        quantidade = row[6]
        estoque_minimo = row[7]
        unidade = row[5]
        familia = row[1]

        if codigo and descricao:
            estoque[codigo] = {
                "nome": descricao,
                "familia": familia,
                "quantidade": quantidade,
                "estoque_minimo": estoque_minimo,
                "unidade": unidade
            }

    return estoque

# Teste
estoque = carregar_estoque()
print(f"Total de produtos carregados: {len(estoque)}")
print(estoque["PRD00017"])