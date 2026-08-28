import sys, os, inspect, dis

sys.path.insert(0, os.path.abspath("."))
import backend

out_file = os.path.join(os.path.dirname(__file__), "full_survey_data.txt")

with open(out_file, "w", encoding="utf-8") as f:
    def p(text=""):
        f.write(text + "\n")

    p("=== 1. UPI_STATE (app/engine/upi_state.py) ===")
    import app.engine.upi_state as upi_state
    state_inst = upi_state.get_upi_state()
    p(f"UpiHotState class doc: {upi_state.UpiHotState.__doc__}")
    p(f"UpiHotState fields / attributes in instance:")
    for k, v in state_inst.__dict__.items():
        p(f"  - {k}: type={type(v)}, value_repr={repr(v)[:100]}")

    p("\nUpiHotState Methods and Docstrings:")
    for name, method in inspect.getmembers(upi_state.UpiHotState, predicate=inspect.isfunction):
        p(f"  Method: {name}{inspect.signature(method)}")
        doc = inspect.getdoc(method)
        if doc:
            p(f"    Doc: {doc}")

    p("\n=== 2. UPI_CASES (app/services/upi_cases.py) ===")
    import app.services.upi_cases as upi_cases
    service_inst = upi_cases.get_upi_case_service()
    p(f"UpiCaseService class doc: {upi_cases.UpiCaseService.__doc__}")
    p(f"UpiCaseService attributes in instance:")
    for k, v in service_inst.__dict__.items():
        p(f"  - {k}: type={type(v)}, value_repr={repr(v)[:100]}")

    p("\nUpiCaseService Methods:")
    for name, method in inspect.getmembers(upi_cases.UpiCaseService, predicate=inspect.isfunction):
        p(f"  Method: {name}{inspect.signature(method)}")
        doc = inspect.getdoc(method)
        if doc:
            p(f"    Doc: {doc}")

    p("\n=== 3. UPI_MODELS (app/models/upi_models.py) ===")
    import app.models.upi_models as upi_models
    for name in dir(upi_models):
        obj = getattr(upi_models, name)
        if isinstance(obj, type) and hasattr(obj, "model_fields"):
            p(f"\nModel: {name}")
            p(f"  Doc: {inspect.getdoc(obj)}")
            for fname, finfo in obj.model_fields.items():
                p(f"  Field: {fname} : {finfo.annotation} (default={finfo.default})")

    p("\n=== 4. DB_MODELS (app/models/db_models.py) ===")
    import app.models.db_models as db_models
    for name in dir(db_models):
        obj = getattr(db_models, name)
        if isinstance(obj, type) and hasattr(obj, "__tablename__"):
            p(f"\nSQLAlchemy Table: {obj.__tablename__} (Class: {name})")
            for col in obj.__table__.columns:
                p(f"  Col: {col.name} ({col.type}), PK={col.primary_key}, nullable={col.nullable}, default={col.default}")

    p("\n=== 5. DB_SESSION (app/db/session.py) ===")
    import app.db.session as db_session
    p(f"AsyncDatabaseStore doc: {db_session.AsyncDatabaseStore.__doc__}")
    for name, method in inspect.getmembers(db_session.AsyncDatabaseStore, predicate=inspect.isfunction):
        p(f"  Store Method: {name}{inspect.signature(method)}")
        doc = inspect.getdoc(method)
        if doc:
            p(f"    Doc: {doc}")

    p("\n=== 6. UPI_API (app/api/upi.py) ===")
    import app.api.upi as upi_api
    for route in upi_api.router.routes:
        p(f"\nRoute: {route.path} [{','.join(route.methods)}]")
        p(f"  Endpoint: {route.endpoint.__name__}{inspect.signature(route.endpoint)}")
        p(f"  Doc: {inspect.getdoc(route.endpoint)}")

    p("\n=== 7. CONFIG (app/config.py) ===")
    import app.config as config
    settings = config.get_settings()
    for k, v in (settings.model_dump().items() if hasattr(settings, "model_dump") else settings.__dict__.items()):
        p(f"  {k} = {v}")

print(f"Wrote full survey data to {out_file}")
