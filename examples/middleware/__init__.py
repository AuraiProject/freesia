from freesia import Freesia

app = Freesia()


@app.route("/<name>")
async def hello(request, name):
    print("enter user handler")
    return "hello, " + name


async def middleware1(request, handler):
    print("enter middleware1")
    res = await handler()
    print("exit middleware1")
    return res + " !"


async def middleware2(request, handler):
    print("enter middleware2")
    res = await handler()
    print("exit middleware2")
    return res + " :D"


app.use([middleware1, middleware2])

if __name__ == "__main__":
    app.run()
