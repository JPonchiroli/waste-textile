# Atualiza o script: usa Holt (sem sazonalidade), adiciona salvamento do CSV e gráfico, com checagens básicas
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# Função atualizada para processar arquivo e prever 12 meses com Holt (trend apenas)
def process_file(filepath):
    # 1) Ler arquivo
    if filepath.endswith('.xlsx'):
        df_local = pd.read_excel(filepath)
    elif filepath.endswith('.csv'):
        df_local = pd.read_csv(filepath)
    else:
        raise ValueError('Formato de arquivo nao suportado')

    print('Arquivo carregado')

    # 2) Normalizar colunas esperadas
    # Espera colunas: Mes, Producao_Total_kg
    if 'Mes' not in df_local.columns or 'Producao_Total_kg' not in df_local.columns:
        raise ValueError('Colunas obrigatorias nao encontradas: Mes e Producao_Total_kg')

    # 3) Preparar datas e ordenar
    df_local['Mes'] = pd.to_datetime(df_local['Mes'], format='%Y-%m', errors='coerce')
    df_local = df_local.dropna(subset=['Mes'])
    df_local = df_local.sort_values('Mes')

    # 4) Serie mensal e limpeza
    series = df_local.set_index('Mes')['Producao_Total_kg'].asfreq('MS')
    series = series.dropna()

    if series.shape[0] < 6:
        raise ValueError('Poucos dados para prever. Forneca pelo menos 6 meses.')

    # 5) Modelo Holt sem sazonalidade (robusto para serie curta)
    model = ExponentialSmoothing(series, trend='add', seasonal=None, initialization_method='estimated')
    fit = model.fit()

    # 6) Previsao 12 meses
    steps = 12
    forecast = fit.forecast(steps)

    # 7) Intervalos de confiança aproximados
    resid_std = fit.resid.dropna().std()
    fcst_df = pd.DataFrame({
        'Mes': forecast.index,
        'Producao_Prevista_kg': forecast.values
    })
    fcst_df['Lower'] = fcst_df['Producao_Prevista_kg'] - 1.96 * resid_std
    fcst_df['Upper'] = fcst_df['Producao_Prevista_kg'] + 1.96 * resid_std

    # 8) Salvar: preserva nome base do arquivo
    base = os.path.splitext(os.path.basename(input_path))[0]
    out_name = base + '_previsao_12m.csv'
    out_path = os.path.join(output_dir, out_name)
    fcst_df.to_csv(out_path, index=False)

    # 9) (Opcional) Salvar gráfico PNG no mesmo diretório
    plt.figure(figsize=(10,5))
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