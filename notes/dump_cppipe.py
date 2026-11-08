"""Read-only dump of CellProfiler .cppipe module settings.

.cppipe is a text file whose string values are stored as escaped UTF-16
(for example \\xff\\xfeA\\x00d\\x00d\\x00 for "Add"). This script decodes them
and prints the settings of the chosen modules. It never executes the file.

Usage: python3 -I dump_cppipe.py pipelines/mouse.cppipe 3,5,6   (module numbers)
       python3 -I dump_cppipe.py pipelines/mouse.cppipe list     (module names only)
"""
import re
import sys


def decode(value):
    """Undo Python-2 style escapes (\\xNN, \\\\, \\') and then UTF-16 with BOM."""
    if not value.startswith("\\xff\\xfe"):
        return value
    out, i = bytearray(), 0
    while i < len(value):
        if value.startswith("\\x", i) and i + 4 <= len(value):
            out.append(int(value[i + 2:i + 4], 16))
            i += 4
        elif value[i] == "\\" and i + 1 < len(value) and value[i + 1] in "\\'\"":
            out.append(ord(value[i + 1]))
            i += 2
        else:
            out.append(ord(value[i]))
            i += 1
    try:
        return bytes(out).decode("utf-16")
    except UnicodeDecodeError:
        return value


def modules(path):
    mods, cur = [], None
    for line in open(path, encoding="latin-1"):
        line = line.rstrip("\n")
        m = re.match(r"^([A-Za-z0-9]+):\[module_num:(\d+)\|", line)
        if m:
            cur = (m.group(1), int(m.group(2)), [])
            mods.append(cur)
        elif cur and line.startswith("    ") and ":" in line:
            key, value = line.strip().split(":", 1)
            cur[2].append((key, decode(value)))
    return mods


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    mods = modules(sys.argv[1])
    if sys.argv[2] == "list":
        print("; ".join(f"#{n} {name}" for name, n, _ in mods))
    else:
        want = {int(x) for x in sys.argv[2].split(",")}
        for name, n, items in mods:
            if n in want:
                print(f"--- #{n} {name}")
                for key, value in items:
                    # keep user home directories out of the output
                    print("   ", key, "=", "<path omitted>" if "Users" in value else value)
