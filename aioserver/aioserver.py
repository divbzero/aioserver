import inspect
import io
import json
from collections import defaultdict
from functools import partial, reduce, wraps
from xml.etree.ElementTree import ElementTree

from aiohttp import web

__all__ = ['Application']


class Application(web.Application):

    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self.handler_middlewares = []
        try:
            from . import middleware
        except ImportError:
            return
        for name in middleware.__all__:
            setattr(self, name, compose(self.middleware, getattr(middleware, name)))

    def route(self, path, method='*'):
        return partial(self.add_route, method, path)
    def options(self, path):
        return partial(self.add_route, 'OPTIONS', path)
    def head(self, path):
        return partial(self.add_route, 'HEAD', path)
    def get(self, path):
        return partial(self.add_route, 'GET', path)
    def post(self, path):
        return partial(self.add_route, 'POST', path)
    def put(self, path):
        return partial(self.add_route, 'PUT', path)
    def patch(self, path):
        return partial(self.add_route, 'PATCH', path)
    def delete(self, path):
        return partial(self.add_route, 'DELETE', path)

    def use(self, middleware_handler):
        '''Add middleware to all request handlers.'''
        argnames = list(inspect.signature(middleware_handler).parameters)
        if argnames == ['request', 'handler']:
            # request middleware accepts (request, handler) arguments and returns response
            self.middlewares.append(web.middleware(middleware_handler))
        elif argnames[0:1] == ['handler']:
            # handler middleware accepts (handler) argument and returns handler
            self.handler_middlewares.append(middleware_handler)
        else:
            raise ValueError('middleware_handler function signature must be (request, handler) or (handler)')
        return middleware_handler

    def middleware(self, middleware_handler):
        '''Decorator to add middleware to a specific request handler.
        
        The middleware handler should take the `request` object and the
        request `handler` as arguments and return a response:
        
            @app.middleware
            async def always_ok(request, handler):
                response = await handler(request)
                response.set_status(200, 'OK')
                return response
        
        The middleware can then be applied to request handlers:
        
            @always_ok
            @app.get('/not-found-but-still-ok')
            async def not_found_but_still_ok(request):
                return 404, {'message': 'Not found but still OK!'}
                
        '''
        argnames = list(inspect.signature(middleware_handler).parameters)
        if argnames == ['request', 'handler']:
            # request middleware accepts (request, handler) arguments and returns response
            return partial(self.wrap_handler, middleware_handler=middleware_handler)
        elif argnames[0:1] == ['handler']:
            # handler middleware accepts (handler) argument and returns handler
            return middleware_handler
        else:
            raise ValueError('middleware_handler function signature must be (request, handler) or (handler)')
        return middleware_handler

    def add_route(self, method, path, handler):
        handler = self.ensure_response(handler)
        handler.__routes__.append(self.router.add_route(method, path, handler))
        return handler

    def wrap_handler(self, handler, middleware_handler):
        '''Wrap a request handler with a middleware handler.'''
        handler = self.ensure_response(handler)
        @wraps(handler)
        async def wrapped_handler(request):
            return await middleware_handler(request, handler)
        for route in handler.__routes__:
            route._handler = wrapped_handler
        wrapped_handler.__headers__ = handler.__headers__
        wrapped_handler.__routes__ = handler.__routes__
        return wrapped_handler
        
    def ensure_response(self, handler):
        try:
            headers = handler.__headers__
            routes = handler.__routes__
            previously_wrapped = True
        except AttributeError:
            headers = {}
            routes = []
            previously_wrapped = False
        if previously_wrapped:
            return handler
        @wraps(handler)
        async def wrapped_handler(request):
            return self.make_response(await handler(request), headers)
        wrapped_handler.__headers__ = headers
        wrapped_handler.__routes__ = routes
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
            @self.ensure_response
            async def options(request):
                return 200
            options.__headers__.update(cors_preflight_headers)
            resource.add_route('OPTIONS', self.ensure_response(options))
            
    def update_handlers(self):
        for resource in self.router.resources():
            for route in resource:
                for handler_middleware in self.handler_middlewares:
                    route.handler = self.wrap_handler(route.handler, handler_middleware)

    @property
    def run(self):
        self.update_options()
        self.update_handlers()
        return partial(web.run_app, self)


def compose(*functions):
    return reduce(lambda f, g: lambda *args, **kargs: f(g(*args, **kargs)), functions)
