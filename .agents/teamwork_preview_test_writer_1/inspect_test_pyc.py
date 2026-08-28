import os
import sys
import marshal
import types

def inspect_pyc(path):
    print(f"=== Inspecting {path} ===")
    if not os.path.exists(path):
        print("Not found")
        return
    with open(path, "rb") as f:
        data = f.read()
    for offset in [16, 12]:
        try:
            code = marshal.loads(data[offset:])
            if isinstance(code, types.CodeType):
                print(f"Code name: {code.co_name}, consts count: {len(code.co_consts)}")
                for c in code.co_consts:
                    if isinstance(c, types.CodeType):
                        print(f"  def/class: {c.co_name}")
                return
        except Exception:
            continue
    print("Could not load code object")

if __name__ == "__main__":
    inspect_pyc("tests/test_m1_stress.pyc")
    inspect_pyc("tests/e2e/conftest.pyc")
