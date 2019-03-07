from freesia import Freesia, MethodView


class MyView(MethodView):
    async def get(self, request, message):
        return message.lower().replace("you", "I").replace("me", "you").replace("hello", "hi")


app = Freesia()
app.add_route("/say/<message>", view_func=MyView.as_view("ai"))

if __name__ == "__main__":
    app.run()
