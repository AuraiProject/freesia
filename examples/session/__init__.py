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
