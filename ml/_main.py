import os
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def process_file(input_path, output_dir):
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

    # 3. Converter 'Mes' para datetime, garantindo formato AAAA-MM
    df['Mes'] = pd.to_datetime(df['Mes'], format='%Y-%m', errors='coerce')
    df = df.dropna(subset=['Mes']).sort_values('Mes').reset_index(drop=True)

    # 4. Formatar 'Mes' como string 'AAAA-MM' para exibição
    df['Mes'] = df['Mes'].dt.strftime('%Y-%m')

    if len(df) < 6:
        raise ValueError('Poucos dados para prever. Forneça pelo menos 6 meses.')

    # 5. Extrair último mês histórico
    last_date = pd.to_datetime(df['Mes'].iloc[-1])  # Converte para datetime
    start_forecast = (last_date + pd.DateOffset(months=1))

    # 6. Função para prever séries com Holt
    def forecast_series(series, periods=12):
        series = series.asfreq('MS')
        model = ExponentialSmoothing(
            series,
            trend='add',
            seasonal=None,
            initialization_method='estimated'
        )
        fit = model.fit()
        forecast = fit.forecast(periods)
        return forecast.values

    # Prever eficiência e horas operacionais
    hist_eff = pd.to_datetime(df['Mes'])  # Precisamos do índice temporal
    eff_series = pd.Series(df['Eficiencia_kg_h'].values, index=hist_eff)
    hours_series = pd.Series(df['Horas_Operacionais'].values, index=hist_eff)

    eff_forecast = forecast_series(eff_series)
    hours_forecast = forecast_series(hours_series)

    # 7. Gerar previsões mês a mês
    forecast_data = []

    for i in range(12):
        next_month = (start_forecast + pd.DateOffset(months=i)).strftime('%Y-%m')

        eff = eff_forecast[i]
        hours = hours_forecast[i]
        prod = round(eff * hours, 2)
        residuo = round(prod * 0.10, 2)

        # Intervalo de confiança (±5%)
        lower = round(prod * 0.95, 2)
        upper = round(prod * 1.05, 2)

        forecast_data.append({
            'Mes': next_month,
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
    combined_df = pd.concat([df, forecast_df], ignore_index=True)

    # 10. Salvar como Excel
    base = os.path.splitext(os.path.basename(input_path))[0]
    out_name = f"{base}_com_previsao.xlsx"
    out_path = os.path.join(output_dir, out_name)

    with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
        combined_df.to_excel(writer, sheet_name='Dados_Completos', index=False)
        forecast_df.to_excel(writer, sheet_name='Previsoes_12m', index=False)

    print(f"Arquivo com previsões salvo em: {out_path}")

    return out_path, None