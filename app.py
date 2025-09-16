from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session
from werkzeug.utils import secure_filename
# Supondo que process_file agora gerará 3 gráficos
from ml._main import process_file 
import pandas as pd
import os

import matplotlib
# Usar backend não interativo para evitar problemas com threads
matplotlib.use('Agg')  # Usar backend não interativo
import matplotlib.pyplot as plt

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'waste-textile-secret-key' # Use uma chave mais segura em produção

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

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # --- ALTERAÇÃO IMPORTANTE ---
            # Ajuste sua função `process_file` para retornar o caminho do CSV e uma LISTA com os 3 caminhos dos gráficos.
            # Exemplo de retorno esperado: ('caminho/do/output.csv', ['caminho/fig1.png', 'caminho/fig2.png', 'caminho/fig3.png'])
            out_csv_path, out_fig_paths = process_file(filepath, app.config['UPLOAD_FOLDER'])
            
            # Verifique se foram retornados 3 gráficos
            if len(out_fig_paths) != 3:
                flash('Erro no processamento: a função não retornou 3 gráficos.')
                return redirect(url_for('index'))

        except Exception as e:
            flash(f'Erro no processamento do arquivo: {str(e)}')
            return redirect(url_for('index'))

        # Salva o nome do arquivo CSV na sessão
        out_csv_name = os.path.basename(out_csv_path)
        session['last_processed_file'] = out_csv_name

        # Salva os nomes dos arquivos de imagem dos gráficos na sessão
        session['fig1'] = os.path.basename(out_fig_paths[0])
        session['fig2'] = os.path.basename(out_fig_paths[1])
        session['fig3'] = os.path.basename(out_fig_paths[2])

        # Redireciona com sucesso
        return redirect(url_for('index') + '?upload=success')
    else:
        flash('Tipo de arquivo não permitido! Envie apenas .xlsx ou .csv')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file_route(filename): # Renomeado para evitar conflito de nome
    if 'last_processed_file' not in session or session['last_processed_file'] != filename:
        flash('Arquivo não encontrado ou acesso inválido.')
        return redirect(url_for('index'))

    return send_from_directory(
        directory=app.config['UPLOAD_FOLDER'],
        path=filename,
        as_attachment=True
    )

# --- ROTA PARA SERVIR AS IMAGENS ---
@app.route('/plots/<filename>')
def serve_plot(filename):
    # Por segurança, verifica se o arquivo solicitado está na sessão
    allowed_files = [session.get('fig1'), session.get('fig2'), session.get('fig3')]
    if filename not in allowed_files:
        return 'Acesso não permitido', 403
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/dashboard')
def dashboard():
    # Verificar se há dados processados disponíveis
    if 'last_processed_file' not in session:
        flash('Nenhum dado processado encontrado. Faça upload de um arquivo primeiro.')
        return redirect(url_for('index'))
    
    try:
        # Carregar dados do arquivo processado
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], session['last_processed_file'])
        
        # Verificar se o arquivo existe
        if not os.path.exists(file_path):
            flash('Arquivo processado não encontrado. Faça upload novamente.')
            return redirect(url_for('index'))
            
        # Processar dados para o dashboard
        dashboard_data = process_data_for_dashboard(file_path)
        
        # Verificar se temos dados válidos
        if not dashboard_data['months']:
            flash('Erro ao processar dados para o dashboard.')
            return redirect(url_for('index'))
            
        return render_template('dashboard.html', data=dashboard_data)
        
    except Exception as e:
        app.logger.error(f'Erro ao carregar dashboard: {str(e)}')
        flash(f'Erro ao carregar dashboard: {str(e)}')
        return redirect(url_for('index'))

