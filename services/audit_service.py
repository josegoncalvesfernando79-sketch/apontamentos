import json
from datetime import datetime


def log_audit(conn, tabela, registro_id, acao, dados_antes, dados_depois, usuario_id):
    conn.execute(
        """
        INSERT INTO auditoria (tabela, registro_id, acao, dados_antes, dados_depois, usuario_id, data_hora)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tabela,
            registro_id,
            acao,
            json.dumps(dados_antes, ensure_ascii=False) if dados_antes else None,
            json.dumps(dados_depois, ensure_ascii=False) if dados_depois else None,
            usuario_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
