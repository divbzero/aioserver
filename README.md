aioserver
===

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

app.run(host='127.0.0.1', port=8080)
```

Changelog
---

### v0.2.0

- Decorator-based request handlers

### v0.4.0

* Allow handler to specify HTTP response status
* Allow handler to specify additional HTTP headers


### v0.5.0

* Serialize XML ElementTree as text/xml response

