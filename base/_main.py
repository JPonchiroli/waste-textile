# Gerar o arquivo
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def criar_base_dados_melhorada():
    """
    Cria uma base de dados mais sólida e realista para análise de produção têxtil
    """
    # Período de 12 meses (2023)
    meses = [f"2023-{str(i).zfill(2)}" for i in range(1, 13)]
    
    # Valores base mais realistas para produção têxtil
    np.random.seed(42)  # Para resultados consistentes
    
    # Horas operacionais - variação sazonal (mais horas no meio do ano)
    horas_base = np.array([680, 720, 730, 710, 690, 750, 760, 740, 720, 710, 690, 680])
    horas_variacao = np.random.normal(0, 20, 12)
    horas_operacionais = np.maximum(600, horas_base + horas_variacao)  # Mínimo de 600 horas
    
    # Eficiência - tendência de melhoria ao longo do ano
    eficiencia_base = np.array([78, 80, 82, 84, 85, 86, 87, 88, 89, 90, 91, 92])
    eficiencia_variacao = np.random.normal(0, 2, 12)
    eficiencia_kg_h = np.maximum(75, eficiencia_base + eficiencia_variacao)
    
    # Produção total = eficiência × horas operacionais
    producao_total_kg = np.round(eficiencia_kg_h * horas_operacionais, 1)
    
    # Resíduo = 10% da produção (valor comum na indústria têxtil)
    residuo_kg = np.round(producao_total_kg * 0.1, 1)
    
    # Criar DataFrame
    dados = {
        'Mes': meses,
        'Producao_Total_kg': producao_total_kg,
        'Eficiencia_kg_h': eficiencia_kg_h,
        'Horas_Operacionais': horas_operacionais,
        'Residuo_kg': residuo_kg
    }
    
    df = pd.DataFrame(dados)
    
    return df

def gerar_excel_base_solida():
    """
    Gera um arquivo Excel com base de dados sólida para análise
    """
    df = criar_base_dados_melhorada()
    
    # Adicionar algumas métricas calculadas
    df['Producao_Minima_Esperada'] = np.round(df['Producao_Total_kg'] * 0.95, 1)
    df['Producao_Maxima_Esperada'] = np.round(df['Producao_Total_kg'] * 1.05, 1)
    df['Utilizacao_Capacidade'] = np.round((df['Horas_Operacionais'] / 720) * 100, 1)  # 720h = capacidade máxima teórica
    
    # Salvar como Excel
    nome_arquivo = "base_residuos_teste.xlsx"
    df.to_excel(nome_arquivo, index=False)
    
    print(f"Arquivo {nome_arquivo} gerado com sucesso!")
    return nome_arquivo

gerar_excel_base_solida()