# -*- coding: utf-8 -*-
"""تهيئة البيئة (§7.1 من ملف المعرفة): حزم + ffmpeg + خطوط + raqm."""
import os, shutil, subprocess, sys, importlib

PKGS = {"yt_dlp": "yt-dlp", "edge_tts": "edge-tts", "imageio_ffmpeg": "imageio-ffmpeg",
        "arabic_reshaper": "arabic-reshaper", "bidi": "python-bidi"}

def _pip(names):
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", *names],
                   capture_output=True)

def ensure_deps(verbose=True):
    missing = []
    for mod, pkg in PKGS.items():
        try:
            importlib.import_module(mod)
        except Exception:
            missing.append(pkg)
    if missing:
        if verbose: print("📦 تثبيت:", ", ".join(missing))
        _pip(missing)
    return not missing

def ensure_ffmpeg(root=None):
    """ffmpeg عبر imageio-ffmpeg + symlink في <root>/bin (لا root privileges)."""
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    root = root or os.getcwd()
    bindir = os.path.join(root, "bin"); os.makedirs(bindir, exist_ok=True)
    import imageio_ffmpeg
    src = imageio_ffmpeg.get_ffmpeg_exe()
    dst = os.path.join(bindir, "ffmpeg")
    if not os.path.exists(dst):
        os.symlink(src, dst)
    os.environ["PATH"] = bindir + os.pathsep + os.environ.get("PATH", "")
    return dst

def raqm():
    try:
        from PIL import features
        return bool(features.check("raqm"))
    except Exception:
        return False

def selftest(root=None):
    root = root or os.getcwd()
    ensure_deps(); ff = ensure_ffmpeg(root)
    rep = {"ffmpeg": ff, "raqm(Pillow shaping)": raqm(), "fonts": {}}
    from . import config
    cfg = config.load(root)
    for k, rel in cfg["fonts"].items():
        p = rel if os.path.isabs(rel) else os.path.join(root, rel)
        ok = os.path.exists(p)
        if ok:
            try:
                from PIL import ImageFont
                ImageFont.truetype(p, 40); ok = True
            except Exception:
                ok = False
        rep["fonts"][k] = p if ok else f"MISSING:{p}"
    rep["python"] = sys.version.split()[0]
    return rep
