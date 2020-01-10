from uuid import uuid4

__all__ = ['cors', 'session']

seconds = 1
minutes = 60 * seconds
hours = 60 * minutes
days = 24 * hours
weeks = 7 * days
months = 30 * days
years = 365 * days

def cors(access_control_allow_origin, access_control_expose_headers=[], access_control_allow_credentials=False):
    '''Middleware to add CORS headers.'''
    # define CORS headers
    cors_headers = {}
    cors_headers['Access-Control-Allow-Origin'] = access_control_allow_origin
    if access_control_allow_credentials:
        cors_headers['Access-Control-Allow-Credentials'] = 'true'
    if access_control_expose_headers:
        cors_headers['Access-Control-Expose-Headers'] = ', '.join(access_control_expose_headers)
    # add CORS headers to handler
    def cors_middleware(handler):
        handler.__headers__.update(cors_headers)
        return handler
    return cors_middleware

def session(max_age=10 * years, secure=True, httponly=True, **kargs):
    '''Middleware to get and set session identfier as a cookie.'''
    async def session_middleware(request, handler):
        # get session on request
        try:
            request.session = request.cookies['session']
        except KeyError:
            request.session = str(uuid4())
        # run next handler
        response = await handler(request)
        # set session on response
        response.set_cookie('session', request.session, max_age=max_age, secure=secure, httponly=httponly, **kargs)
        return response
    return session_middleware
