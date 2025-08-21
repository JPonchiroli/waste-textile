import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Evita problemas com GUI
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def process_file(input_path, output_dir):
    print('Processando arquivo:', input_path)

    # 1) Ler arquivo
    if input_path.endswith('.xlsx'):
        df_local = pd.read_excel(input_path)
    elif input_path.endswith('.csv'):
        df_local = pd.read_csv(input_path)
    else:
        raise ValueError('Formato de arquivo nao suportado')

    print('Arquivo carregado')

    # 2) Normalizar colunas esperadas
    if 'Mes' not in df_local.columns or 'Producao_Total_kg' not in df_local.columns:
        raise ValueError('Colunas obrigatorias nao encontradas: Mes e Producao_Total_kg')

    # 3) Preparar datas e ordenar
    df_local['Mes'] = pd.to_datetime(df_local['Mes'], format='%Y-%m', errors='coerce')
    df_local = df_local.dropna(subset=['Mes'])
    df_local = df_local.sort_values('Mes')

    # 4) Série mensal
    series = df_local.set_index('Mes')['Producao_Total_kg'].asfreq('MS')
    series = series.dropna()

    if len(series) < 6:
        raise ValueError('Poucos dados para prever. Forneca pelo menos 6 meses.')

    # 5) Modelo Holt (trend, sem sazonalidade)
    model = ExponentialSmoothing(series, trend='add', seasonal=None, initialization_method='estimated')
    fit = model.fit()

    # 6) Previsão 12 meses
    forecast = fit.forecast(12)

    # 7) Intervalos de confiança
    resid_std = fit.resid.dropna().std()
    fcst_df = pd.DataFrame({
        'Mes': forecast.index,
        'Producao_Prevista_kg': forecast.values
    })
    fcst_df['Lower'] = fcst_df['Producao_Prevista_kg'] - 1.96 * resid_std
    fcst_df['Upper'] = fcst_df['Producao_Prevista_kg'] + 1.96 * resid_std

    # 8) Salvar CSV
    base = os.path.splitext(os.path.basename(input_path))[0]
    out_name = base + '_previsao_12m.csv'
    out_path = os.path.join(output_dir, out_name)
    fcst_df.to_csv(out_path, index=False)

    # 9) Salvar gráfico
    plt.figure(figsize=(10, 5))
    sns.lineplot(x=series.index, y=series.values, label='Historico')
    sns.lineplot(x=forecast.index, y=forecast.values, label='Previsao')
    plt.fill_between(forecast.index, fcst_df['Lower'], fcst_df['Upper'], color='orange', alpha=0.2, label='Intervalo ~95%')
    plt.title('Producao Total (kg) - Historico e Previsao (12 meses)')
    plt.xlabel('Mes')
    plt.ylabel('kg')
    plt.legend()
    plt.tight_layout()

    fig_name = base + '_previsao_12m.png'
    fig_path = os.path.join(output_dir, fig_name)
    plt.savefig(fig_path, dpi=150)
    plt.close()

    return out_path, fig_path