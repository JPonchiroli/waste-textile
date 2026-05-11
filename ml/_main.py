import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing, SimpleExpSmoothing

from ml.model import load_or_train_model, predict_recycling_metrics

REQUIRED_COLS = ['Mes', 'Producao_Total_kg', 'Eficiencia_kg_h', 'Horas_Operacionais']
FORECAST_PERIODS = 12
WASTE_RATE = 0.10
RANGE_RATE = 0.05

MODEL, SCALER = load_or_train_model()


def _read_input_file(input_path):
    extension = os.path.splitext(input_path)[1].lower()
    if extension == '.xlsx':
        return pd.read_excel(input_path, engine='openpyxl')
    if extension == '.csv':
        return pd.read_csv(input_path)
    raise ValueError('Formato de arquivo nao suportado. Envie .xlsx ou .csv.')


def _safe_pct_change(new_value, old_value):
    if pd.isna(old_value) or old_value == 0:
        return 0.0
    return float(((new_value - old_value) / old_value) * 100)


def _prepare_monthly_data(df):
    missing_cols = [col for col in REQUIRED_COLS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Colunas obrigatorias nao encontradas: {', '.join(missing_cols)}")

    prepared = df.copy()
    prepared['Mes_dt'] = pd.to_datetime(prepared['Mes'].astype(str), format='%Y-%m', errors='coerce')
    prepared = prepared.dropna(subset=['Mes_dt'])

    for col in ['Producao_Total_kg', 'Eficiencia_kg_h', 'Horas_Operacionais']:
        prepared[col] = pd.to_numeric(prepared[col], errors='coerce')

    prepared = prepared.dropna(subset=['Producao_Total_kg', 'Eficiencia_kg_h', 'Horas_Operacionais'])
    prepared = prepared[
        (prepared['Producao_Total_kg'] > 0)
        & (prepared['Eficiencia_kg_h'] > 0)
        & (prepared['Horas_Operacionais'] > 0)
    ]

    if prepared.empty:
        raise ValueError('Nenhuma linha valida encontrada no arquivo.')

    monthly = (
        prepared
        .groupby('Mes_dt', as_index=True)
        .agg({
            'Producao_Total_kg': 'sum',
            'Horas_Operacionais': 'sum',
            'Eficiencia_kg_h': 'mean'
        })
        .sort_index()
    )

    full_index = pd.date_range(monthly.index.min(), monthly.index.max(), freq='MS')
    monthly = monthly.reindex(full_index)
    monthly[['Producao_Total_kg', 'Horas_Operacionais', 'Eficiencia_kg_h']] = (
        monthly[['Producao_Total_kg', 'Horas_Operacionais', 'Eficiencia_kg_h']]
        .interpolate(method='time')
        .ffill()
        .bfill()
    )

    if len(monthly) < 6:
        raise ValueError('Poucos dados para prever. Forneca pelo menos 6 meses validos.')

    monthly['Mes_dt'] = monthly.index
    monthly['Mes'] = monthly.index.strftime('%Y-%m')
    monthly['Residuo_kg'] = (monthly['Producao_Total_kg'] * WASTE_RATE).round(2)
    monthly['Producao_Minima_Esperada'] = np.nan
    monthly['Producao_Maxima_Esperada'] = np.nan
    monthly['Tipo_Dado'] = 'Historico'
    monthly = monthly.reset_index(drop=True)
    monthly = _add_recycling_predictions(monthly)

    return monthly


def _add_recycling_predictions(df):
    predictions = predict_recycling_metrics(df, SCALER, MODEL)
    return df.merge(
        predictions,
        on='Mes',
        how='left'
    )


def _naive_forecast(train, periods):
    return np.repeat(train.iloc[-1], periods)


def _moving_average_forecast(train, periods):
    window = min(3, len(train))
    return np.repeat(train.tail(window).mean(), periods)


def _drift_forecast(train, periods):
    if len(train) < 2:
        return _naive_forecast(train, periods)
    slope = (train.iloc[-1] - train.iloc[0]) / (len(train) - 1)
    return np.array([train.iloc[-1] + slope * step for step in range(1, periods + 1)])


def _statsmodels_forecast(train, periods, model_name):
    if model_name == 'ses':
        fit = SimpleExpSmoothing(train, initialization_method='estimated').fit(optimized=True)
        return fit.forecast(periods).to_numpy()

    if model_name == 'holt':
        fit = ExponentialSmoothing(
            train,
            trend='add',
            damped_trend=False,
            seasonal=None,
            initialization_method='estimated'
        ).fit(optimized=True)
        return fit.forecast(periods).to_numpy()

    if model_name == 'holt_damped':
        fit = ExponentialSmoothing(
            train,
            trend='add',
            damped_trend=True,
            seasonal=None,
            initialization_method='estimated'
        ).fit(optimized=True)
        return fit.forecast(periods).to_numpy()

    if model_name == 'seasonal_add':
        fit = ExponentialSmoothing(
            train,
            trend='add',
            damped_trend=True,
            seasonal='add',
            seasonal_periods=12,
            initialization_method='estimated'
        ).fit(optimized=True)
        return fit.forecast(periods).to_numpy()

    raise ValueError(f'Modelo desconhecido: {model_name}')


def _candidate_forecast(train, periods, candidate):
    if candidate == 'naive':
        return _naive_forecast(train, periods)
    if candidate == 'moving_average_3m':
        return _moving_average_forecast(train, periods)
    if candidate == 'drift':
        return _drift_forecast(train, periods)
    return _statsmodels_forecast(train, periods, candidate)


def _forecast_series(series, periods=FORECAST_PERIODS):
    clean_series = pd.Series(series).astype(float).asfreq('MS').interpolate(method='time').ffill().bfill()
    clean_series = clean_series.clip(lower=0.01)

    candidates = ['naive', 'moving_average_3m', 'drift', 'ses', 'holt', 'holt_damped']
    if len(clean_series) >= 24:
        candidates.append('seasonal_add')

    if len(clean_series) >= 10:
        holdout_size = min(6, max(2, len(clean_series) // 4))
        train = clean_series.iloc[:-holdout_size]
        validation = clean_series.iloc[-holdout_size:]

        scores = []
        for candidate in candidates:
            try:
                forecast = _candidate_forecast(train, holdout_size, candidate)
                forecast = np.clip(forecast, 0.01, None)
                mae = float(np.mean(np.abs(validation.to_numpy() - forecast)))
                scores.append((mae, candidate))
            except Exception:
                continue

        if scores:
            _, best_candidate = min(scores, key=lambda item: item[0])
        else:
            best_candidate = 'holt_damped'
    else:
        best_candidate = 'holt_damped'

    try:
        forecast = _candidate_forecast(clean_series, periods, best_candidate)
    except Exception:
        best_candidate = 'moving_average_3m'
        forecast = _moving_average_forecast(clean_series, periods)

    forecast = np.clip(forecast, 0.01, None)
    return forecast, best_candidate


def _build_forecast_df(df, periods=FORECAST_PERIODS):
    last_date = df['Mes_dt'].iloc[-1]
    forecast_index = pd.date_range(last_date + pd.DateOffset(months=1), periods=periods, freq='MS')

    eff_series = pd.Series(df['Eficiencia_kg_h'].to_numpy(), index=df['Mes_dt'])
    hours_series = pd.Series(df['Horas_Operacionais'].to_numpy(), index=df['Mes_dt'])

    eff_forecast, eff_model = _forecast_series(eff_series, periods)
    hours_forecast, hours_model = _forecast_series(hours_series, periods)

    forecast_df = pd.DataFrame({
        'Mes_dt': forecast_index,
        'Mes': forecast_index.strftime('%Y-%m'),
        'Eficiencia_kg_h': np.round(eff_forecast, 2),
        'Horas_Operacionais': np.round(hours_forecast, 2),
    })
    forecast_df['Producao_Total_kg'] = (
        forecast_df['Eficiencia_kg_h'] * forecast_df['Horas_Operacionais']
    ).round(2)
    forecast_df['Residuo_kg'] = (forecast_df['Producao_Total_kg'] * WASTE_RATE).round(2)
    forecast_df['Producao_Minima_Esperada'] = (forecast_df['Producao_Total_kg'] * (1 - RANGE_RATE)).round(2)
    forecast_df['Producao_Maxima_Esperada'] = (forecast_df['Producao_Total_kg'] * (1 + RANGE_RATE)).round(2)
    forecast_df['Tipo_Dado'] = 'Previsao'
    forecast_df['Modelo_Eficiencia'] = eff_model
    forecast_df['Modelo_Horas'] = hours_model
    forecast_df = _add_recycling_predictions(forecast_df)

    return forecast_df


def _save_plot(path):
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def process_file(input_path, output_dir):
    """
    Le um arquivo de dados, gera previsoes para 12 meses, salva um Excel
    com os resultados e cria 3 graficos de visualizacao.
    """
    print('Processando arquivo:', input_path)

    raw_df = _read_input_file(input_path)
    historical_df = _prepare_monthly_data(raw_df)
    forecast_df = _build_forecast_df(historical_df)

    combined_df = pd.concat([historical_df, forecast_df], ignore_index=True, sort=False)
    output_cols = [
        'Mes',
        'Tipo_Dado',
        'Producao_Total_kg',
        'Eficiencia_kg_h',
        'Horas_Operacionais',
        'Residuo_kg',
        'Potencial_Reciclagem_Percent',
        'Residuo_Reciclavel_kg',
        'Economia_RS',
        'Producao_Minima_Esperada',
        'Producao_Maxima_Esperada',
        'Modelo_Eficiencia',
        'Modelo_Horas',
        'Mes_dt',
    ]
    combined_df = combined_df.reindex(columns=output_cols)
    forecast_df = forecast_df.reindex(columns=output_cols)

    base = os.path.splitext(os.path.basename(input_path))[0]
    out_name = f"{base}_com_previsao.xlsx"
    out_path = os.path.join(output_dir, out_name)

    with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
        combined_df.drop(columns=['Mes_dt']).to_excel(writer, sheet_name='Dados_Completos', index=False)
        forecast_df.drop(columns=['Mes_dt']).to_excel(writer, sheet_name='Previsoes_12m', index=False)

    fig_paths = []
    plt.style.use('seaborn-v0_8-whitegrid')

    plt.figure(figsize=(14, 9))
    plt.plot(
        historical_df['Mes_dt'],
        historical_df['Producao_Total_kg'],
        marker='o',
        linestyle='-',
        label='Producao Historica'
    )
    forecast_plot_dates = pd.concat([
        historical_df[['Mes_dt', 'Producao_Total_kg']].tail(1),
        forecast_df[['Mes_dt', 'Producao_Total_kg']]
    ])
    plt.plot(
        forecast_plot_dates['Mes_dt'],
        forecast_plot_dates['Producao_Total_kg'],
        marker='o',
        linestyle='--',
        label='Producao Prevista'
    )
    plt.title('Producao Total: Historico vs. Previsao (12 Meses)', fontsize=22)
    plt.ylabel('Producao (kg)', fontsize=22)
    plt.xlabel('Mes', fontsize=22)
    plt.xticks(rotation=45, fontsize=18)
    plt.yticks(fontsize=18)
    plt.legend(fontsize=18)
    fig1_path = os.path.join(output_dir, f"{base}_grafico_producao.png")
    _save_plot(fig1_path)
    fig_paths.append(fig1_path)

    plt.figure(figsize=(14, 9))
    plt.plot(forecast_df['Mes_dt'], forecast_df['Eficiencia_kg_h'], marker='o', color='green')
    plt.title(f"Previsao de Eficiencia (modelo: {forecast_df['Modelo_Eficiencia'].iloc[0]})", fontsize=20)
    plt.ylabel('Eficiencia (kg/h)', fontsize=22)
    plt.xlabel('Mes', fontsize=22)
    plt.xticks(rotation=45, fontsize=18)
    plt.yticks(fontsize=18)
    fig2_path = os.path.join(output_dir, f"{base}_grafico_eficiencia.png")
    _save_plot(fig2_path)
    fig_paths.append(fig2_path)

    plt.figure(figsize=(14, 9))
    plt.plot(forecast_df['Mes_dt'], forecast_df['Horas_Operacionais'], marker='o', color='purple')
    plt.title(f"Previsao de Horas Operacionais (modelo: {forecast_df['Modelo_Horas'].iloc[0]})", fontsize=20)
    plt.ylabel('Horas', fontsize=22)
    plt.xlabel('Mes', fontsize=22)
    plt.xticks(rotation=45, fontsize=18)
    plt.yticks(fontsize=18)
    fig3_path = os.path.join(output_dir, f"{base}_grafico_horas.png")
    _save_plot(fig3_path)
    fig_paths.append(fig3_path)

    print(f"Arquivo com previsoes salvo em: {out_path}")
    print(f"Graficos salvos: {fig_paths}")

    return out_path, fig_paths
