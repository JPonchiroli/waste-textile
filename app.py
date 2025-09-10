from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash, session
from werkzeug.utils import secure_filename
# Supondo que process_file agora gerará 3 gráficos
from ml._main import process_file 
import os

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

        # --- NOVA ALTERAÇÃO ---
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

# --- NOVA ROTA PARA SERVIR AS IMAGENS ---
@app.route('/plots/<filename>')
def serve_plot(filename):
    # Por segurança, verifica se o arquivo solicitado está na sessão
    allowed_files = [session.get('fig1'), session.get('fig2'), session.get('fig3')]
    if filename not in allowed_files:
        return 'Acesso não permitido', 403
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True, port=5001)