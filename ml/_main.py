import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def process_file(input_path, output_dir):
    print('Processando arquivo:', input_path)

    # 1. Ler arquivo
    if input_path.endswith('.xlsx'):
        df_local = pd.read_excel(input_path)
    elif input_path.endswith('.csv'):
        df_local = pd.read_csv(input_path)
    else:
        raise ValueError('Formato de arquivo não suportado')

    # 2. Validar colunas
    if 'Mes' not in df_local.columns or 'Producao_Total_kg' not in df_local.columns:
        raise ValueError('Colunas obrigatórias não encontradas: Mes e Producao_Total_kg')

    # 3. Converter e ordenar datas
    df_local['Mes'] = pd.to_datetime(df_local['Mes'], format='%Y-%m', errors='coerce')
    df_local = df_local.dropna(subset=['Mes']).sort_values('Mes')

    # 4. Criar série temporal
    series = df_local.set_index('Mes')['Producao_Total_kg'].asfreq('MS').dropna()

    if len(series) < 6:
        raise ValueError('Poucos dados para prever. Forneça pelo menos 6 meses.')

    # 5. Modelo Holt
    model = ExponentialSmoothing(series, trend='add', seasonal=None, initialization_method='estimated')
    fit = model.fit()

    # 6. Previsão
    forecast = fit.forecast(12)
    resid_std = fit.resid.dropna().std()

    fcst_df = pd.DataFrame({
        'Mes': forecast.index.strftime('%Y-%m'),
        'Producao_Prevista_kg': forecast.values
    })
    fcst_df['Lower'] = fcst_df['Producao_Prevista_kg'] - 1.96 * resid_std
    fcst_df['Upper'] = fcst_df['Producao_Prevista_kg'] + 1.96 * resid_std

    # 7. Salvar como .xlsx
    base = os.path.splitext(os.path.basename(input_path))[0]
    out_name = base + '_previsao_12m.xlsx'
    out_path = os.path.join(output_dir, out_name)

    with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
        df_local.to_excel(writer, sheet_name='Dados Originais', index=False)
        fcst_df.to_excel(writer, sheet_name='Previsao 12 Meses', index=False)

    # 8. Gráfico
    plt.figure(figsize=(10, 5))
    sns.lineplot(x=series.index, y=series.values, label='Histórico')
    sns.lineplot(x=forecast.index, y=forecast.values, label='Previsão')
    plt.fill_between(forecast.index, fcst_df['Lower'], fcst_df['Upper'], color='orange', alpha=0.2, label='Intervalo ~95%')
    plt.title('Produção Total (kg) - Histórico e Previsão (12 meses)')
    plt.xlabel('Mês')
    plt.ylabel('kg')
    plt.legend()
    plt.tight_layout()

    fig_name = base + '_previsao_12m.png'
    fig_path = os.path.join(output_dir, fig_name)
    plt.savefig(fig_path, dpi=150)
    plt.close()

    return out_path, fig_path