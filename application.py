"""Punto de entrada WSGI.

Elastic Beanstalk (plataforma Python) busca por defecto un objeto `application` en
`application.py`.
"""

from dotenv import load_dotenv

load_dotenv()  # Solo afecta el desarrollo local; en Beanstalk no hay archivo .env.

from blacklist_api import create_app  # noqa: E402

application = create_app()

if __name__ == "__main__":
    application.run(debug=True)
