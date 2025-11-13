"""WSGI entrypoint used by gunicorn (`webapp.wsgi:app`)."""

from webapp.app import app as app, main


if __name__ == "__main__":
    main()
