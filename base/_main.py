# Gerar o arquivo com dados mais precisos para produção têxtil
import pandas as pd
import numpy as np
from datetime import datetime

def criar_base_dados_realista():
    """
    Cria uma base de dados realista para análise de produção têxtil e resíduos,
    baseada em estatísticas da indústria têxtil global e brasileira.
    """
    # Período de 12 meses (2023)
    meses = [f"2023-{str(i).zfill(2)}" for i in range(1, 13)]
    
    np.random.seed(42)  # Para reprodutibilidade
    
    # Capacidade de produção típica de uma tecelagem média: 100-200 toneladas/mês
    producao_base_tons = np.array([120, 130, 140, 150, 160, 170, 180, 175, 165, 155, 145, 135])
    
    # Variação sazonal e aleatória (demanda maior no meio do ano)
    producao_variacao = np.random.normal(0, 10, 12)
    producao_total_tons = np.maximum(100, producao_base_tons + producao_variacao)
    
    # Eficiência de produção: 85-95% para máquinas modernas
    eficiencia_base = np.array([85, 86, 87, 88, 89, 90, 91, 92, 91, 90, 89, 88])
    eficiencia_variacao = np.random.normal(0, 1.5, 12)
    eficiencia_percentual = np.clip(eficiencia_base + eficiencia_variacao, 80, 95)
    
    # Horas operacionais: considerando 3 turnos, com manutenção
    horas_base = np.array([720, 730, 740, 750, 760, 770, 780, 775, 765, 755, 745, 735])
    horas_variacao = np.random.normal(0, 15, 12)  # Manutenção, quebras
    horas_operacionais = np.maximum(650, horas_base + horas_variacao)
    
    # Resíduos: 8-12% da produção (pré-consumo principalmente)
    percentual_residuo = np.random.uniform(0.08, 0.12, 12)
    residuo_tons = np.round(producao_total_tons * percentual_residuo, 2)
    residuo_kg = residuo_tons * 1000  # Para compatibilidade
    
    # Eficiência em kg/h (compatibilidade)
    producao_total_kg = producao_total_tons * 1000
    eficiencia_kg_h = np.round(producao_total_kg / horas_operacionais, 2)
    
    # Quebra de resíduos
    residuo_pre_consumo_tons = np.round(residuo_tons * 0.9, 2)  # 90% pré-consumo
    residuo_pos_consumo_tons = np.round(residuo_tons * 0.1, 2)  # 10% pós-consumo
    residuo_pre_consumo_kg = residuo_pre_consumo_tons * 1000
    residuo_pos_consumo_kg = residuo_pos_consumo_tons * 1000
    
    # Custos aproximados (baseado em mercado brasileiro)
    custo_residuo_por_kg = 0.5  # R$/kg para tratamento/disposição
    custo_total_residuo = np.round(residuo_kg * custo_residuo_por_kg, 2)
    
    # Potencial de reciclagem: 60-80% dos resíduos podem ser reciclados
    potencial_reciclagem_percent = np.random.uniform(60, 80, 12)
    residuo_reciclavel_tons = np.round(residuo_tons * potencial_reciclagem_percent / 100, 2)
    residuo_reciclavel_kg = residuo_reciclavel_tons * 1000
    
    # Consumo de água e energia (aproximado)
    agua_por_ton = 100  # m³/ton produzida
    consumo_agua_m3 = np.round(producao_total_tons * agua_por_ton, 1)
    
    energia_por_ton = 2000  # kWh/ton
    consumo_energia_kwh = np.round(producao_total_tons * energia_por_ton, 1)
    
    # Criar DataFrame com colunas compatíveis e novas
    dados = {
        'Mes': meses,
        'Producao_Total_kg': producao_total_kg,
        'Eficiencia_kg_h': eficiencia_kg_h,
        'Horas_Operacionais': horas_operacionais,
        'Residuo_kg': residuo_kg,
        # Novas colunas para dados mais precisos
        'Eficiencia_Percentual': eficiencia_percentual,
        'Producao_Total_Tons': producao_total_tons,
        'Residuo_Pre_Consumo_kg': residuo_pre_consumo_kg,
        'Residuo_Pos_Consumo_kg': residuo_pos_consumo_kg,
        'Custo_Residuo_RS': custo_total_residuo,
        'Potencial_Reciclagem_Percent': potencial_reciclagem_percent,
        'Residuo_Reciclavel_kg': residuo_reciclavel_kg,
        'Consumo_Agua_m3': consumo_agua_m3,
        'Consumo_Energia_kWh': consumo_energia_kwh
    }
    
    df = pd.DataFrame(dados)
    
    return df

def gerar_excel_base_realista():
    """
    Gera um arquivo Excel com base de dados realista para análise de produção têxtil
    """
    df = criar_base_dados_realista()
    
    # Adicionar métricas calculadas
    df['Producao_Por_Hora_Tons'] = np.round(df['Producao_Total_Tons'] / df['Horas_Operacionais'], 3)
    df['Custo_Por_Ton_Produzida_RS'] = np.round(df['Custo_Residuo_RS'] / df['Producao_Total_Tons'], 2)
    df['Eficiencia_Global'] = np.round((df['Producao_Total_kg'] / (df['Producao_Total_kg'] + df['Residuo_kg'])) * 100, 2)
    
    # Salvar como Excel
    nome_arquivo = "base_residuos_textil_realista.xlsx"
    df.to_excel(nome_arquivo, index=False)
    
    print(f"Arquivo {nome_arquivo} gerado com sucesso!")
    print(f"Total produção anual: {df['Producao_Total_Tons'].sum():.1f} toneladas ({df['Producao_Total_kg'].sum():.0f} kg)")
    print(f"Total resíduos: {df['Residuo_kg'].sum():.0f} kg")
    print(f"Percentual médio de resíduos: {(df['Residuo_kg'].sum() / df['Producao_Total_kg'].sum() * 100):.1f}%")
    
    return nome_arquivo

# Executar a geração
gerar_excel_base_realista()