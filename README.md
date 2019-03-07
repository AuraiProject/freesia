![freesia](./images/logo.png)

## Introduction
Freesia is a concise and lightweight async web framework. Its api is inspired by Flask.

## Installation
```bash
pip3 install freesia
```

## Docs
You can find the project's detailed API documentation on [here](https://freesia.readthedocs.io/en/latest/?).

## Example
*hello world*
```python
from freesia import Freesia

app = Freesia()

@app.route('/hello/<name>')
async def hello(request, name):
    return "Hello, " + name + "!"

if __name__ == "__main__":
    app.run()
```

*middleware*
```python
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
```

*session*
```python
from freesia import Freesia, set_up_session, get_session, Response
from freesia.session import SimpleCookieSession

app = Freesia()

@app.route("/")
async def hello(request):
    s = await get_session(request)
    if "count" not in s:
        s["count"] = 1
        return Response(text="Hello, stranger!")
    else:
        s["count"] += 1
        return Response(text="I've seen you %d times" % s["count"])

if __name__ == "__main__":
    set_up_session(app, SimpleCookieSession)
    app.run()
```

## More
You can see more exmaple and usags in [docs](https://freesia.readthedocs.io/en/latest/?) and [examples](./examples).