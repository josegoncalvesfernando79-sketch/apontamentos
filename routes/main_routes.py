from datetime import datetime

from flask import Blueprint, current_app, flash, render_template, request, session, redirect, url_for, make_response

from models.db import get_conn, now_iso
from services.audit_service import log_audit
from services.auth_service import admin_required, login_required

main_bp = Blueprint("main", __name__)


def _sector_filter_sql(alias="f"):
    if session.get("perfil") == "encarregado":
        return f" AND {alias}.setor_id = {int(session.get('setor_id') or 0)} "
    return ""


@main_bp.route("/dashboard")
@login_required
def dashboard():
    today = datetime.now().strftime("%Y-%m-%d")
    sector_filter = _sector_filter_sql("f")
    with get_conn(current_app.config["DATABASE"]) as conn:
        presentes = conn.execute(
            f"""
            SELECT COUNT(*) total
            FROM frequencias fr
            JOIN funcionarios f ON f.id = fr.funcionario_id
            WHERE fr.data = ? AND fr.hora_entrada IS NOT NULL {sector_filter}
            """,
            (today,),
        ).fetchone()["total"]
        ativos = conn.execute(f"SELECT COUNT(*) total FROM funcionarios f WHERE f.ativo = 1 {sector_filter}").fetchone()["total"]
        plantoes = conn.execute(
            f"""
            SELECT p.*, f.nome funcionario_nome
            FROM plantoes p
            JOIN funcionarios f ON f.id = p.funcionario_id
            WHERE p.data = ? {sector_filter.replace('f.', 'f.')}
            ORDER BY p.hora_inicio
            """,
            (today,),
        ).fetchall()
    return render_template("dashboard.html", presentes=presentes, ausentes=max(ativos - presentes, 0), plantoes=plantoes)


@main_bp.route("/setores", methods=["GET", "POST"])
@login_required
@admin_required
def setores():
    db = current_app.config["DATABASE"]
    with get_conn(db) as conn:
        if request.method == "POST":
            nome = request.form["nome"]
            descricao = request.form.get("descricao")
            setor_id = request.form.get("setor_id")
            ts = now_iso()
            if setor_id:
                before = conn.execute("SELECT * FROM setores WHERE id = ?", (setor_id,)).fetchone()
                conn.execute(
                    "UPDATE setores SET nome = ?, descricao = ?, updated_at = ? WHERE id = ?",
                    (nome, descricao, ts, setor_id),
                )
                after = conn.execute("SELECT * FROM setores WHERE id = ?", (setor_id,)).fetchone()
                log_audit(conn, "setores", setor_id, "UPDATE", dict(before), dict(after), session["user_id"])
                flash("Setor atualizado.", "success")
            else:
                cursor = conn.execute(
                    "INSERT INTO setores (nome, descricao, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (nome, descricao, ts, ts),
                )
                row_id = cursor.lastrowid
                after = conn.execute("SELECT * FROM setores WHERE id = ?", (row_id,)).fetchone()
                log_audit(conn, "setores", row_id, "INSERT", None, dict(after), session["user_id"])
                flash("Setor criado.", "success")
            return redirect(url_for("main.setores"))
        rows = conn.execute("SELECT * FROM setores ORDER BY nome").fetchall()
    return render_template("setores.html", setores=rows)