def process_data_for_dashboard(csv_path):
    """
    Processa os dados do arquivo Excel gerado pelo sistema para o dashboard
    """
    try:
        # Ler o arquivo Excel (que contém duas abas)
        dados_completos_df = pd.read_excel(csv_path, sheet_name='Dados_Completos')
        previsoes_df = pd.read_excel(csv_path, sheet_name='Previsoes_12m')
        
        # Verificar se a coluna Residuo_kg existe nos dados históricos, se não, calcular
        if 'Residuo_kg' not in dados_completos_df.columns or dados_completos_df['Residuo_kg'].isnull().all():
            dados_completos_df['Residuo_kg'] = dados_completos_df['Producao_Total_kg'] * 0.10
        
        # Combinar dados históricos e previsões
        # Primeiro garantir que as colunas estão consistentes
        colunas_comuns = ['Mes', 'Producao_Total_kg', 'Eficiencia_kg_h', 'Horas_Operacionais', 'Residuo_kg']
        
        # Selecionar apenas as colunas comuns para ambos os DataFrames
        dados_historicos = dados_completos_df[colunas_comuns].copy()
        previsoes_para_combinar = previsoes_df[colunas_comuns].copy()
        
        # Combinar dados históricos e previsões
        dados_combinados = pd.concat([dados_historicos, previsoes_para_combinar], ignore_index=True)
        
        # Adicionar coluna is_forecast para identificar previsões
        dados_combinados['is_forecast'] = [False] * len(dados_historicos) + [True] * len(previsoes_para_combinar)
        
        # Adicionar intervalos de confiança se disponíveis nas previsões
        if all(col in previsoes_df.columns for col in ['Producao_Minima_Esperada', 'Producao_Maxima_Esperada']):
            # Para dados históricos, preencher com valores vazios
            min_expected_historical = [None] * len(dados_historicos)
            max_expected_historical = [None] * len(dados_historicos)
            
            dados_combinados['min_expected'] = min_expected_historical + previsoes_df['Producao_Minima_Esperada'].tolist()
            dados_combinados['max_expected'] = max_expected_historical + previsoes_df['Producao_Maxima_Esperada'].tolist()
        
        # Preparar dados para o dashboard
        dashboard_data = {
            'months': dados_combinados['Mes'].astype(str).tolist(),
            'production': dados_combinados['Producao_Total_kg'].tolist(),
            'efficiency': dados_combinados['Eficiencia_kg_h'].tolist(),
            'hours': dados_combinados['Horas_Operacionais'].tolist(),
            'waste': dados_combinados['Residuo_kg'].tolist(),
            'is_forecast': dados_combinados['is_forecast'].tolist()
        }
        
        # Adicionar intervalos de confiança se disponíveis
        if 'min_expected' in dados_combinados.columns:
            dashboard_data['min_expected'] = dados_combinados['min_expected'].tolist()
        if 'max_expected' in dados_combinados.columns:
            dashboard_data['max_expected'] = dados_combinados['max_expected'].tolist()
        
        # Calcular métricas para os cards (usando o último mês disponível)
        if len(dados_combinados) > 0:
            ultimo_registro = dados_combinados.iloc[-1]
            ultimo_historico = dados_historicos.iloc[-1] if len(dados_historicos) > 0 else ultimo_registro
            
            # Calcular variações percentuais
            variacao_producao = ((ultimo_registro['Producao_Total_kg'] - ultimo_historico['Producao_Total_kg']) / 
                                ultimo_historico['Producao_Total_kg']) * 100
            variacao_eficiencia = ((ultimo_registro['Eficiencia_kg_h'] - ultimo_historico['Eficiencia_kg_h']) / 
                                  ultimo_historico['Eficiencia_kg_h']) * 100
            variacao_horas = ((ultimo_registro['Horas_Operacionais'] - ultimo_historico['Horas_Operacionais']) / 
                             ultimo_historico['Horas_Operacionais']) * 100
            
            # Adicionar métricas ao dashboard_data
            dashboard_data['metrics'] = {
                'producao_total': float(ultimo_registro['Producao_Total_kg']),
                'variacao_producao': float(variacao_producao),
                'eficiencia': float(ultimo_registro['Eficiencia_kg_h']),
                'variacao_eficiencia': float(variacao_eficiencia),
                'horas_operacionais': float(ultimo_registro['Horas_Operacionais']),
                'variacao_horas': float(variacao_horas),
                'residuo_estimado': float(ultimo_registro['Residuo_kg']),
                'variacao_residuo': float(variacao_producao)  # Resíduo varia na mesma proporção da produção
            }
        else:
            # Valores padrão se não houver dados suficientes
            dashboard_data['metrics'] = {
                'producao_total': 0,
                'variacao_producao': 0,
                'eficiencia': 0,
                'variacao_eficiencia': 0,
                'horas_operacionais': 0,
                'variacao_horas': 0,
                'residuo_estimado': 0,
                'variacao_residuo': 0
            }
        
        return dashboard_data
        
    except Exception as e:
        print(f"Erro ao processar dados para dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Retornar dados vazios em caso de erro
        return {
            'months': [], 'production': [], 'efficiency': [], 'hours': [], 'waste': [],
            'min_expected': [], 'max_expected': [], 'is_forecast': [], 
            'metrics': {
                'producao_total': 0, 'variacao_producao': 0,
                'eficiencia': 0, 'variacao_eficiencia': 0,
                'horas_operacionais': 0, 'variacao_horas': 0,
                'residuo_estimado': 0, 'variacao_residuo': 0
            }
        }

if __name__ == '__main__':
    app.run(debug=True, port=5001)