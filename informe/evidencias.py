# Genera capturas tipo terminal con la salida REAL de los comandos (para el informe)
import subprocess, os, html, pathlib
RAIZ = pathlib.Path(__file__).resolve().parent.parent
OUT = RAIZ / "informe" / "img"
OUT.mkdir(parents=True, exist_ok=True)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def sh(cmd):
    r = subprocess.run(cmd, cwd=RAIZ, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (r.stdout + r.stderr).rstrip()


def terminal(nombre, bloques, ancho=1100):
    cuerpo = ""
    for cmd, salida in bloques:
        cuerpo += f'<div class="p"><span class="ps">PS C:\\...\\Analisis_Estatico_Grupo5&gt;</span> {html.escape(cmd)}</div>'
        cuerpo += f"<pre>{html.escape(salida)}</pre>"
    por_linea = max(40, int((ancho - 24) / 7.25))
    lineas = sum(2 + sum(max(1, -(-len(l) // por_linea)) for l in s.splitlines()) for _, s in bloques)
    alto = 60 + lineas * 17 + 24
    pagina = f"""<!doctype html><meta charset="utf-8"><style>
body{{margin:0;background:#0C0C0C;font:13px/17px Consolas,'Cascadia Mono',monospace;color:#CCCCCC}}
.bar{{background:#1F1F1F;color:#ddd;font:12px 'Segoe UI',sans-serif;padding:8px 12px;display:flex;gap:8px;align-items:center}}
.bar i{{width:11px;height:11px;border-radius:50%;display:inline-block;background:#555}}
.w{{padding:8px 12px}} pre{{margin:0 0 6px;white-space:pre-wrap;word-break:break-word}} .p{{color:#fff;margin-top:4px}} .ps{{color:#61D6D6}}
</style><div class="bar"><i></i><i></i><i></i>&nbsp;Windows PowerShell — Analisis_Estatico_Grupo5</div><div class="w">{cuerpo}</div>"""
    f = OUT / f"{nombre}.html"
    f.write_text(pagina, encoding="utf-8")
    png = OUT / f"{nombre}.png"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={ancho},{alto}",
                    f"--screenshot={png}", f.as_uri()], capture_output=True, timeout=60)
    f.unlink()
    print(nombre, png.exists())


def recorte(texto, primeras, ultimas=3):
    l = texto.splitlines()
    if len(l) <= primeras + ultimas:
        return texto
    return "\n".join(l[:primeras] + [f"   … ({len(l) - primeras - ultimas} líneas más) …"] + l[-ultimas:])


# 1. Instalación y versión
terminal("01_instalacion", [
    ("npm ls --depth=0", sh("npm ls --depth=0")),
    ("npx eslint --version", sh("npx eslint --version")),
])
# 2. Configuración
terminal("02_configuracion", [("Get-Content eslint.config.mjs", (RAIZ / "eslint.config.mjs").read_text(encoding="utf-8"))])
# 3. Análisis del código original (commit 5a554b1)
antes = (RAIZ / "resultados" / "eslint_antes.txt").read_text(encoding="utf-8").strip()
terminal("03_eslint_antes", [("npx eslint src    # código original, commit 5a554b1", recorte(antes, 34))], 1250)
filtro = 'findstr /V /C:"id-length" /C:"max-statements-per-line" resultados\\eslint_antes.txt'
terminal("03b_eslint_antes_relevantes", [(filtro, sh(filtro))], 1250)
# 4. Análisis después de las correcciones
despues = sh("npx eslint src")
terminal("04_eslint_despues", [("npx eslint src", recorte(despues, 24))], 1250)
# 5. Resumen por regla antes/después
terminal("05_resumen_reglas", [("python resultados/resumen_reglas.py", sh("python resultados/resumen_reglas.py"))])
# 6. Comprobación en navegador
terminal("06_comprobacion", [("python pruebas/comprobar.py", (RAIZ / "resultados" / "comprobacion_navegador.txt").read_text(encoding="utf-8").strip())])
# 7. Historial del repositorio
terminal("07_git_log", [("git log --oneline", sh("git log --oneline")), ("git diff --stat HEAD~1 HEAD -- src/app.js", sh("git diff --stat HEAD~1 HEAD -- src/app.js"))])
