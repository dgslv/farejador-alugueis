"""O painel: Flask + Jinja. `create_app()` monta a aplicação; as rotas ficam em routes.py."""

from flask import Flask


def create_app() -> Flask:
    # templates/ e static/ ficam dentro deste pacote, então funcionam igual
    # rodando do código-fonte, instalado via pip ou dentro do PyInstaller.
    app = Flask(__name__, template_folder="templates", static_folder="static")
    from farejador.web.routes import bp

    app.register_blueprint(bp)
    return app
