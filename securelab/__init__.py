"""Secure Flask Lab, um app de anotações escrito com as defesas no lugar certo.

Cada defesa está marcada no código com um comentário DEFESA para facilitar
a leitura e a conversa em entrevista.
"""
from __future__ import annotations

import os
import secrets
import sqlite3
from functools import wraps
from pathlib import Path

from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL,
    senha_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dono_id INTEGER NOT NULL REFERENCES usuarios(id),
    titulo TEXT NOT NULL,
    texto TEXT NOT NULL
);
"""


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        DATABASE=str(Path(app.instance_path) / "lab.db"),
        # DEFESA cookie de sessão fora do alcance do JavaScript e de outros sites
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    # banco ----------------------------------------------------------------
    def db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        conn = g.pop("db", None)
        if conn is not None:
            conn.close()

    with app.app_context():
        db().executescript(SCHEMA)

    app.db = db  # usado nos testes

    # CSRF -----------------------------------------------------------------
    def csrf_token() -> str:
        if "csrf" not in session:
            session["csrf"] = secrets.token_urlsafe(32)
        return session["csrf"]

    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def check_csrf():
        # DEFESA todo POST precisa trazer o token que só a nossa página conhece
        if request.method == "POST":
            sent = request.form.get("csrf", "")
            expected = session.get("csrf", "")
            # o "not expected" importa, sem ele vazio == vazio passaria depois do session.clear()
            if not expected or not secrets.compare_digest(sent, expected):
                abort(400, "token CSRF inválido")

    # cabeçalhos de segurança ------------------------------------------------
    @app.after_request
    def security_headers(resp):
        resp.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'; form-action 'self'"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return resp

    # autenticação ---------------------------------------------------------
    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped

    @app.route("/registrar", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            nome = request.form.get("nome", "").strip()
            senha = request.form.get("senha", "")
            if not nome or len(senha) < 10:
                flash("nome obrigatório e senha com pelo menos 10 caracteres")
            else:
                try:
                    # DEFESA senha guardada com hash lento e salt (scrypt do werkzeug)
                    db().execute("INSERT INTO usuarios (nome, senha_hash) VALUES (?, ?)",
                                 (nome, generate_password_hash(senha)))
                    db().commit()
                    return redirect(url_for("login"))
                except sqlite3.IntegrityError:
                    flash("esse nome já existe")
        return render_template("form.html", titulo="Criar conta", acao=url_for("register"))

    @app.route("/entrar", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            row = db().execute("SELECT * FROM usuarios WHERE nome = ?", (request.form.get("nome", ""),)).fetchone()
            if row and check_password_hash(row["senha_hash"], request.form.get("senha", "")):
                session.clear()  # DEFESA nova sessão no login evita session fixation
                session["user_id"], session["nome"] = row["id"], row["nome"]
                return redirect(url_for("index"))
            # DEFESA mesma mensagem para usuário inexistente e senha errada
            flash("usuário ou senha incorretos")
        return render_template("form.html", titulo="Entrar", acao=url_for("login"))

    @app.post("/sair")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    # notas ----------------------------------------------------------------
    @app.route("/")
    @login_required
    def index():
        termo = request.args.get("busca", "")
        # DEFESA consulta parametrizada, o termo nunca vira parte do SQL
        notas = db().execute(
            "SELECT id, titulo FROM notas WHERE dono_id = ? AND titulo LIKE ? ORDER BY id DESC",
            (session["user_id"], f"%{termo}%"),
        ).fetchall()
        return render_template("index.html", notas=notas, busca=termo)

    @app.post("/notas")
    @login_required
    def create_note():
        titulo = request.form.get("titulo", "").strip()[:120]
        texto = request.form.get("texto", "")[:5000]
        if titulo:
            db().execute("INSERT INTO notas (dono_id, titulo, texto) VALUES (?, ?, ?)",
                         (session["user_id"], titulo, texto))
            db().commit()
        return redirect(url_for("index"))

    @app.route("/notas/<int:nota_id>")
    @login_required
    def show_note(nota_id: int):
        # DEFESA o dono entra no WHERE, então trocar o número na URL não mostra nota alheia (IDOR)
        nota = db().execute("SELECT * FROM notas WHERE id = ? AND dono_id = ?",
                            (nota_id, session["user_id"])).fetchone()
        if nota is None:
            abort(404)  # 404 e não 403, para nem confirmar que a nota existe
        return render_template("nota.html", nota=nota)

    return app
