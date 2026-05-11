import io
import os

import matplotlib
import pandas as pd
from flask import Flask, flash, redirect, render_template, request, send_file, send_from_directory, session, url_for
from werkzeug.utils import secure_filename

from ml._main import process_file


matplotlib.use('Agg')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'waste-textile-secret-key'  # Use uma chave mais segura em producao.

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'arquivo' not in request.files:
        flash('Nenhum arquivo enviado')
        return redirect(url_for('index'))

    file = request.files['arquivo']
    if file.filename == '':
        flash('Nenhum arquivo selecionado')
        return redirect(url_for('index'))

    if not file or not allowed_file(file.filename):
        flash('Tipo de arquivo nao permitido! Envie apenas .xlsx ou .csv')
        return redirect(url_for('index'))

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        out_file_path, out_fig_paths = process_file(filepath, app.config['UPLOAD_FOLDER'])

        if len(out_fig_paths) != 3:
            flash('Erro no processamento: a funcao nao retornou 3 graficos.')
            return redirect(url_for('index'))

    except Exception as e:
        flash(f'Erro no processamento do arquivo: {str(e)}')
        return redirect(url_for('index'))

    session['last_processed_file'] = os.path.basename(out_file_path)
    session['fig1'] = os.path.basename(out_fig_paths[0])
    session['fig2'] = os.path.basename(out_fig_paths[1])
    session['fig3'] = os.path.basename(out_fig_paths[2])

    return redirect(url_for('dashboard'))


@app.route('/download/template')
def download_template():
    columns = [
        'Mes',
        'Producao_Total_kg',
        'Eficiencia_kg_h',
        'Horas_Operacionais',
        'Residuo_kg'
    ]

    df = pd.DataFrame(columns=columns)
    output = io.BytesIO()
    df.to_excel(output, index=False, sheet_name='Dados')
    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='modelo_waste_textile.xlsx'
    )


@app.route('/download/<filename>')
def download_file_route(filename):
    if 'last_processed_file' not in session or session['last_processed_file'] != filename:
        flash('Arquivo nao encontrado ou acesso invalido.')
        return redirect(url_for('index'))

    return send_from_directory(
        directory=app.config['UPLOAD_FOLDER'],
        path=filename,
        as_attachment=True
    )


@app.route('/plots/<filename>')
def serve_plot(filename):
    allowed_files = [session.get('fig1'), session.get('fig2'), session.get('fig3')]
    if filename not in allowed_files:
        return 'Acesso nao permitido', 403
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/dashboard')
def dashboard():
    if 'last_processed_file' not in session:
        flash('Nenhum dado processado encontrado. Faca upload de um arquivo primeiro.')
        return redirect(url_for('index'))

    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], session['last_processed_file'])

        if not os.path.exists(file_path):
            flash('Arquivo processado nao encontrado. Faca upload novamente.')
            return redirect(url_for('index'))

        dashboard_data = process_data_for_dashboard(file_path)

        if not dashboard_data['months']:
            flash('Erro ao processar dados para o dashboard.')
            return redirect(url_for('index'))

        return render_template('dashboard.html', data=dashboard_data)

    except Exception as e:
        app.logger.error(f'Erro ao carregar dashboard: {str(e)}')
        flash(f'Erro ao carregar dashboard: {str(e)}')
        return redirect(url_for('index'))


