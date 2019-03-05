from freesia import Freesia, response

app = Freesia()


@app.route('/')
def index(request):
    return response("Hello, world!")


@app.route('/hello/<name>')
def hello(request, name):
    return response("Hello, " + name + "!")


if __name__ == "__main__":
    app.run()