@main_bp.route("/funcionarios", methods=["GET", "POST"])
@login_required
def funcionarios():
    db = current_app.config["DATABASE"]
    with get_conn(db) as conn:
        if request.method == "POST":
            ts = now_iso()
            funcionario_id = request.form.get("funcionario_id")
            payload = (
                request.form["nome"],
                request.form["matricula"],
                request.form.get("cargo"),
                request.form["setor_id"],
                1 if request.form.get("ativo") == "on" else 0,
            )
            if funcionario_id:
                before = conn.execute("SELECT * FROM funcionarios WHERE id = ?", (funcionario_id,)).fetchone()
                conn.execute(
                    """
                    UPDATE funcionarios
                    SET nome = ?, matricula = ?, cargo = ?, setor_id = ?, ativo = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (*payload, ts, funcionario_id),
                )
                after = conn.execute("SELECT * FROM funcionarios WHERE id = ?", (funcionario_id,)).fetchone()
                log_audit(conn, "funcionarios", funcionario_id, "UPDATE", dict(before), dict(after), session["user_id"])
                flash("Funcionário atualizado.", "success")
            else:
                cursor = conn.execute(
                    """
                    INSERT INTO funcionarios (nome, matricula, cargo, setor_id, ativo, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (*payload, ts, ts),
                )
                row_id = cursor.lastrowid
                after = conn.execute("SELECT * FROM funcionarios WHERE id = ?", (row_id,)).fetchone()
                log_audit(conn, "funcionarios", row_id, "INSERT", None, dict(after), session["user_id"])
                flash("Funcionário cadastrado.", "success")
            return redirect(url_for("main.funcionarios"))

        sector_filter = _sector_filter_sql("f")
        funcionarios_rows = conn.execute(
            f"""
            SELECT f.*, s.nome setor_nome
            FROM funcionarios f
            JOIN setores s ON s.id = f.setor_id
            WHERE 1=1 {sector_filter}
            ORDER BY f.nome
            """
        ).fetchall()
        setores_rows = conn.execute("SELECT * FROM setores WHERE ativo = 1 ORDER BY nome").fetchall()
    return render_template("funcionarios.html", funcionarios=funcionarios_rows, setores=setores_rows)


@main_bp.route("/frequencias", methods=["GET", "POST"])
@login_required
def frequencias():
    db = current_app.config["DATABASE"]
    with get_conn(db) as conn:
        if request.method == "POST":
            funcionario_id = request.form["funcionario_id"]
            data = request.form["data"]
            entrada = request.form.get("hora_entrada")
            saida = request.form.get("hora_saida")
            ts = now_iso()
            existing = conn.execute(
                "SELECT * FROM frequencias WHERE funcionario_id = ? AND data = ?",
                (funcionario_id, data),
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE frequencias SET hora_entrada = ?, hora_saida = ?, registro_manual = 1, registrado_por = ?, updated_at = ? WHERE id = ?",
                    (entrada, saida, session["user_id"], ts, existing["id"]),
                )
                after = conn.execute("SELECT * FROM frequencias WHERE id = ?", (existing["id"],)).fetchone()
                log_audit(conn, "frequencias", existing["id"], "UPDATE", dict(existing), dict(after), session["user_id"])
                flash("Frequência atualizada.", "success")
            else:
                cursor = conn.execute(
                    """
                    INSERT INTO frequencias (funcionario_id, data, hora_entrada, hora_saida, registro_manual, registrado_por, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 1, ?, ?, ?)
                    """,
                    (funcionario_id, data, entrada, saida, session["user_id"], ts, ts),
                )
                row_id = cursor.lastrowid
                after = conn.execute("SELECT * FROM frequencias WHERE id = ?", (row_id,)).fetchone()
                log_audit(conn, "frequencias", row_id, "INSERT", None, dict(after), session["user_id"])
                flash("Frequência registrada.", "success")
            return redirect(url_for("main.frequencias"))

        filtro_data = request.args.get("data")
        filtro_mes = request.args.get("mes")
        filtro_funcionario = request.args.get("funcionario_id")
        query = """
            SELECT fr.*, f.nome funcionario_nome
            FROM frequencias fr
            JOIN funcionarios f ON f.id = fr.funcionario_id
            WHERE 1=1
        """
        params = []
        if session.get("perfil") == "encarregado":
            query += " AND f.setor_id = ?"
            params.append(session.get("setor_id"))
        if filtro_data:
            query += " AND fr.data = ?"
            params.append(filtro_data)
        if filtro_mes:
            query += " AND substr(fr.data, 1, 7) = ?"
            params.append(filtro_mes)
        if filtro_funcionario:
            query += " AND fr.funcionario_id = ?"
            params.append(filtro_funcionario)
        query += " ORDER BY fr.data DESC, f.nome"

        registros = conn.execute(query, tuple(params)).fetchall()
        funcionarios_rows = conn.execute(
            f"SELECT f.* FROM funcionarios f WHERE f.ativo = 1 {_sector_filter_sql('f')} ORDER BY f.nome"
        ).fetchall()
    return render_template("frequencias.html", registros=registros, funcionarios=funcionarios_rows)


@main_bp.route("/ocorrencias", methods=["GET", "POST"])
@login_required
def ocorrencias():
    db = current_app.config["DATABASE"]
    with get_conn(db) as conn:
        if request.method == "POST":
            ocorrencia_id = request.form.get("ocorrencia_id")
            data = (
                request.form["funcionario_id"],
                request.form["tipo"],
                request.form["data_inicio"],
                request.form["data_fim"],
                request.form.get("observacoes"),
            )
            ts = now_iso()
            if ocorrencia_id:
                before = conn.execute("SELECT * FROM ocorrencias WHERE id = ?", (ocorrencia_id,)).fetchone()
                conn.execute(
                    "UPDATE ocorrencias SET funcionario_id=?, tipo=?, data_inicio=?, data_fim=?, observacoes=?, updated_at=? WHERE id=?",
                    (*data, ts, ocorrencia_id),
                )
                after = conn.execute("SELECT * FROM ocorrencias WHERE id = ?", (ocorrencia_id,)).fetchone()
                log_audit(conn, "ocorrencias", ocorrencia_id, "UPDATE", dict(before), dict(after), session["user_id"])
                flash("Ocorrência atualizada.", "success")
            else:
                cursor = conn.execute(
                    "INSERT INTO ocorrencias (funcionario_id, tipo, data_inicio, data_fim, observacoes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (*data, ts, ts),
                )
                row_id = cursor.lastrowid
                after = conn.execute("SELECT * FROM ocorrencias WHERE id = ?", (row_id,)).fetchone()
                log_audit(conn, "ocorrencias", row_id, "INSERT", None, dict(after), session["user_id"])
                flash("Ocorrência registrada.", "success")
            return redirect(url_for("main.ocorrencias"))

        rows = conn.execute(
            f"""
            SELECT o.*, f.nome funcionario_nome
            FROM ocorrencias o
            JOIN funcionarios f ON f.id = o.funcionario_id
            WHERE 1=1 {_sector_filter_sql('f')}
            ORDER BY o.data_inicio DESC
            """
        ).fetchall()
        funcionarios_rows = conn.execute(
            f"SELECT * FROM funcionarios f WHERE f.ativo = 1 {_sector_filter_sql('f')} ORDER BY f.nome"
        ).fetchall()
    return render_template("ocorrencias.html", ocorrencias=rows, funcionarios=funcionarios_rows)


@main_bp.route("/plantoes", methods=["GET", "POST"])
@login_required
def plantoes():
    db = current_app.config["DATABASE"]
    with get_conn(db) as conn:
        if request.method == "POST":
            plantao_id = request.form.get("plantao_id")
            data = (
                request.form["funcionario_id"],
                request.form["data"],
                request.form["hora_inicio"],
                request.form["hora_fim"],
                request.form.get("observacoes"),
            )
            ts = now_iso()
            if plantao_id:
                before = conn.execute("SELECT * FROM plantoes WHERE id = ?", (plantao_id,)).fetchone()
                conn.execute(
                    "UPDATE plantoes SET funcionario_id=?, data=?, hora_inicio=?, hora_fim=?, observacoes=?, updated_at=? WHERE id=?",
                    (*data, ts, plantao_id),
                )
                after = conn.execute("SELECT * FROM plantoes WHERE id = ?", (plantao_id,)).fetchone()
                log_audit(conn, "plantoes", plantao_id, "UPDATE", dict(before), dict(after), session["user_id"])
                flash("Plantão atualizado.", "success")
            else:
                cursor = conn.execute(
                    "INSERT INTO plantoes (funcionario_id, data, hora_inicio, hora_fim, observacoes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (*data, ts, ts),
                )
                row_id = cursor.lastrowid
                after = conn.execute("SELECT * FROM plantoes WHERE id = ?", (row_id,)).fetchone()
                log_audit(conn, "plantoes", row_id, "INSERT", None, dict(after), session["user_id"])
                flash("Plantão cadastrado.", "success")
            return redirect(url_for("main.plantoes"))

        rows = conn.execute(
            f"""
            SELECT p.*, f.nome funcionario_nome
            FROM plantoes p
            JOIN funcionarios f ON f.id = p.funcionario_id
            WHERE 1=1 {_sector_filter_sql('f')}
            ORDER BY p.data DESC, p.hora_inicio
            """
        ).fetchall()
        funcionarios_rows = conn.execute(
            f"SELECT * FROM funcionarios f WHERE f.ativo = 1 {_sector_filter_sql('f')} ORDER BY f.nome"
        ).fetchall()
    return render_template("plantoes.html", plantoes=rows, funcionarios=funcionarios_rows)


@main_bp.route("/auditoria")
@login_required
@admin_required
def auditoria():
    with get_conn(current_app.config["DATABASE"]) as conn:
        rows = conn.execute(
            """
            SELECT a.*, u.nome usuario_nome
            FROM auditoria a
            LEFT JOIN usuarios u ON u.id = a.usuario_id
            ORDER BY a.data_hora DESC
            LIMIT 300
            """
        ).fetchall()
    return render_template("auditoria.html", auditorias=rows)


@main_bp.route("/relatorios")
@login_required
def relatorios():
    tipo = request.args.get("tipo", "setor")
    formato = request.args.get("formato", "csv")
    mes = request.args.get("mes", datetime.now().strftime("%Y-%m"))
    db = current_app.config["DATABASE"]
    with get_conn(db) as conn:
        if tipo == "funcionario":
            rows = conn.execute(
                f"""
                SELECT f.nome, f.matricula, fr.data, fr.hora_entrada, fr.hora_saida
                FROM frequencias fr
                JOIN funcionarios f ON f.id = fr.funcionario_id
                WHERE substr(fr.data,1,7)=? {_sector_filter_sql('f')}
                ORDER BY f.nome, fr.data
                """,
                (mes,),
            ).fetchall()
            headers = ["nome", "matricula", "data", "hora_entrada", "hora_saida"]
        else:
            rows = conn.execute(
                f"""
                SELECT s.nome setor, COUNT(f.id) funcionarios_ativos
                FROM setores s
                LEFT JOIN funcionarios f ON f.setor_id = s.id AND f.ativo = 1
                GROUP BY s.id
                ORDER BY s.nome
                """
            ).fetchall()
            headers = ["setor", "funcionarios_ativos"]

    if formato == "pdf":
        html = render_template("relatorio_pdf.html", rows=rows, headers=headers, mes=mes, tipo=tipo)
        response = make_response(html)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = f"attachment; filename=relatorio_{tipo}_{mes}.pdf"
        return response

    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([row[h] for h in headers])
    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv"
    response.headers["Content-Disposition"] = f"attachment; filename=relatorio_{tipo}_{mes}.csv"
    return response
