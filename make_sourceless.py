"""
Convert stub .py + __pycache__/*.pyc pairs into sourceless bytecode modules.

Python supports "sourceless distribution": if a module has NO .py file but a
sibling `<name>.pyc` file (without the cpython-XY tag, i.e. not inside
__pycache__), the import system loads that bytecode directly - no mtime or
size check against a source file is ever performed. This survives Docker
COPY (which does not preserve source mtimes) and any other environment where
the stub/pyc mtime-matching trick would break.
"""
import os
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))

# Real, hand-written source files - never overwrite these with stale bytecode.
SKIP = {
    os.path.join(ROOT, "app", "main.py"),
    os.path.join(ROOT, "backend", "__init__.py"),
}


def main():
    converted = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        if os.path.basename(dirpath) != "__pycache__":
            continue
        pkg_dir = os.path.dirname(dirpath)
        for fname in filenames:
            if not fname.endswith(".cpython-314.pyc"):
                continue
            modname = fname[: -len(".cpython-314.pyc")]
            pyc_src = os.path.join(dirpath, fname)
            pyc_dst = os.path.join(pkg_dir, modname + ".pyc")
            py_stub = os.path.join(pkg_dir, modname + ".py")

            if py_stub in SKIP:
                print(f"  skip (real source): {py_stub}")
                continue

            shutil.copyfile(pyc_src, pyc_dst)
            if os.path.exists(py_stub):
                os.remove(py_stub)
            converted += 1
            print(f"  sourceless: {pyc_dst}")

    print(f"\nConverted {converted} modules to sourceless bytecode.")


if __name__ == "__main__":
    main()
