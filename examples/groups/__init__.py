from freesia import Freesia


def create_app():
    app = Freesia()

    from .api import api
    app.register_group(api)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
