import io
import json
from functools import partial, reduce, wraps
from xml.etree.ElementTree import ElementTree

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
        # extract <status>, <headers>, <body> from value
        if isinstance(value, int):
            # format: <status>
            # example: return 500
            status, headers, body = value, {}, None
        elif not isinstance(value, tuple):
            # format: <body>
            # example: return {'message': 'Hello, World!'}
            status, headers, body = 200, {}, value
        elif len(value) == 2:
            # format: <status>, <body>
            # example: return 404, {'message': 'Not Found'}
            status, body = value
            headers = {}
        elif len(value) == 3:
            # format: <status>, <headers>, <body>
            # example: return 302, {'Location': 'https://www.example.com/'}, {'message': 'Found'}
            status, headers, body = value
        else:
            raise TypeError()
        # return web response
        if body is None:
            return web.Response(status=status, headers=headers)
        elif isinstance(body, web.Response):
            body.set_status(status)
            body.headers.update(headers)
            return body
        elif isinstance(body, bytes):
            return web.Response(status=status, headers=headers, body=body)
        elif isinstance(body, str):
            return web.Response(status=status, headers=headers, text=body)
        elif isinstance(body, (dict, list)):
            with io.StringIO() as stream:
                json.dump(body, stream, ensure_ascii=False, allow_nan=False, indent=4, sort_keys=True)
                stream.write('\n')
                return web.Response(status=status, headers=headers, text=stream.getvalue(), content_type='application/json')
        elif isinstance(body, ElementTree):
            with io.StringIO() as stream:
                body.write(stream, encoding='unicode', xml_declaration=True)
                return web.Response(status=status, headers=headers, text=stream.getvalue(), content_type='text/xml')
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