def process_data_for_dashboard(file_path):
    """
    Processa os dados do arquivo Excel gerado pelo sistema para o dashboard.
    """
    try:
        dados_combinados = pd.read_excel(file_path, sheet_name='Dados_Completos')
        previsoes_df = pd.read_excel(file_path, sheet_name='Previsoes_12m')

        if 'Tipo_Dado' in dados_combinados.columns:
            dados_combinados['is_forecast'] = (
                dados_combinados['Tipo_Dado'].astype(str).str.lower().str.startswith('previs')
            )
        else:
            forecast_months = set(previsoes_df['Mes'].astype(str))
            dados_combinados['is_forecast'] = dados_combinados['Mes'].astype(str).isin(forecast_months)

        if 'Residuo_kg' not in dados_combinados.columns:
            dados_combinados['Residuo_kg'] = dados_combinados['Producao_Total_kg'] * 0.10
        else:
            dados_combinados['Residuo_kg'] = dados_combinados['Residuo_kg'].fillna(
                dados_combinados['Producao_Total_kg'] * 0.10
            )

        if 'Potencial_Reciclagem_Percent' not in dados_combinados.columns:
            dados_combinados['Potencial_Reciclagem_Percent'] = 0.0
        else:
            dados_combinados['Potencial_Reciclagem_Percent'] = dados_combinados['Potencial_Reciclagem_Percent'].fillna(0.0)

        if 'Residuo_Reciclavel_kg' not in dados_combinados.columns:
            dados_combinados['Residuo_Reciclavel_kg'] = 0.0
        else:
            dados_combinados['Residuo_Reciclavel_kg'] = dados_combinados['Residuo_Reciclavel_kg'].fillna(0.0)

        if 'Economia_RS' not in dados_combinados.columns:
            dados_combinados['Economia_RS'] = 0.0
        else:
            dados_combinados['Economia_RS'] = dados_combinados['Economia_RS'].fillna(0.0)

        dados_combinados['min_expected'] = (
            dados_combinados['Producao_Minima_Esperada']
            if 'Producao_Minima_Esperada' in dados_combinados.columns
            else None
        )
        dados_combinados['max_expected'] = (
            dados_combinados['Producao_Maxima_Esperada']
            if 'Producao_Maxima_Esperada' in dados_combinados.columns
            else None
        )

        dados_historicos = dados_combinados[~dados_combinados['is_forecast']].copy()
        previsoes_para_combinar = dados_combinados[dados_combinados['is_forecast']].copy()

        dashboard_data = {
            'months': dados_combinados['Mes'].astype(str).tolist(),
            'production': dados_combinados['Producao_Total_kg'].tolist(),
            'efficiency': dados_combinados['Eficiencia_kg_h'].tolist(),
            'hours': dados_combinados['Horas_Operacionais'].tolist(),
            'waste': dados_combinados['Residuo_kg'].tolist(),
            'recycling_potential': dados_combinados['Potencial_Reciclagem_Percent'].tolist(),
            'recycled_waste': dados_combinados['Residuo_Reciclavel_kg'].tolist(),
            'recycling_savings': dados_combinados['Economia_RS'].tolist(),
            'is_forecast': dados_combinados['is_forecast'].tolist(),
            'min_expected': dados_combinados['min_expected'].astype(object).where(
                pd.notna(dados_combinados['min_expected']), None
            ).tolist(),
            'max_expected': dados_combinados['max_expected'].astype(object).where(
                pd.notna(dados_combinados['max_expected']), None
            ).tolist()
        }

        if len(dados_historicos) > 0 and len(previsoes_para_combinar) > 0:
            ultimo_historico = dados_historicos.iloc[-1]
            primeira_previsao = previsoes_para_combinar.iloc[0]

            variacao_producao = calculate_percentage_change(
                primeira_previsao['Producao_Total_kg'],
                ultimo_historico['Producao_Total_kg']
            )
            variacao_eficiencia = calculate_percentage_change(
                primeira_previsao['Eficiencia_kg_h'],
                ultimo_historico['Eficiencia_kg_h']
            )
            variacao_horas = calculate_percentage_change(
                primeira_previsao['Horas_Operacionais'],
                ultimo_historico['Horas_Operacionais']
            )

            dashboard_data['metrics'] = {
                'producao_total': float(primeira_previsao['Producao_Total_kg']),
                'variacao_producao': float(variacao_producao),
                'eficiencia': float(primeira_previsao['Eficiencia_kg_h']),
                'variacao_eficiencia': float(variacao_eficiencia),
                'horas_operacionais': float(primeira_previsao['Horas_Operacionais']),
                'variacao_horas': float(variacao_horas),
                'residuo_estimado': float(primeira_previsao['Residuo_kg']),
                'variacao_residuo': float(variacao_producao),
                'recycling_potential': float(primeira_previsao['Potencial_Reciclagem_Percent']),
                'recycled_waste': float(primeira_previsao['Residuo_Reciclavel_kg']),
                'recycling_savings': float(primeira_previsao['Economia_RS'])
            }
        else:
            dashboard_data['metrics'] = empty_metrics()

        return dashboard_data

    except Exception as e:
        print(f"Erro ao processar dados para dashboard: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            'months': [], 'production': [], 'efficiency': [], 'hours': [], 'waste': [],
            'min_expected': [], 'max_expected': [], 'is_forecast': [],
            'metrics': empty_metrics()
        }


def calculate_percentage_change(new_value, old_value):
    if pd.isna(old_value) or old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100


def empty_metrics():
    return {
        'producao_total': 0, 'variacao_producao': 0,
        'eficiencia': 0, 'variacao_eficiencia': 0,
        'horas_operacionais': 0, 'variacao_horas': 0,
        'residuo_estimado': 0, 'variacao_residuo': 0,
        'recycling_potential': 0.0,
        'recycled_waste': 0.0,
        'recycling_savings': 0.0
    }


if __name__ == '__main__':
    app.run(debug=True, port=5001)
