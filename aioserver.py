import io
import json
from collections import defaultdict
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

    def cors(self, access_control_allow_origin, access_control_expose_headers=[], access_control_allow_credentials=False):
        # define CORS headers
        cors_headers = {}
        cors_headers['Access-Control-Allow-Origin'] = access_control_allow_origin
        if access_control_allow_credentials:
            cors_headers['Access-Control-Allow-Credentials'] = 'true'
        if access_control_expose_headers:
            cors_headers['Access-Control-Expose-Headers'] = ', '.join(access_control_expose_headers)
        # add CORS headers to handler
        def add_cors_headers(handler):
            try:
                headers = handler.__headers__
            except AttributeError:
                headers = handler.__headers__ = {}
            headers.update(cors_headers)
            return handler
        return add_cors_headers

    def wrap_handler(self, handler):
        # get additional headers
        try:
            headers = handler.__headers__
        except AttributeError:
            headers = handler.__headers__ = {}
        # wrap handler to return web response
        @wraps(handler)
        async def wrapped_handler(*args, **kargs):
            return self.make_response(await handler(*args, **kargs), headers)
        return wrapped_handler

    def make_response(self, value, additional_headers={}):
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
        headers.update(additional_headers)
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

    def update_options(self):
        for resource in self.router.resources():
            # gather CORS parameters
            origin = None
            credentials = False
            headers = set()
            methods = set()
            for route in resource:
                try:
                    origin = route.handler.__headers__['Access-Control-Allow-Origin']
                except KeyError:
                    continue
                if route.handler.__headers__.get('Access-Control-Allow-Credentials'):
                    credentials = True
                try:
                    headers.update(route.handler.__headers__['Access-Control-Expose-Headers'].split(', '))
                except KeyError:
                    pass
                methods.add(route.method.upper())
            if 'OPTIONS' in methods or origin is None:
                continue
            else:
                methods.add('OPTIONS')
            # define CORS preflight headers
            cors_preflight_headers = {}
            cors_preflight_headers['Access-Control-Allow-Origin'] = origin
            if credentials:
                cors_preflight_headers['Access-Control-Allow-Credentials'] = 'true'
            if headers:
                cors_preflight_headers['Access-Control-Allow-Headers'] = ', '.join(sorted(headers))
            cors_preflight_headers['Access-Control-Allow-Methods'] = ', '.join(sorted(methods))
            # add CORS preflight headers to OPTIONS handler
            async def options(request):
                return 200
            options.__headers__ = cors_preflight_headers
            resource.add_route('OPTIONS', self.wrap_handler(options))

    @property
    def run(self):
        self.update_options()
        return partial(web.run_app, self)


def compose(*functions):
    return reduce(lambda f, g: lambda x: f(g(x)), functions)

def tee(function):
    @wraps(function)
    def wrapped_function(x):
        function(x)
        return x
    return wrapped_function
