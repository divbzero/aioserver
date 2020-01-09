Installation
---

```
pip install aioserver
```

Usage
---

```python
from aioserver import Application

app = Application()

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

@app.cors('*')
@app.get('/cross-origin-resource-sharing')
async def cross_origin_resource_sharing(request):
    return {'message': 'Greetings from a different origin!'}

@app.cors('*', ['X-Custom-Header'])
@app.get('/cross-origin-header-sharing')
async def cross_origin_header_sharing(request):
    return 200, {'X-Custom-Header': 'share-this-header-too'}, {'message': 'Hello!'}

app.run(host='127.0.0.1', port=8080)
```

Advanced Usage
---

```python
from aioserver import Application

app = Application()

@app.middleware
async def always_ok(request, next):
    response = await next(request)
    response.set_status(200, 'OK')
    return response

@always_ok
@app.get('/not-found-but-still-ok')
async def not_found_but_still_ok(request):
    return 404, {'message': 'Not found but still OK!'}

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
