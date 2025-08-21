from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session
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

@app.route('/uploadComplete')
def upload_complete():
    return render_template('uploadComplete.html')

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
            print('Entrou no try')
            out_csv_path, out_fig_path = process_file(filepath, app.config['UPLOAD_FOLDER'])
        except Exception as e:
            flash('Erro no processamento: ' + str(e))
            return redirect(url_for('index'))

        # Salva o nome do arquivo gerado na sessão
        out_csv_name = os.path.basename(out_csv_path)
        session['last_processed_file'] = out_csv_name  # ← Armazena para download depois

        return redirect(url_for('upload_complete'))
    else:
        flash('Tipo de arquivo não permitido! Envie apenas .xlsx ou .csv')
        return redirect(url_for('index'))

@app.route('/download/<filename>')
def download_file(filename):
    if 'last_processed_file' not in session or session['last_processed_file'] != filename:
        flash('Arquivo não encontrado ou acesso inválido.')
        return redirect(url_for('index'))

    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=True
    )

if __name__ == '__main__':
    app.run(debug=True)
