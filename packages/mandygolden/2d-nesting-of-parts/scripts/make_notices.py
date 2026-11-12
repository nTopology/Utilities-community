"""Assemble THIRD-PARTY-NOTICES.txt from the licence files of the packages frozen into nest_pack.exe."""
import importlib.metadata as md, os, sys, sysconfig

out = sys.argv[1]
parts = []

def add(title, origin, text):
    parts.append("=" * 78 + "\n" + title + "\n" + origin + "\n" + "=" * 78 + "\n\n" + text.strip() + "\n\n")

# Python interpreter licence (PSF), from the interpreter that PyInstaller bundles
py_lic = None
for cand in (os.path.join(os.path.dirname(sys.executable), "LICENSE.txt"),
             os.path.join(sysconfig.get_paths()["stdlib"], "..", "LICENSE.txt"),
             os.path.join(sys.base_prefix, "LICENSE.txt")):
    if os.path.exists(cand):
        py_lic = open(cand, encoding="utf-8", errors="replace").read(); break
if py_lic is None:
    py_lic = "See https://docs.python.org/3/license.html (PSF License Agreement for Python %s)." % sys.version.split()[0]
add("Python %s" % sys.version.split()[0], "Python Software Foundation License; https://www.python.org/", py_lic)

for dist_name, origin in (("numpy", "BSD 3-Clause License; https://numpy.org/"),
                          ("pillow", "HPND License (historic PIL licence); https://python-pillow.org/"),
                          ("pyinstaller", "GPL 2.0 with the PyInstaller bootloader exception, which permits distributing built programs under any terms; https://pyinstaller.org/")):
    d = md.distribution(dist_name)
    texts = []
    for f in sorted((d.files or []), key=lambda p: (len(str(p)), str(p))):
        s = str(f).replace("\\", "/")
        name = os.path.basename(s).lower()
        if name.startswith(("license", "copying")) and "dist-info/licenses/" in s:
            rel = s.split("dist-info/licenses/", 1)[1]
            body = open(d.locate_file(f), encoding="utf-8", errors="replace").read().strip()
            label = "" if "/" not in rel else "--- bundled component licence: %s ---\n\n" % rel
            texts.append(label + body)
    if not texts:
        raise SystemExit("no licence files found for " + dist_name)
    add("%s %s" % (d.metadata["Name"], d.version), origin, "\n\n".join(texts))

header = ("THIRD-PARTY NOTICES for nest_pack.exe\n\n"
          "nest_pack.exe is the nTop 2D Nesting of Parts packer (nest_pack.py) frozen into one executable.\n"
          "The packing algorithm itself is nTop's own code. The executable also contains the components\n"
          "below, redistributed under their own licences, which require that these notices accompany it.\n\n")
open(out, "w", encoding="utf-8").write(header + "".join(parts))
print("written", out, len(parts), "components", os.path.getsize(out), "bytes")
