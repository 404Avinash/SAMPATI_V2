import sys
import os
import inspect
import dis

sys.path.insert(0, os.path.abspath("."))
import backend

out_file = os.path.join(os.path.dirname(__file__), "deep_inspect.txt")

with open(out_file, "w", encoding="utf-8") as f:
    def log(msg=""):
        f.write(msg + "\n")

    # 1. Config
    import app.config as config
    log("="*60)
    log("APP CONFIG")
    log("="*60)
    s = config.get_settings()
    for k, v in (s.model_dump().items() if hasattr(s, "model_dump") else s.__dict__.items()):
        log(f"{k}: {v}")

    # 2. DB session and init_db
    import app.db.session as db_session
    import app.db.init_db as db_init
    log("="*60)
    log("DB SESSION & INIT_DB")
    log("="*60)
    for name in dir(db_session):
        if not name.startswith("__"):
            val = getattr(db_session, name)
            log(f"db_session.{name}: {type(val)} = {repr(val)[:150]}")
    for name in dir(db_init):
        if not name.startswith("__"):
            val = getattr(db_init, name)
            log(f"db_init.{name}: {type(val)} = {repr(val)[:150]}")

    # Disassemble db_session methods if AsyncDatabaseStore exists
    if hasattr(db_session, "AsyncDatabaseStore"):
        cls = db_session.AsyncDatabaseStore
        log("\nAsyncDatabaseStore Methods:")
        for m_name, m_func in inspect.getmembers(cls, predicate=inspect.isfunction):
            log(f"\n--- Method: {m_name} ---")
            log(inspect.getdoc(m_func) or "")
            log(dis.code_info(m_func))
            log("Disassembly:")
            dis.dis(m_func, file=f)

    # 3. Models
    import app.models.db_models as db_models
    import app.models.upi_models as upi_models
    log("="*60)
    log("DB MODELS")
    log("="*60)
    for name in dir(db_models):
        if not name.startswith("__"):
            val = getattr(db_models, name)
            log(f"db_models.{name}: {val}")
            if inspect.isclass(val):
                for col in getattr(val, "__table__", getattr(val, "__fields__", {})).columns if hasattr(val, "__table__") else []:
                    log(f"  Column: {col.name} ({col.type}) primary_key={col.primary_key}, nullable={col.nullable}")

    log("="*60)
    log("UPI MODELS")
    log("="*60)
    for name in dir(upi_models):
        if not name.startswith("__"):
            val = getattr(upi_models, name)
            log(f"upi_models.{name}: {val}")
            if inspect.isclass(val) and hasattr(val, "model_fields"):
                for fname, finfo in val.model_fields.items():
                    log(f"  Field: {fname}: {finfo.annotation} (default={finfo.default})")

    # 4. UPI Hot State
    import app.engine.upi_state as upi_state
    log("="*60)
    log("UPI HOT STATE")
    log("="*60)
    for m_name, m_func in inspect.getmembers(upi_state.UpiHotState, predicate=inspect.isfunction):
        log(f"\n--- UpiHotState.{m_name} ---")
        log(inspect.getdoc(m_func) or "")
        dis.dis(m_func, file=f)

    # 5. UPI Cases Service
    import app.services.upi_cases as upi_cases
    log("="*60)
    log("UPI CASES SERVICE")
    log("="*60)
    for m_name, m_func in inspect.getmembers(upi_cases.UpiCaseService, predicate=inspect.isfunction):
        log(f"\n--- UpiCaseService.{m_name} ---")
        log(inspect.getdoc(m_func) or "")
        dis.dis(m_func, file=f)

    # 6. UPI API Router
    import app.api.upi as upi_api
    log("="*60)
    log("UPI API ROUTES")
    log("="*60)
    for route in upi_api.router.routes:
        log(f"Route: {route.path} {route.methods} -> {route.endpoint.__name__}")
        log(inspect.getdoc(route.endpoint) or "")
        dis.dis(route.endpoint, file=f)

print(f"Deep inspection written to {out_file}")
