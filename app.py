from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'appfluir'

#banco de dados
def conectar_banco():
    return sqlite3.connect('banco.db')

#tabela de usuários
def criar_tabela_usuarios():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            tipo TEXT NOT NULL
        )
    ''')
    conn.commit()

    cursor.execute('SELECT * FROM usuarios WHERE tipo = "admin"')
    admin = cursor.fetchone()
    if not admin:
        cursor.execute('''
            INSERT INTO usuarios (nome, cpf, senha, tipo)
            VALUES (?, ?, ?, ?)
        ''', ('Admin', 'fluir_admin', 'admin123', 'admin'))
        conn.commit()

    conn.close()


#Login
@app.route('/', methods=['GET', 'POST'])
def pagina_login():
    if request.method == 'POST':
        cpf_digitado = request.form['cpf']
        senha_digitada = request.form['senha']

        banco = conectar_banco()
        banco.row_factory = sqlite3.Row
        usuario = banco.execute(
            'SELECT * FROM usuarios WHERE cpf = ? AND senha = ?',
            (cpf_digitado, senha_digitada)
        ).fetchone()
        banco.close()

        if usuario:
            session['id_usuario'] = usuario['id']
            flash('Login feito com sucesso!')
            return redirect(url_for('pagina_painel'))  # Crie depois a rota 'pagina_painel'
        else:
            flash('CPF ou senha incorretos. Tente novamente.')

    return render_template('login.html')

#Cadastro
@app.route('/cadastro', methods=['GET', 'POST'])
def pagina_cadastro():
    if request.method == 'POST':
        nome_completo = request.form['nome']
        cpf_novo = request.form['cpf']
        senha_nova = request.form['senha']

        banco = conectar_banco()
        try:
            banco.execute(
                'INSERT INTO usuarios (nome, cpf, senha, tipo) VALUES (?, ?, ?, ?)',
                (nome_completo, cpf_novo, senha_nova, 'usuario')
            )
            banco.commit()
            flash('Cadastro realizado com sucesso! Agora faça login.')
            return redirect(url_for('pagina_login'))
        except sqlite3.IntegrityError:
            flash('Esse CPF já está cadastrado.')
        finally:
            banco.close()

    return render_template('cadastro.html')

#Roda todo o app
if __name__ == '__main__':
    criar_tabela_usuarios()
    app.run(debug=True)
