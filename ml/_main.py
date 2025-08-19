import pandas as pd


def process_file(filepath):
    if filepath.endswith(".xlsx"):
        data = pd.read_excel(filepath)
    elif filepath.endswith(".csv"):
        data = pd.read_csv(filepath)
    else:
        raise ValueError("Formato de arquivo não suportado")

    # Exemplo de processamento: mostrar as 3 primeiras linhas
    print(data.head(3))