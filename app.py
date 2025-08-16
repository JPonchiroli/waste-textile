from flask import Flask, render_template
import os
import sys

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'sua-chave-secreta-aqui' # Importante para as mensagens flash

# Garante que a pasta de uploads exista
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 2. Função para verificar se a extensão do arquivo é permitida
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'arquivo' not in request.files:
        flash('Nenhum arquivo enviado')
        return redirect(url_for('index'))

    file = request.files['arquivo']
    nome_textil = request.form['nome']

    if file.filename == '':
        flash('Nenhum arquivo selecionado')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash(f'Têxtil "{nome_textil}" com arquivo "{filename}" enviado com sucesso!')
        return redirect(url_for('index'))
    else:
        flash('Tipo de arquivo não permitido!')
        return redirect(url_for('index'))

if __name__ == '__main__':
    extra_dirs = [
        os.path.join(os.getcwd(), 'templates'),
        os.path.join(os.getcwd(), 'static')
    ]
    extra_files = []
    for extra_dir in extra_dirs:
        for dirname, dirs, files in os.walk(extra_dir):
            for filename in files:
                filename = os.path.join(dirname, filename)
                if os.path.isfile(filename):
                    extra_files.append(filename)

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        extra_files=extra_files  # Força reinício ao alterar HTML/CSS/JS
    )
