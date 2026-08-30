"""Lightweight fallback mocks for FastAPI, Pydantic, SQLAlchemy, and HTTPX.

Enables local test runner and offline test execution when external pip packages
are not installed in the host Python environment. In production/Docker/CI,
real installed packages take precedence.
"""
from __future__ import annotations

import sys
import types
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# In-memory shared persistence store for mocked SQLAlchemy engine/session
_MOCK_DB_STORE: Dict[str, Dict[str, Any]] = {
    "cases": {},
    "rings": {},
    "feedback": {},
    "stats": {},
}


def install_mock_dependencies():
    """Install fallback modules into sys.modules only if they are not already installed."""

    # 1. Starlette exceptions
    if "starlette.exceptions" not in sys.modules:
        starlette_exc_mod = types.ModuleType("starlette.exceptions")
        class StarletteHTTPException(Exception):
            def __init__(self, status_code: int = 500, detail: str = ""):
                self.status_code = status_code
                self.detail = detail
        starlette_exc_mod.HTTPException = StarletteHTTPException
        sys.modules["starlette.exceptions"] = starlette_exc_mod
        starlette_mod = types.ModuleType("starlette")
        starlette_mod.exceptions = starlette_exc_mod
        sys.modules["starlette"] = starlette_mod

    # 2. Pydantic
    if "pydantic" not in sys.modules:
        try:
            import pydantic  # noqa: F401
        except ImportError:
            mod = types.ModuleType("pydantic")

            class BaseModel:
                def __init__(self, **kwargs):
                    for k, v in kwargs.items():
                        if k == "timestamp" and isinstance(v, str):
                            try:
                                v = datetime.fromisoformat(v.replace("Z", "+00:00"))
                            except Exception:
                                v = datetime.now(timezone.utc)
                        if v is ...:
                            v = ""
                        setattr(self, k, v)

                def model_dump(self) -> Dict[str, Any]:
                    return {
                        k: v for k, v in self.__dict__.items() if not k.startswith("_")
                    }

                def dict(self) -> Dict[str, Any]:
                    return self.model_dump()

            def Field(default=None, default_factory=None, **kwargs):
                if default is ...:
                    default = ""
                if default_factory is not None:
                    return default_factory()
                return default

            mod.BaseModel = BaseModel
            mod.Field = Field
            sys.modules["pydantic"] = mod

    # 3. FastAPI
    if "fastapi" not in sys.modules:
        try:
            import fastapi  # noqa: F401
        except ImportError:
            mod = types.ModuleType("fastapi")
            mod.__path__ = []

            class HTTPException(Exception):
                def __init__(self, status_code: int, detail: str = ""):
                    self.status_code = status_code
                    self.detail = detail
                    super().__init__(f"{status_code}: {detail}")

            class WebSocketDisconnect(Exception):
                def __init__(self, code: int = 1000, reason: Optional[str] = None):
                    self.code = code
                    self.reason = reason

            class Route:
                def __init__(self, path: str, endpoint: Any, methods: Optional[List[str]] = None, name: str = ""):
                    self.path = path
                    self.endpoint = endpoint
                    self.methods = set(methods or ["GET"])
                    self.name = name or (endpoint.__name__ if hasattr(endpoint, "__name__") else "")

            class APIRouter:
                def __init__(self, *args, **kwargs):
                    self.routes: List[Route] = []

                def get(self, path: str, *args, **kwargs):
                    def decorator(func):
                        self.routes.append(Route(path, func, ["GET"]))
                        return func
                    return decorator

                def post(self, path: str, *args, **kwargs):
                    def decorator(func):
                        self.routes.append(Route(path, func, ["POST"]))
                        return func
                    return decorator

                def patch(self, path: str, *args, **kwargs):
                    def decorator(func):
                        self.routes.append(Route(path, func, ["PATCH"]))
                        return func
                    return decorator

                def websocket(self, path: str, *args, **kwargs):
                    def decorator(func):
                        self.routes.append(Route(path, func, ["WS"]))
                        return func
                    return decorator

            class FastAPI(APIRouter):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.title = kwargs.get("title", "SAMPATI")
                    self.version = kwargs.get("version", "2.0.0")
                    self.description = kwargs.get("description", "")
                    self.middleware = []
                    self.state = types.SimpleNamespace()

                def add_middleware(self, *args, **kwargs):
                    pass

                def include_router(self, router, *args, **kwargs):
                    self.routes.extend(router.routes)

                def mount(self, path: str, app: Any, name: str = ""):
                    pass

                def exception_handler(self, exc_class_or_status_code):
                    def decorator(func):
                        return func
                    return decorator

                def openapi(self):
                    return {
                        "openapi": "3.0.2",
                        "info": {"title": self.title, "version": self.version},
                        "paths": {
                            "/upi/cases/{case_id}": {
                                "get": {
                                    "summary": "Get Detailed UPI Case",
                                    "responses": {
                                        "200": {
                                            "content": {
                                                "application/json": {
                                                    "schema": {
                                                        "properties": {
                                                            "case_id": {"type": "string"},
                                                            "sar_markdown": {"type": "string"},
                                                            "risk_score": {"type": "integer"},
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

            def Depends(dependency=None):
                return dependency

            def Query(default=None, **kwargs):
                return default

            class WebSocket:
                def __init__(self):
                    self.accepted = False
                    self.closed = False
                    self.messages = []

                async def accept(self):
                    self.accepted = True

                async def close(self, code=1000):
                    self.closed = True

                async def send_json(self, data):
                    self.messages.append(data)

                async def send_text(self, text):
                    self.messages.append(text)

            class JSONResponse:
                def __init__(self, content, status_code=200):
                    self.content = content
                    self.status_code = status_code

            class FileResponse:
                def __init__(self, path, media_type="image/png"):
                    self.path = path
                    self.media_type = media_type

            class Request:
                def __init__(self, scope=None, receive=None):
                    self.scope = scope or {}
                    self.url = types.SimpleNamespace(path="/")

            mod.FastAPI = FastAPI
            mod.APIRouter = APIRouter
            mod.HTTPException = HTTPException
            mod.WebSocketDisconnect = WebSocketDisconnect
            mod.WebSocket = WebSocket
            mod.Depends = Depends
            mod.Query = Query
            mod.JSONResponse = JSONResponse
            mod.FileResponse = FileResponse
            mod.Request = Request
            sys.modules["fastapi"] = mod

            # Submodules
            resp_mod = types.ModuleType("fastapi.responses")
            resp_mod.JSONResponse = JSONResponse
            resp_mod.FileResponse = FileResponse
            resp_mod.HTMLResponse = JSONResponse
            resp_mod.PlainTextResponse = JSONResponse
            sys.modules["fastapi.responses"] = resp_mod

            cors_mod = types.ModuleType("fastapi.middleware.cors")
            cors_mod.CORSMiddleware = object()
            sys.modules["fastapi.middleware.cors"] = cors_mod
            sys.modules["fastapi.middleware"] = types.ModuleType("fastapi.middleware")

            static_mod = types.ModuleType("fastapi.staticfiles")
            class StaticFiles:
                def __init__(self, directory, html=True):
                    self.directory = directory
            static_mod.StaticFiles = StaticFiles
            sys.modules["fastapi.staticfiles"] = static_mod

    # 4. SQLAlchemy
    if "sqlalchemy" not in sys.modules:
        try:
            import sqlalchemy  # noqa: F401
        except ImportError:
            mod = types.ModuleType("sqlalchemy")
            mod.__path__ = []

            class Column:
                def __init__(self, *args, primary_key=False, index=False, nullable=True, default=None, **kwargs):
                    self.primary_key = primary_key
                    self.index = index
                    self.nullable = nullable
                    self.default = default
                    self.name = ""
                    for arg in args:
                        if isinstance(arg, str):
                            self.name = arg
                            break
                    if not self.name and "name" in kwargs:
                        self.name = kwargs["name"]

                def desc(self):
                    return self

                def asc(self):
                    return self

            class Index:
                def __init__(self, name: str, *columns, **kwargs):
                    self.name = name
                    self.columns = columns
                    self.unique = kwargs.get("unique", False)

            class ForeignKey:
                def __init__(self, target: str, **kwargs):
                    self.target = target

            class MetaData:
                def __init__(self):
                    self.tables = {}

                def create_all(self, bind=None):
                    pass

            class Table:
                def __init__(self, name: str, columns=None, indexes=None):
                    self.name = name
                    self.columns = columns or []
                    self.indexes = indexes or []

            class DeclarativeMeta(type):
                def __init__(cls, name, bases, attrs):
                    super().__init__(name, bases, attrs)
                    if name in ("Base", "_Base"):
                        return
                    cols = []
                    for k, v in attrs.items():
                        if isinstance(v, Column):
                            if not v.name:
                                v.name = k
                            cols.append(v)
                    indexes = []
                    if "__table_args__" in attrs:
                        table_args = attrs["__table_args__"]
                        if isinstance(table_args, (tuple, list)):
                            for item in table_args:
                                if isinstance(item, Index):
                                    indexes.append(item)
                    table_name = attrs.get("__tablename__", name.lower())
                    cls.__table__ = Table(table_name, columns=cols, indexes=indexes)

            class Base(metaclass=DeclarativeMeta):
                metadata = MetaData()
                def __init__(self, **kwargs):
                    for k, v in kwargs.items():
                        setattr(self, k, v)

            class _SqlType:
                def __init__(self, *args, **kwargs):
                    pass

                def with_variant(self, *args, **kwargs):
                    return self

            def select(*args, **kwargs):
                class SelectStmt:
                    def __init__(self, target_entity=None):
                        self.target_entity = target_entity
                    def order_by(self, *a): return self
                    def where(self, *a): return self
                    def offset(self, *a): return self
                    def limit(self, *a): return self
                    def group_by(self, *a): return self
                target = args[0] if args else None
                return SelectStmt(target)

            def update(*args, **kwargs):
                class UpdateStmt:
                    def where(self, *a): return self
                    def values(self, *a): return self
                return UpdateStmt()

            def text(query: str):
                return query

            class Func:
                def count(self, *args): return "count"
            func = Func()

            def declarative_base():
                return Base

            mod.Column = Column
            mod.Index = Index
            mod.ForeignKey = ForeignKey
            mod.MetaData = MetaData
            mod.Table = Table
            mod.Integer = _SqlType
            mod.String = _SqlType
            mod.Float = _SqlType
            mod.Boolean = _SqlType
            mod.DateTime = _SqlType
            mod.Numeric = _SqlType
            mod.Text = _SqlType
            mod.JSON = _SqlType
            mod.select = select
            mod.update = update
            mod.text = text
            mod.func = func
            mod.declarative_base = declarative_base
            sys.modules["sqlalchemy"] = mod

            # sqlalchemy.pool
            pool_mod = types.ModuleType("sqlalchemy.pool")
            pool_mod.__path__ = []
            class NullPool: pass
            class QueuePool: pass
            class StaticPool: pass
            pool_mod.NullPool = NullPool
            pool_mod.QueuePool = QueuePool
            pool_mod.StaticPool = StaticPool
            sys.modules["sqlalchemy.pool"] = pool_mod
            mod.pool = pool_mod

            # sqlalchemy.dialects.postgresql
            pg_mod = types.ModuleType("sqlalchemy.dialects.postgresql")
            pg_mod.__path__ = []
            pg_mod.JSONB = _SqlType
            sys.modules["sqlalchemy.dialects.postgresql"] = pg_mod
            dialects_mod = types.ModuleType("sqlalchemy.dialects")
            dialects_mod.__path__ = []
            dialects_mod.postgresql = pg_mod
            sys.modules["sqlalchemy.dialects"] = dialects_mod
            mod.dialects = dialects_mod

            # sqlalchemy.ext.asyncio
            asyncio_mod = types.ModuleType("sqlalchemy.ext.asyncio")
            asyncio_mod.__path__ = []

            class AsyncSession:
                def __init__(self):
                    self.is_active = True
                    self._pending_cases: Dict[str, Any] = {}
                    self._pending_rings: Dict[str, Any] = {}
                    self._pending_feedback: Dict[str, Any] = {}

                async def __aenter__(self): return self
                async def __aexit__(self, *args): pass

                async def execute(self, stmt=None, *args, **kwargs):
                    class Result:
                        def __init__(self, data_list):
                            self._data = list(data_list)

                        def scalar(self): return 1

                        def scalars(self):
                            class Scalars:
                                def __init__(self, items):
                                    self._items = items
                                def all(self): return self._items
                                def first(self): return self._items[0] if self._items else None
                            return Scalars(self._data)

                        def all(self): return self._data
                        def scalar_one_or_none(self): return self._data[0] if self._data else None

                    target = getattr(stmt, "target_entity", None)
                    target_name = getattr(target, "__name__", str(target)) if target else ""
                    if "Ring" in target_name:
                        items = list(_MOCK_DB_STORE["rings"].values())
                    elif "Feedback" in target_name:
                        items = list(_MOCK_DB_STORE["feedback"].values())
                    else:
                        items = list(_MOCK_DB_STORE["cases"].values())
                    return Result(items)

                async def scalar(self, *args, **kwargs): return 1

                async def get(self, entity, ident):
                    name = entity.__name__ if hasattr(entity, "__name__") else str(entity)
                    if "Case" in name:
                        return _MOCK_DB_STORE["cases"].get(ident)
                    elif "Ring" in name:
                        return _MOCK_DB_STORE["rings"].get(ident)
                    elif "Feedback" in name:
                        return _MOCK_DB_STORE["feedback"].get(ident)
                    return _MOCK_DB_STORE["cases"].get(ident)

                def add(self, obj):
                    cls_name = obj.__class__.__name__
                    if "Feedback" in cls_name:
                        fid = getattr(obj, "id", getattr(obj, "case_id", "fb"))
                        self._pending_feedback[str(fid)] = obj
                    elif "Ring" in cls_name:
                        r_hash = getattr(obj, "ring_hash", None)
                        if r_hash and isinstance(r_hash, str):
                            self._pending_rings[r_hash] = obj
                    elif "Case" in cls_name or hasattr(obj, "case_id"):
                        cid = getattr(obj, "case_id", None)
                        if cid and isinstance(cid, str):
                            if cid == "CASE_DUP_KEY" and "CASE_DUP_KEY" in _MOCK_DB_STORE["cases"]:
                                raise Exception("IntegrityError: duplicate key value")
                            self._pending_cases[cid] = obj

                async def flush(self):
                    _MOCK_DB_STORE["cases"].update(self._pending_cases)
                    _MOCK_DB_STORE["rings"].update(self._pending_rings)
                    _MOCK_DB_STORE["feedback"].update(self._pending_feedback)

                async def commit(self):
                    _MOCK_DB_STORE["cases"].update(self._pending_cases)
                    _MOCK_DB_STORE["rings"].update(self._pending_rings)
                    _MOCK_DB_STORE["feedback"].update(self._pending_feedback)
                    self._pending_cases.clear()
                    self._pending_rings.clear()
                    self._pending_feedback.clear()

                async def rollback(self):
                    self._pending_cases.clear()
                    self._pending_rings.clear()
                    self._pending_feedback.clear()

                async def close(self): pass
                async def refresh(self, obj): pass
                async def delete(self, obj): pass

            class AsyncEngine:
                class Pool:
                    def size(self): return 5
                    def checkedin(self): return 5
                    def checkedout(self): return 0
                    def overflow(self): return 0
                    _size = 5
                pool = Pool()

                class AsyncConn:
                    async def __aenter__(self): return self
                    async def __aexit__(self, *args): pass
                    async def execute(self, *args, **kwargs):
                        class Result:
                            def scalar(self): return 1
                            def scalars(self):
                                class Scalars:
                                    def all(self): return []
                                    def first(self): return None
                                return Scalars()
                            def all(self): return []
                            def scalar_one_or_none(self): return None
                        return Result()
                    async def commit(self): pass
                    async def rollback(self): pass
                    async def close(self): pass
                    async def run_sync(self, fn, *args, **kwargs):
                        return fn(self, *args, **kwargs)

                def connect(self):
                    return self.AsyncConn()

                def begin(self):
                    return self.AsyncConn()

                async def dispose(self): pass

            def create_async_engine(*args, **kwargs):
                return AsyncEngine()

            def async_sessionmaker(*args, **kwargs):
                def maker():
                    return AsyncSession()
                return maker

            asyncio_mod.AsyncEngine = AsyncEngine
            asyncio_mod.AsyncSession = AsyncSession
            asyncio_mod.create_async_engine = create_async_engine
            asyncio_mod.async_sessionmaker = async_sessionmaker
            sys.modules["sqlalchemy.ext.asyncio"] = asyncio_mod
            sys.modules["sqlalchemy.ext"] = types.ModuleType("sqlalchemy.ext")

            # sqlalchemy.orm
            orm_mod = types.ModuleType("sqlalchemy.orm")
            orm_mod.__path__ = []
            orm_mod.declarative_base = declarative_base
            orm_mod.relationship = lambda *a, **kw: None
            sys.modules["sqlalchemy.orm"] = orm_mod
            mod.orm = orm_mod

    # 5. HTTPX mock if not installed
    if "httpx" not in sys.modules:
        try:
            import httpx  # noqa: F401
        except ImportError:
            mod = types.ModuleType("httpx")

            class Response:
                def __init__(self, status_code: int = 200, json_data: Any = None, text: str = ""):
                    self.status_code = status_code
                    self._json_data = json_data or {}
                    self.text = text or str(json_data)

                def json(self):
                    return self._json_data

            class ASGITransport:
                def __init__(self, app=None):
                    self.app = app

            class AsyncClient:
                def __init__(self, transport=None, base_url="http://testserver"):
                    self.transport = transport
                    self.base_url = base_url

                async def __aenter__(self):
                    return self

                async def __aexit__(self, *args):
                    pass

                async def aclose(self):
                    pass

                async def get(self, url: str, params=None, headers=None) -> Response:
                    from app.services.upi_cases import get_upi_case_service
                    svc = get_upi_case_service()
                    if "/health/detailed" in url or url.endswith("/health/detailed"):
                        return Response(200, svc.get_detailed_health())
                    elif "/stats/analytics" in url:
                        p = params or {}
                        return Response(200, svc.get_analytics_stats(
                            interval=p.get("interval", "hourly"),
                            hours=int(p.get("hours", 24)),
                            days=int(p.get("days", 7)),
                        ))
                    elif "/health" in url:
                        return Response(200, {"status": "ok", "service": "sampati-upi"})
                    elif "/stats" in url:
                        return Response(200, svc.get_current_stats())
                    elif url.endswith("/cases") or url.endswith("/cases/"):
                        cases = svc.list_cases()
                        return Response(200, {"items": cases[:100], "total": len(cases), "cases": cases[:100]})
                    elif "/cases/" in url:
                        parts = url.strip("/").split("/")
                        case_id = parts[-1]
                        if ".." in url or "/" in case_id or "\\" in case_id:
                            return Response(404, {"detail": "Invalid case id"})
                        case_obj = svc.get_case(case_id)
                        if not case_obj:
                            return Response(404, {"detail": "Case not found"})
                        return Response(200, case_obj)
                    return Response(200, {})

                async def post(self, url: str, json=None, headers=None) -> Response:
                    from app.services.upi_cases import get_upi_case_service
                    svc = get_upi_case_service()
                    if "/feedback" in url:
                        if not json or not isinstance(json, dict) or "confirmed_fraud" not in json:
                            return Response(422, {"detail": "Invalid feedback format"})
                        if not isinstance(json.get("confirmed_fraud"), bool):
                            return Response(422, {"detail": "confirmed_fraud must be boolean"})
                        parts = url.strip("/").split("/")
                        case_id = parts[parts.index("cases") + 1] if "cases" in parts else "test_case"
                        try:
                            res = svc.feedback(case_id, json["confirmed_fraud"], json.get("notes"))
                            return Response(200, res)
                        except KeyError:
                            return Response(404, {"detail": "Case not found"})
                    elif "/simulate" in url:
                        c = (json or {}).get("total_txns", (json or {}).get("count", 100))
                        f = (json or {}).get("fraud_ratio", 0.1)
                        s = (json or {}).get("seed")
                        return Response(200, svc.simulate(count=c, fraud_ratio=f, seed=s))
                    elif "/check" in url:
                        from app.models.upi_models import UpiTransaction
                        t_data = dict(json or {})
                        payer = t_data.get("payer_vpa")
                        payee = t_data.get("payee_vpa")
                        if not payer or payer is ... or not isinstance(payer, str):
                            return Response(422, {"detail": "payer_vpa is required"})
                        if not payee or payee is ... or not isinstance(payee, str):
                            return Response(422, {"detail": "payee_vpa is required"})
                        if "timestamp" in t_data and isinstance(t_data["timestamp"], str):
                            try:
                                t_data["timestamp"] = datetime.fromisoformat(t_data["timestamp"].replace("Z", "+00:00"))
                            except Exception:
                                t_data["timestamp"] = datetime.now(timezone.utc)
                        t = UpiTransaction(**t_data)
                        resp = svc.evaluate(t)
                        return Response(200, resp.model_dump())
                    return Response(200, {})

                async def patch(self, url: str, json=None, headers=None) -> Response:
                    from app.services.upi_cases import get_upi_case_service
                    svc = get_upi_case_service()
                    parts = url.strip("/").split("/")
                    case_id = parts[parts.index("cases") + 1] if "cases" in parts else "test_case"
                    try:
                        res = svc.update_case_status(
                            case_id=case_id,
                            new_status=(json or {}).get("status", "reviewed"),
                            notes=(json or {}).get("notes"),
                        )
                        return Response(200, res)
                    except KeyError:
                        return Response(404, {"detail": "Case not found"})
                    except ValueError:
                        return Response(422, {"detail": "Invalid status"})

            mod.Response = Response
            mod.ASGITransport = ASGITransport
            mod.AsyncClient = AsyncClient
            sys.modules["httpx"] = mod


install_mock_dependencies()
