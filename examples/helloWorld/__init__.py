from freesia import Freesia, response

app = Freesia()


@app.route('/')
async def index(request):
    return response("Hello, world!")


@app.route('/hello/<name>')
async def hello(request, name):
    return response("Hello, " + name + "!")


if __name__ == "__main__":
    app.run()
