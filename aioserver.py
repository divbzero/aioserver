import io
import json
from functools import partial, reduce, wraps

from aiohttp import web

__all__ = ['Application']

class Application(web.Application):

    def route(self, path):
        return compose(tee(partial(self.router.add_route, '*', path)), self.wrap_handler)
    def options(self, path):
        return compose(tee(partial(self.router.add_options, path)), self.wrap_handler)
    def head(self, path):
        return compose(tee(partial(self.router.add_head, path)), self.wrap_handler)
    def get(self, path):
        return compose(tee(partial(self.router.add_get, path)), self.wrap_handler)
    def post(self, path):
        return compose(tee(partial(self.router.add_post, path)), self.wrap_handler)
    def put(self, path):
        return compose(tee(partial(self.router.add_put, path)), self.wrap_handler)
    def patch(self, path):
        return compose(tee(partial(self.router.add_patch, path)), self.wrap_handler)
    def delete(self, path):
        return compose(tee(partial(self.router.add_delete, path)), self.wrap_handler)

    def wrap_handler(self, handler):
        @wraps(handler)
        async def wrapped_handler(*args, **kargs):
            return self.make_response(await handler(*args, **kargs))
        return wrapped_handler

    def make_response(self, value):
        if isinstance(value, int):
            # format: <status>
            # example: return 500
            status, headers, value = value, {}, None
        elif not isinstance(value, tuple):
            # format: <body>
            # example: return {'message': 'Hello, World!'}
            status, headers, value = 200, {}, value
        elif len(value) == 2:
            # format: <status>, <body>
            # example: return 404, {'message': 'Not Found'}
            status, value = value
            headers = {}
        elif len(value) == 3:
            # format: <status>, <headers>, <body>
            # example: return 302, {'Location': 'https://www.example.com/'}, {'message': 'Found'}
            status, headers, value = value
        else:
            raise TypeError()
        if value is None:
            return web.Response(status=status, headers=headers)
        elif isinstance(value, web.Response):
            value.set_status(status)
            value.headers.update(headers)
            return value
        elif isinstance(value, bytes):
            return web.Response(status=status, headers=headers, body=value)
        elif isinstance(value, str):
            return web.Response(status=status, headers=headers, text=value)
        elif isinstance(value, (dict, list)):
            with io.StringIO() as stream:
                json.dump(value, stream, ensure_ascii=False, allow_nan=False, indent=4, sort_keys=True)
                stream.write('\n')
                return web.Response(status=status, headers=headers, text=stream.getvalue(), content_type='application/json')
        else:
            raise TypeError()

    @property
    def run(self):
        return partial(web.run_app, self)

def compose(*functions):
    return reduce(lambda f, g: lambda x: f(g(x)), functions)

def tee(function):
    @wraps(function)
    def wrapped_function(x):
        function(x)
        return x
    return wrapped_function
