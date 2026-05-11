import os
import pickle

import numpy as np
import pandas as pd

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, 'model.pkl')
SCALER_PATH = os.path.join(BASE_DIR, 'scaler.pkl')
TRAINING_DATA_PATH = os.path.join(BASE_DIR, 'training_data.csv')

FEATURE_COLUMNS = [
    'Mes_Num',
    'Producao_Total_kg',
    'Eficiencia_kg_h',
    'Horas_Operacionais',
    'Residuo_kg'
]
TARGET_COLUMNS = [
    'Potencial_Reciclagem_Percent',
    'Economia_RS'
]


class SimpleStandardScaler:
    def __init__(self):
        self.mean_ = None
        self.scale_ = None

    def fit(self, X):
        X = np.asarray(X, dtype=float)
        self.mean_ = X.mean(axis=0)
        self.scale_ = X.std(axis=0)
        self.scale_[self.scale_ == 0] = 1.0
        return self

    def transform(self, X):
        X = np.asarray(X, dtype=float)
        return (X - self.mean_) / self.scale_

    def fit_transform(self, X):
        return self.fit(X).transform(X)


class LinearMultiOutputRegressor:
    def __init__(self):
        self.coef_ = None
        self.intercept_ = None

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)

        if y.ndim == 1:
            y = y.reshape(-1, 1)

        X_design = np.hstack([np.ones((X.shape[0], 1)), X])
        coeffs, *_ = np.linalg.lstsq(X_design, y, rcond=None)
        self.intercept_ = coeffs[0, :]
        self.coef_ = coeffs[1:, :]
        return self

    def predict(self, X):
        X = np.asarray(X, dtype=float)
        X_design = np.hstack([np.ones((X.shape[0], 1)), X])
        coeffs = np.vstack([self.intercept_, self.coef_])
        return X_design.dot(coeffs)


def generate_synthetic_training_data(samples=60, start_date='2022-01', random_state=42):
    rng = np.random.default_rng(random_state)
    dates = pd.date_range(start_date, periods=samples, freq='MS')
    anos = dates.year.to_numpy()
    meses = dates.month.to_numpy()

    hours_season = np.array([ -8.0, -5.0, 0.0, 4.0, 8.0, 12.0, 15.0, 12.0, 6.0, 2.0, -2.0, -7.0 ])
    eff_season = np.array([ -1.5, -1.0, -0.2, 0.8, 1.6, 2.0, 2.2, 1.8, 1.0, 0.3, -0.6, -1.2 ])
    waste_season = np.array([ 0.013, 0.012, 0.010, 0.008, 0.007, 0.006, 0.006, 0.007, 0.009, 0.010, 0.012, 0.014 ])
    price_season = np.array([ 2.10, 2.05, 2.00, 2.05, 2.10, 2.20, 2.30, 2.35, 2.40, 2.45, 2.50, 2.55 ])

    trend_hours = np.linspace(0.0, 10.0, samples)
    trend_eff = np.linspace(0.0, 2.5, samples)
    trend_price = np.linspace(0.0, 0.5, samples)

    horas = np.empty(samples, dtype=float)
    eficiencia = np.empty(samples, dtype=float)
    waste_pct = np.empty(samples, dtype=float)

    for i in range(samples):
        season_hours = hours_season[meses[i] - 1]
        season_eff = eff_season[meses[i] - 1]
        season_waste = waste_season[meses[i] - 1]

        if i == 0:
            horas[i] = 700 + season_hours + rng.normal(0, 12)
            eficiencia[i] = 88.5 + season_eff + rng.normal(0, 1.2)
            waste_pct[i] = 0.10 + season_waste + rng.normal(0, 0.004)
        else:
            horas[i] = (
                0.82 * horas[i - 1]
                + 0.18 * (700 + season_hours + trend_hours[i])
                + rng.normal(0, 10)
            )
            eficiencia[i] = (
                0.78 * eficiencia[i - 1]
                + 0.22 * (88.5 + season_eff + trend_eff[i])
                + rng.normal(0, 1.0)
            )
            waste_pct[i] = (
                0.65 * waste_pct[i - 1]
                + 0.35 * (0.10 + season_waste - 0.0008 * (eficiencia[i] - 88.5))
                + rng.normal(0, 0.003)
            )

    horas = np.round(horas, 0).clip(560, 840)
    eficiencia = np.round(eficiencia, 1).clip(70, 105)
    waste_pct = np.clip(waste_pct, 0.06, 0.14)

    production_factor = np.round(rng.normal(0.98, 0.02, size=samples), 3)
    producao = np.round(horas * eficiencia * production_factor, 2)
    residuo_kg = np.round(producao * waste_pct, 2)

    rec_base = 55.0 + (eficiencia - 84.0) * 0.6 - (waste_pct - 0.10) * 60.0
    potencial_reciclagem = np.clip(rec_base + rng.normal(0, 3.5, size=samples), 45, 98).round(1)

    preco_inicial = np.clip(price_season[meses - 1] + trend_price + rng.normal(0, 0.12, size=samples), 1.8, 3.8)
    economia_rs = np.round(residuo_kg * (potencial_reciclagem / 100) * preco_inicial, 2)

    df = pd.DataFrame({
        'Ano': anos,
        'Mes_Num': meses,
        'Mes': dates.strftime('%Y-%m'),
        'Producao_Total_kg': producao,
        'Eficiencia_kg_h': eficiencia,
        'Horas_Operacionais': horas,
        'Residuo_kg': residuo_kg,
        'Potencial_Reciclagem_Percent': potencial_reciclagem,
        'Economia_RS': economia_rs
    })

    return df


def train_and_save_model(df=None):
    if df is None:
        df = generate_synthetic_training_data()

    X = df[FEATURE_COLUMNS].astype(float)
    y = df[TARGET_COLUMNS].astype(float)

    scaler = SimpleStandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LinearMultiOutputRegressor().fit(X_scaled, y)

    with open(SCALER_PATH, 'wb') as scaler_file:
        pickle.dump(scaler, scaler_file)

    with open(MODEL_PATH, 'wb') as model_file:
        pickle.dump(model, model_file)

    df.to_csv(TRAINING_DATA_PATH, index=False)

    return model, scaler


def load_or_train_model():
    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        with open(MODEL_PATH, 'rb') as model_file:
            model = pickle.load(model_file)
        with open(SCALER_PATH, 'rb') as scaler_file:
            scaler = pickle.load(scaler_file)
        return model, scaler

    return train_and_save_model()


def predict_recycling_metrics(df, scaler, model):
    data = df.copy()

    if 'Residuo_kg' not in data.columns:
        data['Residuo_kg'] = np.round(data['Producao_Total_kg'] * 0.10, 2)

    if 'Mes_Num' not in data.columns:
        data['Mes_Num'] = (
            pd.to_datetime(data['Mes'].astype(str), format='%Y-%m', errors='coerce')
            .dt.month
            .fillna(1)
            .astype(int)
        )

    predict_df = data[FEATURE_COLUMNS].fillna(0).astype(float)
    predict_scaled = scaler.transform(predict_df)
    predictions = model.predict(predict_scaled)

    data['Potencial_Reciclagem_Percent'] = np.clip(predictions[:, 0], 40, 98).round(1)
    data['Economia_RS'] = np.maximum(predictions[:, 1], 0).round(2)
    data['Residuo_Reciclavel_kg'] = np.round(
        data['Residuo_kg'] * data['Potencial_Reciclagem_Percent'] / 100,
        2
    )

    return data[['Mes', 'Potencial_Reciclagem_Percent', 'Economia_RS', 'Residuo_Reciclavel_kg']]
