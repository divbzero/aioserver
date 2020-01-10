Installation
---

```
pip install aioserver
```

Usage
---

#### Create Application

```python
from aioserver import Application

app = Application()
```

#### Basic Routes

```python
@app.get('/')
async def index(request):
    return {'message': 'Hello, world!'}

@app.get('/found')
async def found(request):
    return 302, {'Location': 'https://www.example.com/'}, {'message': 'Found'}

@app.get('/not-found')
async def not_found(request):
    return 404, {'message': 'Not Found'}

@app.get('/server-error')
async def server_error(request):
    return 500
```

#### CORS Headers

```python
@app.cors('*')
@app.get('/cross-origin-resource-sharing')
async def cross_origin_resource_sharing(request):
    return {'message': 'Greetings from a different origin!'}

@app.cors('*', ['X-Custom-Header'])
@app.get('/cross-origin-header-sharing')
async def cross_origin_header_sharing(request):
    return 200, {'X-Custom-Header': 'share-this-header-too'}, {'message': 'Hello!'}
```

### Session Cookie

```python
from aioserver.middleware import hours

@app.get('/session-cookie')
@app.session(max_age=24 * hours)
async def session_cookie(request):
    print(f'session uuid {request.session}')
    return 200, {'message': 'Session UUID set as cookie for 24 hours.'}
```

#### Custom Middleware

Route-specific middleware:

```python
@app.middleware
async def always_ok(request, handler):
    response = await handler(request)
    response.set_status(200, 'OK')
    return response

@always_ok
@app.get('/not-found-but-still-ok')
async def not_found_but_still_ok(request):
    return 404, {'message': 'Not found but still OK!'}
```

Global middleware:

```python
async def strict_transport_security(request, handler):
    response = await handler(request)
    response.headers['Strict-Transport-Security'] = 'max-age=31536000'
    return response

app.use(strict_transport_security)
```

#### Run Application

```python
app.run(host='127.0.0.1', port=8080)
```

Changelog
---

### v0.2.0

- Decorator-based request handlers

### v0.4.0

- Allow handler to specify HTTP response status
- Allow handler to specify additional HTTP headers

### v0.5.0

- Serialize XML ElementTree as text/xml response

### v0.6.0

- Decorator-based CORS

### v0.6.2

- Fix project description
