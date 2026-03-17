import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta

import bcrypt


@contextmanager
def get_conn(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path):
    with get_conn(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                usuario TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL,
                perfil TEXT NOT NULL CHECK(perfil IN ('admin', 'encarregado')),
                setor_id INTEGER,
                ativo INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(setor_id) REFERENCES setores(id)
            );

            CREATE TABLE IF NOT EXISTS setores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                descricao TEXT,
                ativo INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS funcionarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                matricula TEXT NOT NULL UNIQUE,
                cargo TEXT,
                setor_id INTEGER NOT NULL,
                ativo INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(setor_id) REFERENCES setores(id)
            );

            CREATE TABLE IF NOT EXISTS frequencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                funcionario_id INTEGER NOT NULL,
                data TEXT NOT NULL,
                hora_entrada TEXT,
                hora_saida TEXT,
                registro_manual INTEGER NOT NULL DEFAULT 0,
                registrado_por INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(funcionario_id) REFERENCES funcionarios(id),
                FOREIGN KEY(registrado_por) REFERENCES usuarios(id),
                UNIQUE(funcionario_id, data)
            );

            CREATE TABLE IF NOT EXISTS ocorrencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                funcionario_id INTEGER NOT NULL,
                tipo TEXT NOT NULL CHECK(tipo IN ('Falta', 'Férias', 'Abono', 'Licença')),
                data_inicio TEXT NOT NULL,
                data_fim TEXT NOT NULL,
                observacoes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(funcionario_id) REFERENCES funcionarios(id)
            );

            CREATE TABLE IF NOT EXISTS plantoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                funcionario_id INTEGER NOT NULL,
                data TEXT NOT NULL,
                hora_inicio TEXT NOT NULL,
                hora_fim TEXT NOT NULL,
                observacoes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(funcionario_id) REFERENCES funcionarios(id)
            );

            CREATE TABLE IF NOT EXISTS auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tabela TEXT NOT NULL,
                registro_id INTEGER NOT NULL,
                acao TEXT NOT NULL CHECK(acao IN ('INSERT', 'UPDATE')),
                dados_antes TEXT,
                dados_depois TEXT,
                usuario_id INTEGER,
                data_hora TEXT NOT NULL,
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
            );
            """
        )


def now_iso():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def seed_data(db_path):
    with get_conn(db_path) as conn:
        existing = conn.execute("SELECT COUNT(*) AS total FROM usuarios").fetchone()["total"]
        if existing > 0:
            return

        ts = now_iso()
        conn.execute(
            "INSERT INTO setores (nome, descricao, created_at, updated_at) VALUES (?, ?, ?, ?)",
            ("Administração", "Setor administrativo", ts, ts),
        )
        conn.execute(
            "INSERT INTO setores (nome, descricao, created_at, updated_at) VALUES (?, ?, ?, ?)",
            ("Saúde", "Unidades de saúde", ts, ts),
        )

        setor_admin = conn.execute("SELECT id FROM setores WHERE nome = 'Administração'").fetchone()["id"]
        setor_saude = conn.execute("SELECT id FROM setores WHERE nome = 'Saúde'").fetchone()["id"]

        conn.execute(
            """
            INSERT INTO usuarios (nome, usuario, senha_hash, perfil, setor_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("Administrador Geral", "admin", hash_password("admin123"), "admin", setor_admin, ts, ts),
        )
        conn.execute(
            """
            INSERT INTO usuarios (nome, usuario, senha_hash, perfil, setor_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("Encarregado Saúde", "encarregado", hash_password("enc123"), "encarregado", setor_saude, ts, ts),
        )

        conn.execute(
            """
            INSERT INTO funcionarios (nome, matricula, cargo, setor_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("João Silva", "MAT001", "Analista", setor_admin, ts, ts),
        )
        conn.execute(
            """
            INSERT INTO funcionarios (nome, matricula, cargo, setor_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("Maria Souza", "MAT002", "Enfermeira", setor_saude, ts, ts),
        )

        usuario_admin = conn.execute("SELECT id FROM usuarios WHERE usuario = 'admin'").fetchone()["id"]
        funcionario_maria = conn.execute("SELECT id FROM funcionarios WHERE matricula = 'MAT002'").fetchone()["id"]

        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        conn.execute(
            """
            INSERT INTO frequencias (funcionario_id, data, hora_entrada, hora_saida, registro_manual, registrado_por, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (funcionario_maria, today, "08:00", None, 1, usuario_admin, ts, ts),
        )
        conn.execute(
            """
            INSERT INTO plantoes (funcionario_id, data, hora_inicio, hora_fim, observacoes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (funcionario_maria, tomorrow, "19:00", "07:00", "Plantão noturno", ts, ts),
        )

        # Auditoria inicial dos dados base
        rows = conn.execute("SELECT id, nome FROM setores").fetchall()
        for row in rows:
            conn.execute(
                "INSERT INTO auditoria (tabela, registro_id, acao, dados_antes, dados_depois, usuario_id, data_hora) VALUES (?, ?, 'INSERT', NULL, ?, NULL, ?)",
                ("setores", row["id"], json.dumps(dict(row), ensure_ascii=False), ts),
            )
