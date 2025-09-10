import os
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def process_file(input_path, output_dir):
    """
    Lê um arquivo de dados, gera previsões para 12 meses, salva um Excel 
    com os resultados e cria 3 gráficos de visualização.
    """
    print('Processando arquivo:', input_path)

    # 1. Ler arquivo
    if input_path.endswith('.xlsx'):
        df = pd.read_excel(input_path, engine='openpyxl')
    elif input_path.endswith('.csv'):
        df = pd.read_csv(input_path)
    else:
        raise ValueError('Formato de arquivo não suportado')

    # 2. Validar colunas
    required_cols = ['Mes', 'Producao_Total_kg', 'Eficiencia_kg_h', 'Horas_Operacionais']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f'Coluna obrigatória não encontrada: {col}')

    # 3. Converter 'Mes' para datetime para cálculos
    df['Mes_dt'] = pd.to_datetime(df['Mes'], format='%Y-%m', errors='coerce')
    df = df.dropna(subset=['Mes_dt']).sort_values('Mes_dt').reset_index(drop=True)

    if len(df) < 6:
        raise ValueError('Poucos dados para prever. Forneça pelo menos 6 meses.')

    # 4. Extrair último mês histórico para iniciar a previsão
    last_date = df['Mes_dt'].iloc[-1]
    start_forecast = (last_date + pd.DateOffset(months=1))

    # 5. Função para prever séries com Holt-Winters
    def forecast_series(series, periods=12):
        # A frequência 'MS' significa "Month Start" (início do mês)
        series_resampled = series.asfreq('MS')
        model = ExponentialSmoothing(
            series_resampled,
            trend='add',
            seasonal=None, # Sem sazonalidade neste modelo simples
            initialization_method='estimated'
        )
        fit = model.fit()
        forecast = fit.forecast(periods)
        return forecast.values

    # 6. Preparar séries temporais para previsão
    # O índice da série DEVE ser do tipo datetime
    eff_series = pd.Series(df['Eficiencia_kg_h'].values, index=df['Mes_dt'])
    hours_series = pd.Series(df['Horas_Operacionais'].values, index=df['Mes_dt'])

    eff_forecast = forecast_series(eff_series)
    hours_forecast = forecast_series(hours_series)

    # 7. Gerar dados de previsão mês a mês
    forecast_data = []
    for i in range(12):
        next_month_dt = start_forecast + pd.DateOffset(months=i)
        next_month_str = next_month_dt.strftime('%Y-%m')
        eff = eff_forecast[i]
        hours = hours_forecast[i]
        prod = round(eff * hours, 2)
        residuo = round(prod * 0.10, 2)
        lower = round(prod * 0.95, 2)
        upper = round(prod * 1.05, 2)
        forecast_data.append({
            'Mes': next_month_str,
            'Mes_dt': next_month_dt,
            'Eficiencia_kg_h': round(eff, 2),
            'Horas_Operacionais': round(hours, 2),
            'Producao_Total_kg': prod,
            'Residuo_kg': residuo,
            'Producao_Minima_Esperada': lower,
            'Producao_Maxima_Esperada': upper
        })

    # 8. Criar DataFrame de previsões
    forecast_df = pd.DataFrame(forecast_data)

    # 9. Combinar dados originais + previsões
    # Selecionamos apenas as colunas originais para concatenar
    original_cols_for_concat = df[['Mes', 'Producao_Total_kg', 'Eficiencia_kg_h', 'Horas_Operacionais', 'Mes_dt']]
    combined_df = pd.concat([original_cols_for_concat, forecast_df], ignore_index=True)

    # 10. Salvar como Excel
    base = os.path.splitext(os.path.basename(input_path))[0]
    out_name = f"{base}_com_previsao.xlsx"
    out_path = os.path.join(output_dir, out_name)

    # Remove a coluna de data auxiliar antes de salvar
    with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
        combined_df.drop(columns=['Mes_dt']).to_excel(writer, sheet_name='Dados_Completos', index=False)
        forecast_df.drop(columns=['Mes_dt']).to_excel(writer, sheet_name='Previsoes_12m', index=False)

    # --- 11. GERAÇÃO DE GRÁFICOS (NOVA SEÇÃO) ---
    fig_paths = []
    plt.style.use('seaborn-v0_8-whitegrid') # Estilo visual dos gráficos

    # Gráfico 1: Produção Histórica vs. Previsão
    plt.figure(figsize=(14, 9))
    # Plota os dados históricos (até o último ponto dos dados originais)
    plt.plot(combined_df['Mes_dt'][:len(df)], combined_df['Producao_Total_kg'][:len(df)], marker='o', linestyle='-', label='Produção Histórica')
    # Plota a previsão (começando do último ponto histórico para criar uma linha contínua)
    plt.plot(combined_df['Mes_dt'][len(df)-1:], combined_df['Producao_Total_kg'][len(df)-1:], marker='o', linestyle='--', label='Produção Prevista')
    plt.title('Produção Total: Histórico vs. Previsão (12 Meses)', fontsize=22)
    plt.ylabel('Produção (kg)', fontsize=22)
    plt.xlabel('Mês', fontsize=22)
    plt.xticks(rotation=45, fontsize=22)
    plt.yticks(fontsize=22)
    plt.legend(fontsize=22)
    plt.tight_layout()
    fig1_path = os.path.join(output_dir, f"{base}_grafico_producao.png")
    plt.savefig(fig1_path)
    fig_paths.append(fig1_path)
    plt.close()

    # Gráfico 2: Previsão de Eficiência
    plt.figure(figsize=(14, 9))
    plt.plot(forecast_df['Mes_dt'], forecast_df['Eficiencia_kg_h'], marker='o', color='green')
    plt.title('Previsão de Eficiência (12 Meses)', fontsize=22)
    plt.ylabel('Eficiência (kg/h)', fontsize=22)
    plt.xlabel('Mês', fontsize=22)
    plt.xticks(rotation=45, fontsize=22)
    plt.yticks(fontsize=22)
    plt.tight_layout()
    fig2_path = os.path.join(output_dir, f"{base}_grafico_eficiencia.png")
    plt.savefig(fig2_path)
    fig_paths.append(fig2_path)
    plt.close()

    # Gráfico 3: Previsão de Horas Operacionais
    plt.figure(figsize=(14, 9))
    plt.plot(forecast_df['Mes_dt'], forecast_df['Horas_Operacionais'], marker='o', color='purple')
    plt.title('Previsão de Horas Operacionais (12 Meses)', fontsize=22)
    plt.ylabel('Horas', fontsize=22)
    plt.xlabel('Mês', fontsize=22)
    plt.xticks(rotation=45, fontsize=22)
    plt.yticks(fontsize=22)

    plt.tight_layout()
    fig3_path = os.path.join(output_dir, f"{base}_grafico_horas.png")
    plt.savefig(fig3_path)
    fig_paths.append(fig3_path)
    plt.close()

    print(f"Arquivo com previsões salvo em: {out_path}")
    print(f"Gráficos salvos: {fig_paths}")

    # --- 12. RETORNO CORRIGIDO ---
    # Agora retorna o caminho do Excel e a LISTA com os 3 caminhos dos gráficos.
    return out_path, fig_paths