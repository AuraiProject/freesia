from freesia import Freesia, jsonify

app = Freesia()


@app.route('/')
async def index(request):
    return "Hello, world!", 200, "ok"


@app.route('/hello/<name>')
async def hello(request, name):
    return "Hello, " + name + "!"


@app.route('/echo/<words>')
async def echo(request, words):
    return await jsonify(words)


if __name__ == "__main__":
    app.run()
