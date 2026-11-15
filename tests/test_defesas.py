"""Cada teste confirma que uma defesa está funcionando."""
import pytest

from securelab import create_app


@pytest.fixture
def app(tmp_path):
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "teste.db"), "SECRET_KEY": "teste"})


def token(client):
    client.get("/entrar")
    with client.session_transaction() as s:
        return s["csrf"]


def criar_e_entrar(client, nome, senha="senha-bem-longa"):
    client.post("/registrar", data={"nome": nome, "senha": senha, "csrf": token(client)})
    client.post("/entrar", data={"nome": nome, "senha": senha, "csrf": token(client)})


def nova_nota(client, titulo, texto="x"):
    client.post("/notas", data={"titulo": titulo, "texto": texto, "csrf": token(client)})


def test_precisa_login(app):
    resp = app.test_client().get("/")
    assert resp.status_code == 302 and "/entrar" in resp.headers["Location"]


def test_senha_nao_fica_em_texto_puro(app):
    c = app.test_client()
    criar_e_entrar(c, "ana")
    with app.app_context():
        row = app.db().execute("SELECT senha_hash FROM usuarios WHERE nome='ana'").fetchone()
    assert "senha-bem-longa" not in row["senha_hash"]
    assert row["senha_hash"].startswith(("scrypt:", "pbkdf2:"))


def test_login_errado_tem_mensagem_generica(app):
    c = app.test_client()
    criar_e_entrar(c, "ana")
    c.post("/sair", data={"csrf": token(c)})
    r1 = c.post("/entrar", data={"nome": "ana", "senha": "errada", "csrf": token(c)})
    r2 = c.post("/entrar", data={"nome": "ninguem", "senha": "errada", "csrf": token(c)})
    assert "usuário ou senha incorretos" in r1.get_data(as_text=True)
    assert "usuário ou senha incorretos" in r2.get_data(as_text=True)


def test_busca_trata_aspas_como_texto(app):
    """Caracteres especiais de SQL na busca viram texto comum e não mudam a consulta."""
    c = app.test_client()
    criar_e_entrar(c, "ana")
    nova_nota(c, "nota da ana")
    resp = c.get("/", query_string={"busca": "' OR '1'='1"})
    assert resp.status_code == 200
    assert "nota da ana" not in resp.get_data(as_text=True)


def test_busca_nao_mostra_nota_de_outro_usuario(app):
    a, b = app.test_client(), app.test_client()
    criar_e_entrar(a, "ana")
    nova_nota(a, "segredo da ana")
    criar_e_entrar(b, "bia")
    assert "segredo da ana" not in b.get("/", query_string={"busca": "segredo"}).get_data(as_text=True)


def test_html_do_usuario_sai_escapado(app):
    c = app.test_client()
    criar_e_entrar(c, "ana")
    nova_nota(c, "<b>negrito</b>", "<img src=x>")
    html = c.get("/notas/1").get_data(as_text=True)
    assert "<b>negrito</b>" not in html and "&lt;b&gt;negrito&lt;/b&gt;" in html
    assert "<img src=x>" not in html


def test_nao_acessa_nota_alheia_trocando_o_id(app):
    a, b = app.test_client(), app.test_client()
    criar_e_entrar(a, "ana")
    nova_nota(a, "privada")
    assert a.get("/notas/1").status_code == 200
    criar_e_entrar(b, "bia")
    assert b.get("/notas/1").status_code == 404


def test_post_sem_csrf_e_recusado(app):
    c = app.test_client()
    criar_e_entrar(c, "ana")
    assert c.post("/notas", data={"titulo": "sem token"}).status_code == 400


def test_cabecalhos_de_seguranca(app):
    h = app.test_client().get("/entrar").headers
    assert "default-src 'self'" in h["Content-Security-Policy"]
    assert h["X-Content-Type-Options"] == "nosniff"


def test_cookie_de_sessao_httponly(app):
    c = app.test_client()
    resp = c.get("/entrar")
    cookie = resp.headers.get("Set-Cookie", "")
    assert "HttpOnly" in cookie and "SameSite=Lax" in cookie
