<p align="center"><sub>Secure Flask Lab</sub></p>

---

<p align="center">
  <img src="assets/banner.png" alt="Secure Flask Lab" width="100%">
</p>

<p align="center">
  App Flask com defesas contra SQLi, XSS, IDOR e CSRF, cada uma provada por teste
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-EF4444?style=for-the-badge&logo=python&logoColor=white">
  <img alt="Flask" src="https://img.shields.io/badge/Flask-3-242424?style=for-the-badge&logo=flask&logoColor=white">
  <img alt="OWASP Top 10" src="https://img.shields.io/badge/OWASP-Top%2010-242424?style=for-the-badge">
  <a href="https://github.com/arthurlynow098/secure-flask-lab/actions/workflows/testes.yml"><img alt="Testes" src="https://img.shields.io/github/actions/workflow/status/arthurlynow098/secure-flask-lab/testes.yml?style=for-the-badge&label=testes&color=242424"></a>
</p>

## Sobre o projeto

Eu venho do desenvolvimento back-end, e a maior parte das vulnerabilidades web que estudei nasce de um descuido pequeno de quem escreveu o código. Uma consulta montada com concatenação de texto, um `|safe` esquecido no template, uma rota que confere se o usuário está logado mas não confere se a nota é dele.

O Secure Flask Lab é um app de anotações simples, com cadastro, login e busca, escrito com cada defesa no lugar certo. Todas estão marcadas no código com o comentário `DEFESA`, e **cada uma tem um teste automatizado que prova que ela funciona**. A ideia é ter um projeto que eu consiga abrir numa entrevista e explicar linha por linha.

## Como funciona

| Risco (OWASP Top 10) | Defesa no código | Teste que prova |
|---|---|---|
| **A03 Injection** | Toda consulta usa parâmetros `?` do sqlite3. O que o usuário digita nunca vira SQL | `test_busca_trata_aspas_como_texto` |
| **A03 Injection, XSS** | Autoescape do Jinja ligado e nenhum `\|safe` em conteúdo do usuário, mais CSP restritivo | `test_html_do_usuario_sai_escapado` |
| **A01 Broken Access Control, IDOR** | O `dono_id` da sessão entra no `WHERE`. Responde 404 em vez de 403 para nem confirmar que a nota existe | `test_nao_acessa_nota_alheia_trocando_o_id` |
| **A01, CSRF** | Token aleatório por sessão em todo formulário, comparado em tempo constante | `test_post_sem_csrf_e_recusado` |
| **A02 Cryptographic Failures** | Senha com hash scrypt e salt (`werkzeug.security`) | `test_senha_nao_fica_em_texto_puro` |
| **A07 Authentication Failures** | Mesma mensagem para usuário inexistente e senha errada, sessão renovada no login | `test_login_errado_tem_mensagem_generica` |
| **A05 Security Misconfiguration** | CSP, `nosniff`, `Referrer-Policy`, `Permissions-Policy` e cookie `HttpOnly` com `SameSite` | `test_cabecalhos_de_seguranca` e `test_cookie_de_sessao_httponly` |

## Tecnologias

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3776AB?style=flat-square&amp;logo=python&amp;logoColor=white">
  <img alt="Flask" src="https://img.shields.io/badge/Flask-000000?style=flat-square&amp;logo=flask&amp;logoColor=white">
  <img alt="OWASP Top 10" src="https://img.shields.io/badge/OWASP_Top_10-000000?style=flat-square&amp;logo=owasp&amp;logoColor=white">
  <img alt="pytest" src="https://img.shields.io/badge/pytest-0A9EDC?style=flat-square&amp;logo=pytest&amp;logoColor=white">
</p>

## Executando o código

```bash
git clone https://github.com/arthurlynow098/secure-flask-lab.git
cd secure-flask-lab
pip install flask

flask --app securelab run
# abra http://127.0.0.1:5000/registrar
```

O banco SQLite é criado sozinho na pasta `instance/`. Em produção defina a variável `SECRET_KEY` e `FLASK_ENV=production` para o cookie ganhar a flag `Secure`.

Testes

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

## Exemplo

```text
$ python -m pytest -v

tests/test_defesas.py::test_precisa_login PASSED
tests/test_defesas.py::test_senha_nao_fica_em_texto_puro PASSED
tests/test_defesas.py::test_login_errado_tem_mensagem_generica PASSED
tests/test_defesas.py::test_busca_trata_aspas_como_texto PASSED
tests/test_defesas.py::test_busca_nao_mostra_nota_de_outro_usuario PASSED
tests/test_defesas.py::test_html_do_usuario_sai_escapado PASSED
tests/test_defesas.py::test_nao_acessa_nota_alheia_trocando_o_id PASSED
tests/test_defesas.py::test_post_sem_csrf_e_recusado PASSED
tests/test_defesas.py::test_cabecalhos_de_seguranca PASSED
tests/test_defesas.py::test_cookie_de_sessao_httponly PASSED

10 passed
```

## Estudei por aqui

Segui essas aulas e materiais para entender e aplicar tudo que está aqui.

| Material | O que tirei dele |
|---|---|
| [OWASP Top 10](https://owasp.org/Top10/) | As categorias de risco usadas na tabela acima |
| [PortSwigger Academy, SQL injection](https://portswigger.net/web-security/sql-injection) | Como a injeção acontece e por que parâmetros resolvem |
| [PortSwigger Academy, Cross-site scripting](https://portswigger.net/web-security/cross-site-scripting) | Tipos de XSS e o papel do escape de saída e do CSP |
| [PortSwigger Academy, IDOR](https://portswigger.net/web-security/access-control/idor) | Controle de acesso por objeto |
| [OWASP SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html) | Consultas parametrizadas como defesa principal |
| [Tutorial oficial do Flask](https://flask.palletsprojects.com/en/stable/tutorial/) | Estrutura do app, factory e banco SQLite |

## Licença

Distribuído sob a licença MIT. Veja o arquivo [LICENSE](LICENSE).

<p align="center"><sub>A gravura do banner é a mamangava de Wenceslaus Hollar, de 1646, em domínio público no <a href="https://commons.wikimedia.org/wiki/File%3AWenceslas_Hollar_-_Dragonflies_and_a_bumble_bee_%28State_1%29.jpg">Wikimedia Commons</a>.</sub></p>
