"""
Create minimal .py stub files with matching mtimes so Python uses existing .pyc files.
The pyc header (bytes 8-12) contains the source mtime; we set the stub's mtime to match.
"""
import struct, os, time

def get_pyc_source_mtime(pyc_path):
    """Read mtime and source_size from pyc header."""
    with open(pyc_path, "rb") as f:
        data = f.read(16)
    bit_field = struct.unpack_from("<I", data, 4)[0]
    if bit_field & 1:
        return None, None  # hash-based pyc
    mtime = struct.unpack_from("<I", data, 8)[0]
    src_size = struct.unpack_from("<I", data, 12)[0]
    return mtime, src_size

def create_stub(py_path, mtime, src_size):
    """Create a .py stub padded to exact original size, written in binary (LF) mode."""
    os.makedirs(os.path.dirname(py_path), exist_ok=True)
    header = b"# stub - loaded from __pycache__\n"
    padding = max(0, src_size - len(header))
    content = header + b"\n" * padding
    with open(py_path, "wb") as f:  # binary to avoid CRLF on Windows
        f.write(content)
    os.utime(py_path, (mtime, mtime))
    print(f"  stub({src_size}b): {py_path}")

def main():
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "dist")]
        for fname in sorted(files):
            if not fname.endswith(".cpython-314.pyc"):
                continue
            pyc_path = os.path.join(root, fname)
            # Compute corresponding .py path
            py_name = fname.replace(".cpython-314.pyc", ".py")
            py_dir = os.path.dirname(root)  # parent of __pycache__
            py_path = os.path.join(py_dir, py_name)

            mtime, src_size = get_pyc_source_mtime(pyc_path)
            if mtime is None:
                print(f"  hash-based: {pyc_path}, skipping")
                continue
            create_stub(py_path, mtime, src_size)
    print("\nDone. Python should now load from __pycache__.")

if __name__ == "__main__":
    main()
