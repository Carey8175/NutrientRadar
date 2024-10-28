from SystemCode.server.sanic_api import app


if __name__ == '__main__':
    app.run(
        host="0.0.0.0",
        port=18080,
        access_log=False,
        workers=3
    )