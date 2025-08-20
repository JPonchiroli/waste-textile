from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
from ml._main import process_file  # Importa o módulo _main.py
import time
import os

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui'

# Garante que a pasta de uploads exista
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Verifica extensão
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET'])
def upload_page():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'arquivo' not in request.files:
        flash('Nenhum arquivo enviado')
        return redirect(url_for('index'))

    file = request.files['arquivo']
    nome_textil = request.form.get('nome', '')

    if file.filename == '':
        flash('Nenhum arquivo selecionado')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # Processa o arquivo upado e gera o arquivo de saída
            out_csv_path, out_fig_path = process_file(filepath, app.config['UPLOAD_FOLDER'])
        except Exception as e:
            flash('Erro no processamento: ' + str(e))
            return redirect(url_for('index'))

        # Retorna o arquivo de previsão para download
        out_csv_name = os.path.basename(out_csv_path)
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            out_csv_name,
            as_attachment=True
        )
    else:
        flash('Tipo de arquivo não permitido! Envie apenas .xlsx ou .csv')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
