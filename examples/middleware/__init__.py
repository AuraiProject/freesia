from freesia import Freesia

app = Freesia()


@app.route("/<name>")
async def hello(request, name):
    print("enter user handler")
    return "hello, " + name + "!"


async def add_smiling_face(request, handler):
    print("enter middleware")
    res = await handler()
    print("exit middleware")
    return res + " :D"


app.use([add_smiling_face])

if __name__ == "__main__":
    app.run()
