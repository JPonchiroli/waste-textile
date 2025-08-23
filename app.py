from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session
from werkzeug.utils import secure_filename
from ml._main import process_file
import os

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'waste-textile'

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
            out_csv_path, out_fig_path = process_file(filepath, app.config['UPLOAD_FOLDER'])
            print(f"Arquivo processado: {out_csv_path}")
        except Exception as e:
            flash(f'Erro no processamento: {str(e)}')
            return redirect(url_for('index'))

        out_csv_name = os.path.basename(out_csv_path)
        session['last_processed_file'] = out_csv_name

        # Redireciona com sucesso
        return redirect(url_for('index') + '?upload=success')
    else:
        flash('Tipo de arquivo não permitido! Envie apenas .xlsx ou .csv')
        return redirect(url_for('index'))


@app.route('/download/<filename>')
def download_file(filename):
    if 'last_processed_file' not in session or session['last_processed_file'] != filename:
        flash('Arquivo não encontrado ou acesso inválido.')
        return redirect(url_for('index'))

    return send_from_directory(
        directory=app.config['UPLOAD_FOLDER'],
        path=filename,
        as_attachment=True
    )


if __name__ == '__main__':
    app.run(debug=True, port=5001)