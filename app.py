import os

from flask import Flask

import csrf
import db
from config import Config


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY não definida. Configure a variável de ambiente SECRET_KEY "
            "antes de iniciar o servidor."
        )

    os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)

    import auth
    import main
    import orcamentos

    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(orcamentos.bp)

    with app.app_context():
        db.init_db()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
