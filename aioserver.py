import io
import json
from collections import defaultdict
from functools import partial, reduce, wraps
from uuid import uuid4
from xml.etree.ElementTree import ElementTree

from aiohttp import web

__all__ = ['Application']

seconds = 1
minutes = 60 * seconds
hours = 60 * minutes
days = 24 * hours
weeks = 7 * days
months = 30 * days
years = 365 * days

class Application(web.Application):

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
        
    def cors(self, access_control_allow_origin, access_control_expose_headers=[], access_control_allow_credentials=False):
        '''Decorator to add CORS headers to a handler.'''
        # define CORS headers
        cors_headers = {}
        cors_headers['Access-Control-Allow-Origin'] = access_control_allow_origin
        if access_control_allow_credentials:
            cors_headers['Access-Control-Allow-Credentials'] = 'true'
        if access_control_expose_headers:
            cors_headers['Access-Control-Expose-Headers'] = ', '.join(access_control_expose_headers)
        # add CORS headers to handler
        def add_cors_headers(handler):
            handler = self.ensure_response(handler)
            handler.__headers__.update(cors_headers)
            return handler
        return add_cors_headers

    def session(self, max_age=10 * years, secure=True, httponly=True, **kargs):
        '''Decorator to get and set session identfier as a cookie.'''
        @self.middleware
        async def session_middleware(request, next):
            # get session on request
            try:
                request.session = request.cookies['session']
            except KeyError:
                request.session = str(uuid4())
            # run next handler
            response = await next(request)
            # set session on response
            response.set_cookie('session', request.session, max_age=max_age, secure=secure, httponly=httponly, **kargs)
            return response
        return session_middleware

    def middleware(self, middleware_handler):
        '''Decorator for creating middleware.
        
        Middleware should be defined by decorating a middleware handler:
        
            @app.middleware
            async def always_ok(request, next):
                response = await next(request)
                response.set_status(200, 'OK')
                return response
                
        The middleware handler should take the `request` object and the `next`
        handler as arguments and return a response.
        
        The middleware can then be applied to request handlers:
        
            @always_ok
            @app.get('/not-found-but-still-ok')
            async def not_found_but_still_ok(request):
                return 404, {'message': 'Not found but still OK!'}
                
        '''
        return partial(self.wrap_handler, middleware_handler=middleware_handler)

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

    @property
    def run(self):
        self.update_options()
        return partial(web.run_app, self)
