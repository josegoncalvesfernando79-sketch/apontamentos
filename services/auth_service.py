from functools import wraps

import bcrypt
from flask import redirect, session, url_for, flash


def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Faça login para acessar o sistema.", "warning")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("perfil") != "admin":
            flash("Acesso restrito ao administrador.", "danger")
            return redirect(url_for("main.dashboard"))
        return fn(*args, **kwargs)

    return wrapper
