"""WSGI entrypoint used by gunicorn (`pi_service.wsgi:app`)."""

from pi_service.app import app as app, main


if __name__ == "__main__":
    main()

