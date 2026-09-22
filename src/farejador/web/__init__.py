"""The dashboard: Flask + Jinja. `create_app()` builds the application; routes live in routes.py."""

from flask import Flask


def create_app() -> Flask:
    # templates/ and static/ live inside this package, so they resolve the same
    # way from source, installed via pip, or inside the PyInstaller bundle.
    app = Flask(__name__, template_folder="templates", static_folder="static")
    from farejador.web.routes import bp

    app.register_blueprint(bp)
    return app
