import sys
import os
import inspect
import dis
import marshal
import types

sys.path.insert(0, os.path.abspath("."))
import backend  # sets up loader

modules_to_inspect = [
    "app.config",
    "app.db.session",
    "app.db.init_db",
    "app.models.db_models",
    "app.models.upi_models",
    "app.engine.upi_state",
    "app.engine.upi_scorer",
    "app.engine.upi_rules",
    "app.services.upi_cases",
    "app.api.upi",
    "app.api.cases",
    "app.api.gateway",
    "app.api.websocket",
    "app.dpip.feed",
    "app.federation.coordinator",
    "app.forensics.upi_sar",
]

out_file = os.path.join(os.path.dirname(__file__), "backend_decompiled_summary.txt")

with open(out_file, "w", encoding="utf-8") as f:
    for mod_name in modules_to_inspect:
        f.write(f"\n{'='*80}\nMODULE: {mod_name}\n{'='*80}\n")
        try:
            mod = __import__(mod_name, fromlist=["*"])
        except Exception as e:
            f.write(f"ERROR importing {mod_name}: {e}\n")
            continue
        
        for attr_name in dir(mod):
            if attr_name.startswith("__"):
                continue
            attr = getattr(mod, attr_name)
            if isinstance(attr, (types.FunctionType, types.MethodType)):
                sig = ""
                try:
                    sig = str(inspect.signature(attr))
                except Exception:
                    pass
                doc = inspect.getdoc(attr) or ""
                f.write(f"\nFunction: {attr_name}{sig}\n  Doc: {doc}\n")
            elif isinstance(attr, type):
                f.write(f"\nClass: {attr_name}\n")
                doc = inspect.getdoc(attr) or ""
                f.write(f"  Doc: {doc}\n")
                for member_name, member in inspect.getmembers(attr):
                    if not member_name.startswith("__"):
                        sig = ""
                        try:
                            sig = str(inspect.signature(member))
                        except Exception:
                            pass
                        doc_m = inspect.getdoc(member) or ""
                        f.write(f"    - {member_name}{sig}: {doc_m[:80]}\n")
            else:
                f.write(f"Var: {attr_name} = {repr(attr)[:200]}\n")

print(f"Wrote analysis to {out_file}")
