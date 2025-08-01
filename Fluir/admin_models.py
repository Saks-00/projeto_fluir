import sqlite3
from typing import List, Optional, Dict, Any

class Usuario:
    def __init__(self, id: int = None, nome: str = '', cpf: str = '', senha: str = '', tipo: str = 'usuario'):
        self.id = id
        self.nome = nome
        self.cpf = cpf
        self.senha = senha
        self.tipo = tipo
    
    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Usuario':
        return cls(
            id=row['id'],
            nome=row['nome'],
            cpf=row['cpf'],
            senha=row['senha'],
            tipo=row['tipo']
        )
    
    def is_admin(self) -> bool:
        return self.tipo == 'admin'

class AdminRepository:
    def __init__(self, conectar_banco_func):
        self.conectar_banco = conectar_banco_func
    
    def autenticar_admin(self, cpf: str, senha: str) -> Optional[Usuario]:
        banco = self.conectar_banco()
        banco.row_factory = sqlite3.Row
        row = banco.execute(
            'SELECT * FROM usuarios WHERE cpf = ? AND senha = ? AND tipo = "admin"',
            (cpf, senha)
        ).fetchone()
        banco.close()
        
        return Usuario.from_row(row) if row else None
    
    def listar_todos_usuarios(self) -> List[Usuario]:
        banco = self.conectar_banco()
        banco.row_factory = sqlite3.Row
        rows = banco.execute('SELECT * FROM usuarios').fetchall()
        banco.close()
        
        return [Usuario.from_row(row) for row in rows]
    
    def buscar_usuario_por_id(self, id: int) -> Optional[Usuario]:
        banco = self.conectar_banco()
        banco.row_factory = sqlite3.Row
        row = banco.execute('SELECT * FROM usuarios WHERE id = ?', (id,)).fetchone()
        banco.close()
        
        return Usuario.from_row(row) if row else None
    
    def criar_usuario(self, usuario: Usuario) -> bool:
        try:
            banco = self.conectar_banco()
            banco.execute(
                'INSERT INTO usuarios (nome, cpf, senha, tipo) VALUES (?, ?, ?, ?)',
                (usuario.nome, usuario.cpf, usuario.senha, usuario.tipo)
            )
            banco.commit()
            banco.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def atualizar_usuario(self, usuario: Usuario) -> bool:
        try:
            banco = self.conectar_banco()
            banco.execute(
                'UPDATE usuarios SET nome = ?, cpf = ?, senha = ?, tipo = ? WHERE id = ?',
                (usuario.nome, usuario.cpf, usuario.senha, usuario.tipo, usuario.id)
            )
            banco.commit()
            banco.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def excluir_usuario(self, id: int) -> bool:
        banco = self.conectar_banco()
        cursor = banco.execute('DELETE FROM usuarios WHERE id = ?', (id,))
        sucesso = cursor.rowcount > 0
        banco.commit()
        banco.close()
        return sucesso

class AdminService:
    def __init__(self, repository: AdminRepository):
        self.repository = repository
    
    def autenticar(self, cpf: str, senha: str) -> Optional[Usuario]:
        return self.repository.autenticar_admin(cpf, senha)
    
    def listar_usuarios(self) -> List[Usuario]:
        return self.repository.listar_todos_usuarios()
    
    def obter_usuario(self, id: int) -> Optional[Usuario]:
        return self.repository.buscar_usuario_por_id(id)
    
    def criar_usuario(self, nome: str, cpf: str, senha: str, tipo: str) -> tuple[bool, str]:
        usuario = Usuario(nome=nome, cpf=cpf, senha=senha, tipo=tipo)
        
        if self.repository.criar_usuario(usuario):
            return True, "Usuário adicionado com sucesso!"
        else:
            return False, "Erro: CPF já cadastrado no sistema."
    
    def criar_admin(self, nome: str, identificador: str, senha: str) -> tuple[bool, str]:
        cpf_admin = f"fluir_admin_{identificador}"
        usuario = Usuario(nome=nome, cpf=cpf_admin, senha=senha, tipo='admin')
        
        if self.repository.criar_usuario(usuario):
            return True, "Administrador adicionado com sucesso!"
        else:
            return False, "Erro: Identificador de admin já cadastrado no sistema."
    
    def atualizar_usuario(self, id: int, nome: str, cpf: str, senha: str, tipo: str) -> tuple[bool, str]:
        usuario = Usuario(id=id, nome=nome, cpf=cpf, senha=senha, tipo=tipo)
        
        if self.repository.atualizar_usuario(usuario):
            return True, "Usuário atualizado com sucesso!"
        else:
            return False, "Erro: CPF já cadastrado para outro usuário."
    
    def excluir_usuario(self, id: int, admin_atual_id: int) -> tuple[bool, str]:
        if id == admin_atual_id:
            return False, "Não é possível excluir o administrador atual."
        
        if self.repository.excluir_usuario(id):
            return True, "Usuário excluído com sucesso!"
        else:
            return False, "Erro ao excluir usuário."

class AdminController:
    def __init__(self, admin_service: AdminService):
        self.admin_service = admin_service
    
    def verificar_acesso(self) -> bool:
        from flask import session
        return session.get('admin_logado', False) and session.get('id_admin') is not None
    
    def processar_login(self, cpf: str, senha: str) -> tuple[bool, str, Optional[Usuario]]:
        admin = self.admin_service.autenticar(cpf, senha)
        
        if admin:
            return True, "Login de administrador realizado com sucesso!", admin
        else:
            return False, "CPF ou senha incorretos. Acesso negado.", None
    
    def processar_adicionar_usuario(self, nome: str, cpf: str, senha: str, tipo: str) -> tuple[bool, str]:
        return self.admin_service.criar_usuario(nome, cpf, senha, tipo)
    
    def processar_adicionar_admin(self, nome: str, identificador: str, senha: str) -> tuple[bool, str]:
        return self.admin_service.criar_admin(nome, identificador, senha)
    
    def processar_editar_usuario(self, id: int, nome: str, cpf: str, senha: str, tipo: str) -> tuple[bool, str]:
        return self.admin_service.atualizar_usuario(id, nome, cpf, senha, tipo)
    
    def processar_excluir_usuario(self, id: int, admin_atual_id: int) -> tuple[bool, str]:
        return self.admin_service.excluir_usuario(id, admin_atual_id)