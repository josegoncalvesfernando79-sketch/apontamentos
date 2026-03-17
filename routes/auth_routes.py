from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from models.db import get_conn
from services.auth_service import verify_password

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        senha = request.form.get("senha", "")
        with get_conn(current_app.config["DATABASE"]) as conn:
            row = conn.execute("SELECT * FROM usuarios WHERE usuario = ? AND ativo = 1", (usuario,)).fetchone()
        if not row or not verify_password(senha, row["senha_hash"]):
            flash("Usuário ou senha inválidos.", "danger")
            return render_template("login.html")

        session["user_id"] = row["id"]
        session["nome"] = row["nome"]
        session["perfil"] = row["perfil"]
        session["setor_id"] = row["setor_id"]
        flash("Login realizado com sucesso.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Sessão encerrada.", "info")
    return redirect(url_for("auth.login"))
