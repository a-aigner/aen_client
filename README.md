# aen_client – Aeneis API v2 Python client

A lightweight, session-cookie–aware Python wrapper for the **Aeneis REST API v2**. It provides a clean `AenClient` with thoughtful defaults, typed helpers, and exceptions that map to HTTP semantics.

---

## Features

* **Cookie-based auth**: `login()` via Basic Auth → server session cookie; `logout()` clears it.
* **Ergonomic endpoints**: objects (single/bulk), search, queries, files, locale, version view (draft/release), transactions, upload dir.
* **Typed helpers**: dataclasses and TypedDicts mirroring common payload shapes.
* **Error handling**: HTTP-aware exceptions (`ValidationError`, `NotFoundError`, etc.).
* **Requests session**: header defaults, optional retry helper in `utils.configure_retries()`.

---

## Installation

Add to your project (local path install):

```bash
pip install -e path/to/aen_client
```

Or include in `requirements.txt`:

```
-e git+https://your.git/aen-client.git#egg=aen_client
```

> Package name suggestion: **aen-client** (PyPI-friendly). Module import remains `aen_client`.

---

## Requirements

* Python 3.8+
* `requests`
* (optional) `urllib3` for retry configuration

---

## Quickstart

```python
from aen_client import AenClient

client = AenClient(
    base_url="http://localhost:23000/api/v2",
    username="admin",
    password="secret",
)
client.login()

# Switch to draft view (optional)
client.switch_to_draft()

# Search
hits = client.search("invoice process", limit=5)
print(hits)

# Get a single object
obj = client.get_object("27b990ef-a3a6-44db-bb4e-6ac9b228731b")
print(obj)

client.logout()
```

---

## Authentication

* `login(username=None, password=None, service_id=None)`: calls **`GET /user/login`** using Basic Auth. On success, a **Set-Cookie** header establishes a session; subsequent requests rely on that cookie. The client clears `session.auth` post-login.
* `logout()`: calls **`GET /user/logout`** and clears local cookies.

**Tip:** If the server’s session expires, you’ll receive 401/403; handle by calling `login()` again or enable an auto-retry policy in your app.

---

## API Overview

### Objects

* `get_object(object_id, view="detailed")`
* `create_object(category_id, parent_id, attribute_name, properties=None)`
* `update_object(object_id, properties)`
* `delete_object(object_id)`

### Bulk Objects

* `get_objects(object_ids, view="detailed")`
* `create_objects(objects)`
* `update_objects(objects)`
* `delete_objects(object_ids)`

### Search

* `search(q, view=None, attribute_name=None, category_id=None, limit=None)`
* `search_by_component(component_id, object_id, view="detailed")`

### Queries

* `get_object_query_result(object_id, query_id, view="detailed")`
* `get_objects_query_result(query_id, object_ids, view="detailed")`

### Files on Objects

* `list_files(object_id)`
* `get_file(object_id, filename, attribute_name=None, position=None)`
* `download_file_content(object_id, filename, attribute_name=None, position=None)`
* `upload_file(object_id, file_path, attribute_name=None, filename=None)`
* `update_file(object_id, file_path, attribute_name=None, position=None, filename=None)`
* `delete_file(object_id, filename=None, attribute_name=None, position=None)`

### Locale & Version View

* `get_locale()` / `get_locales()` / `set_locale(language_tag)`
* `switch_to_draft()` / `switch_to_release()`

### Transactions

* `begin_transaction()` / `commit_transaction()` / `rollback_transaction()`

### Upload Directory (server app dir)

* `upload_to_appdir(file_path, folder=None, overwrite=True)`
* `download_from_appdir(name, folder=None)`

---

## Exceptions

All errors derive from `AenClientError`:

* `AuthenticationError`
* `PermissionDenied` (401/403)
* `NotFoundError` (404)
* `ValidationError` (400/405)
* `ConflictError` (409)
* `TransactionError`
* `ServerError` (5xx)

Example:

```python
from aen_client import AenClient, NotFoundError

try:
    obj = client.get_object("nonexistent-id")
except NotFoundError:
    print("Object not found.")
```

---

## Types

From `types.py` (selected):

* `View = Literal["simple", "detailed", "all"]`
* `AenObject`, `AenProperty`, `AenCategory`, `AenFile`
* `QueryResult`, `SearchHit`, `JSON`

These are permissive for flexibility; switch to Pydantic later if desired.

---

## Utilities

From `utils.py`:

* `build_url(base_url, path)` – safe URL join
* `merge_params(*mappings)` – merges optional dicts, skipping `None`
* `normalize_oid(value)` – strips leading `A…` from object IDs where applicable
* `chunked(iterable, size)` – batching helper for bulk endpoints
* `configure_retries(session, ...)` – optional `urllib3.Retry` setup for resilience

Enable retries in your app:

```python
import requests
from aen_client.utils import configure_retries

session = requests.Session()
configure_retries(session)
```

> You can also add a flag in `AenClient` to call `configure_retries(self.session)` automatically (left out to keep the core minimal).

---

## Embedding in your Python project

### Option A: As an internal package (recommended)

**Project layout**

```
my_project/
├── pyproject.toml
├── src/
│   ├── my_project/
│   │   ├── __init__.py
│   │   └── app.py
│   └── aen_client/           # copy this package here
│       ├── __init__.py
│       ├── manager.py
│       ├── exceptions.py
│       ├── types.py
│       └── utils.py
└── tests/
```

**pyproject.toml (PEP 621)**

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-project"
version = "0.1.0"
dependencies = [
  "requests>=2.31",
  "urllib3>=2.0; python_version >= '3.8'",  # optional retry helper
]

[tool.setuptools.packages.find]
where = ["src"]
```

**Using the client in your app**

```python
# src/my_project/app.py
from aen_client import AenClient

client = AenClient(
    base_url="http://localhost:23000/api/v2",
    username="admin",
    password="secret",
)
client.login()
try:
    print(client.get_locale())
finally:
    client.logout()
```

Run:

```bash
pip install -e .
python -m my_project.app
```

### Option B: As a separate dependency (editable or wheel)

* Keep `aen_client` in its own repo; publish a wheel or install via VCS URL:

```bash
pip install -e git+https://your.git/aen-client.git#egg=aen-client
```

Then just `from aen_client import AenClient` as shown above.

---

## Advanced usage

### Transactions

```python
client.begin_transaction()
try:
    client.update_object(object_id="OID", properties=[{"name": "Title", "value": "New"}])
    client.commit_transaction()
except Exception:
    client.rollback_transaction()
    raise
```

### File operations

```python
client.upload_file(object_id="OID", file_path="./diagram.png", attribute_name="attachments")
content = client.download_file_content(object_id="OID", filename="diagram.png")
with open("diagram.png", "wb") as f:
    f.write(content)
```

### Queries

```python
result = client.get_object_query_result(object_id="OID", query_id="QID", view="detailed")
print(result)
```

### Searching

```python
hits = client.search(
    q="invoice",
    category_id=["cat-123"],
    limit=20,
)
```

---

## Versioning & compatibility

* Client targets **Aeneis API v2** based on the provided Swagger specification.
* If your server extends endpoints, the JSON-returning methods should continue to work; open an issue if you need first-class wrappers for new routes.

---

## Contributing

* Run static checks and tests before committing.
* Add new endpoints in `AenClient` with docstrings and map their error cases to existing exceptions.

---

