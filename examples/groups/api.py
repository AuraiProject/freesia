from freesia import Group, jsonify

api = Group("api", "/api")

persons_age = {
    "mike": 42,
    "mary": 39
}


@api.route("/<name>")
async def name(request, name):
    if name in persons_age:
        return await jsonify({
            name: persons_age[name]
        })
    else:
        return await jsonify(None)
