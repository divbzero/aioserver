aioserver
===

*An async web framework for humans*

Installation
---

```
pip install aioserver
```

Usage
---

```python
from aiohttp import web
from aioserver import Application

app = Application()

@app.get('/')
async def index(request):
    return {'message': 'Hello, world!'}

app.run(host='127.0.0.1', port=8080)
```

