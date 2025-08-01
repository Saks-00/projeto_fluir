from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from admin_models import AdminRepository, AdminService, AdminController

app = Flask(__name__)
app.secret_key = 'appfluir'

# Banco de dados
def conectar_banco():
    return sqlite3.connect('banco.db')

# Cria a tabela de usuários se não existir
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

    # Cria um admin padrão
    cursor.execute('SELECT * FROM usuarios WHERE tipo = "admin"')
    admin = cursor.fetchone()
    if not admin:
        cursor.execute('''
            INSERT INTO usuarios (nome, cpf, senha, tipo)
            VALUES (?, ?, ?, ?)
        ''', ('Admin', 'fluir_admin', 'admin123', 'admin'))
        conn.commit()

    conn.close()

# Inicialização dos componentes POO para admin
admin_repository = AdminRepository(conectar_banco)
admin_service = AdminService(admin_repository)
admin_controller = AdminController(admin_service)

# Página inicial
@app.route('/')
def pagina_index():
    return render_template('index.html')

# Página de login
@app.route('/login', methods=['GET', 'POST'])
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
            return redirect(url_for('pagina_index'))
        else:
            flash('CPF ou senha incorretos. Tente novamente.')

    return render_template('login.html')

# Página de cadastro
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

# Página de cisternas (temporária)
@app.route('/cisternas')
def pagina_cisternas():
    return '<h1>Página de Cisternas (em construção)</h1>'

# Página de acompanhamento de entrega
@app.route('/acompanhar')
def pagina_acompanhar():
    return render_template('acompanhar_entrega.html')

# Página de detalhes da entrega
@app.route('/detalhe')
def pagina_detalhe():
    return render_template('detalhe-entrega.html')




 # (⁠◠⁠‿⁠・⁠)⁠—⁠☆
#Alteraçoes do Admin     ✧⁠◝⁠(⁠⁰⁠▿⁠⁰⁠)⁠◜⁠✧

# Logout do usuário (adicionado apenas esta rota que faltava)
@app.route('/logout')
def logout_usuario():
    session.pop('id_usuario', None)
    flash('Logout realizado com sucesso!')
    return redirect(url_for('pagina_index'))

# Página de login do admin
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        cpf_digitado = request.form['cpf']
        senha_digitada = request.form['senha']
        sucesso, mensagem, admin = admin_controller.processar_login(cpf_digitado, senha_digitada)
        
        if sucesso:
            session['id_admin'] = admin.id
            session['admin_logado'] = True
            flash(mensagem)
            return redirect(url_for('admin_dashboard'))
        else:
            flash(mensagem)
    return render_template('admin_login.html')

# Dashboard do admin
@app.route('/admin/dashboard')
def admin_dashboard():
    if not admin_controller.verificar_acesso():
        return redirect(url_for('admin_login'))  
    return render_template('admin_dashboard.html')

# Listar usuários
@app.route('/admin/usuarios')
def listar_usuarios():
    if not admin_controller.verificar_acesso():
        return redirect(url_for('admin_login'))   
    usuarios = admin_service.listar_usuarios()
    return render_template('admin_usuarios.html', usuarios=usuarios)

# Adicionar usuário
@app.route('/admin/usuarios/adicionar', methods=['GET', 'POST'])
def adicionar_usuario():
    if not admin_controller.verificar_acesso():
        return redirect(url_for('admin_login'))   
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        senha = request.form['senha']
        tipo = request.form['tipo']
     
        sucesso, mensagem = admin_controller.processar_adicionar_usuario(nome, cpf, senha, tipo)
        flash(mensagem)     
        if sucesso:
            return redirect(url_for('listar_usuarios')) 
    return render_template('admin_adicionar_usuario.html')

# Editar usuário
@app.route('/admin/usuarios/editar/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    if not admin_controller.verificar_acesso():
        return redirect(url_for('admin_login'))   
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        senha = request.form['senha']
        tipo = request.form['tipo']      
        sucesso, mensagem = admin_controller.processar_editar_usuario(id, nome, cpf, senha, tipo)
        flash(mensagem)      
        if sucesso:
            return redirect(url_for('listar_usuarios')) 
    usuario = admin_service.obter_usuario(id)
    if not usuario:
        flash('Usuário não encontrado.')
        return redirect(url_for('listar_usuarios'))    
    return render_template('admin_editar_usuario.html', usuario=usuario)

# Excluir usuário
@app.route('/admin/usuarios/excluir/<int:id>', methods=['POST'])
def excluir_usuario(id):
    if not admin_controller.verificar_acesso():
        return redirect(url_for('admin_login')) 
    admin_atual_id = session.get('id_admin')
    sucesso, mensagem = admin_controller.processar_excluir_usuario(id, admin_atual_id)
    flash(mensagem)    
    return redirect(url_for('listar_usuarios'))

# Adicionando novo admin
@app.route('/admin/adicionar', methods=['GET', 'POST'])
def adicionar_admin():
    if not admin_controller.verificar_acesso():
        return redirect(url_for('admin_login'))    
    if request.method == 'POST':
        nome = request.form['nome']
        identificador = request.form['identificador']
        senha = request.form['senha']
        try:
            banco = conectar_banco()
            banco.execute(
                'INSERT INTO usuarios (nome, cpf, senha, tipo) VALUES (?, ?, ?, ?)',
                (nome, f"fluir_admin_{identificador}", senha, 'admin')
            )
            banco.commit()
            banco.close()
            flash('Administrador adicionado com sucesso!')
            return redirect(url_for('listar_usuarios'))
        except sqlite3.IntegrityError:
            flash('Erro: Identificador de admin já cadastrado no sistema.')
        except Exception as e:
            flash(f'Erro ao adicionar administrador: {str(e)}')
    return render_template('admin_adicionar_admin.html')

# Logout do admin
@app.route('/admin/logout')
def admin_logout():
    session.pop('id_admin', None)
    session.pop('admin_logado', None)
    flash('Logout de administrador realizado com sucesso!')
    return redirect(url_for('pagina_index'))

# Inicia a aplicação
if __name__ == '__main__':
    criar_tabela_usuarios()
    app.run(debug=True)