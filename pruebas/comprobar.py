# Comprobación de las correcciones en el navegador (Chrome sin interfaz).
# Carga index.html + src/app.js, simula acciones del usuario y revisa el texto resultante.
import os, subprocess, pathlib, re, sys
RAIZ = pathlib.Path(__file__).resolve().parent.parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
base = (RAIZ / "index.html").read_text(encoding="utf-8").replace('src="src/app.js"', 'src="../src/app.js"')

def correr(nombre, guion):
    pagina = base.replace("</script>\n", "</script>\n<script>window.addEventListener('load',()=>{" + guion + "});</script>\n", 1)
    f = RAIZ / "pruebas" / f"_{nombre}.html"
    f.write_text(pagina, encoding="utf-8")
    r = subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=8000", "--dump-dom", f.as_uri()],
                       capture_output=True, text=True, encoding="utf-8", timeout=90)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r.stdout))

LOGIN = "const $=id=>document.getElementById(id); const intento=(u,p,ms)=>setTimeout(()=>{$('u').value=u;$('p').value=p;$('fLogin').requestSubmit();},ms);"
casos = {
 "login_correcto": (LOGIN + "location.hash='ingresar'; intento('secretaria','parroquia2026',300);", "Hola, Secretaría"),
 "bloqueo_5_intentos": (LOGIN + "location.hash='ingresar';" + "".join(f"intento('secretaria','mala{i}',{300+i*300});" for i in range(5))
                        + "intento('secretaria','parroquia2026',2000);", "Cuenta bloqueada temporalmente"),
 "venta_completa": (LOGIN + "location.hash='ingresar'; intento('secretaria','parroquia2026',300);"
                    "setTimeout(()=>{location.hash='venta';},900);"
                    "setTimeout(()=>{$('vp').value='camiseta';$('vp').onchange();$('vs').value='34';$('vs').onchange();$('vq').value='2';$('vq').oninput();$('fVenta').requestSubmit();},1500);"
                    "setTimeout(()=>{$('ok').click();},2000);", "Stock actualizado: 12 → 10"),
 "venta_excede_stock": (LOGIN + "location.hash='ingresar'; intento('secretaria','parroquia2026',300);"
                        "setTimeout(()=>{location.hash='venta';},900);"
                        "setTimeout(()=>{$('vp').value='camiseta';$('vp').onchange();$('vs').value='38';$('vs').onchange();$('vq').value='5';$('vq').oninput();$('fVenta').requestSubmit();},1500);",
                        "Solo hay 3 unidades de la talla 38"),
}
ok = True
for nombre, (guion, esperado) in casos.items():
    texto = correr(nombre, guion)
    paso = esperado in texto
    ok &= paso
    print(f"{'PASA ' if paso else 'FALLA'}  {nombre:22s} espera: {esperado}")
sys.exit(0 if ok else 1)
