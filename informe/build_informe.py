# Informe de análisis estático (diseño de la plantilla UTEQ) -> HTML -> PDF con Chrome
import os, subprocess, html, re, shutil
import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
E = html.escape
REPO = "https://github.com/jvelezv10-glitch/analisis-estatico-web-parroquial"
LOGO = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Prototipo_VV_Semana", "logo-uteq.png")
shutil.copy(LOGO, os.path.join(HERE, "logo-uteq.png"))

DATA = dict(
    tema="Análisis estático del módulo de la Web Parroquial",
    grupo="Grupo 5",
    integrantes=[("Valdiviezo Yun On Adamo Eduardo", "0009-0003-5888-884X"),
                 ("Vélez Vinces Jostin Gustavo", "0009-0006-4521-4485")],
    docente="Ing. Cordero Bazurto José Steven",
    curso="Quinto nivel — Paralelo B",
    entrega="27 de noviembre de 2026",
)

# ---------------------------------------------------------------- datos
MANUAL = [
    ("M01", "Ingreso (L261)", "La contraseña de prueba está escrita en texto plano dentro del código que descarga el navegador.",
     "Cualquier persona que abra las herramientas del navegador puede leerla y entrar al panel de secretaría."),
    ("M02", "Ingreso (L262–263)", "Al llegar a 0 intentos el mensaje dice “Cuenta bloqueada”, pero el código no impide nuevos intentos.",
     "El bloqueo es solo visual; permite probar contraseñas sin límite (fuerza bruta)."),
    ("M03", "render, ingreso, venta (L236, 263, 272, 276, 297)", "Se construye HTML con plantillas y se inserta con innerHTML; algunos valores no pasan por esc().",
     "Si los datos vienen de la base de datos, un texto con etiquetas podría ejecutar código (XSS)."),
    ("M04", "priceFor y textos (L18, 66, 96, 100, 132)", "Los precios por talla (10, 11) y el límite de talla (38) están repetidos como números sueltos en cinco lugares.",
     "Al cambiar un precio hay que editar varios sitios; si se olvida uno, el catálogo y la venta muestran precios distintos."),
    ("M05", "bind (L245–323)", "Una sola función de 79 líneas maneja catálogo, ingreso, venta, contenidos y reportes.",
     "Difícil de leer, probar y modificar sin introducir errores."),
    ("M06", "Venta (L275 y L291)", "El resumen lee la cantidad con parseInt y la validación con Number.",
     "Con “2.5” el resumen muestra 2 unidades y la validación la rechaza: el usuario ve datos contradictorios."),
    ("M07", "Resumen de venta (L276–281)", "El total se calcula aunque la cantidad supere el stock.",
     "Se muestra un total (USD 55) de una venta que no se puede realizar."),
    ("M08", "Confirmar venta (L291 y L304)", "El stock se lee al validar y se reutiliza al confirmar.",
     "Con dos ventas simultáneas (riesgo R3 del plan) el stock podría quedar negativo."),
    ("M09", "Aprobación (L316)", "La fecha de aprobación del párroco está fija en “21/11/2026”.",
     "Todo cambio aprobado mostraría una fecha falsa; se pierde trazabilidad."),
    ("M10", "Todo el archivo", "Nombres de una letra o sin significado (S, V, p, n, vp, vs, vq, d1, d2) y varias instrucciones por línea.",
     "Baja legibilidad; un integrante nuevo tarda más en entender el código."),
    ("M11", "Reporte (L227–229)", "La tabla del reporte tiene datos fijos y no se filtra por las fechas elegidas.",
     "El reporte no refleja las ventas reales del período."),
    ("M12", "Reporte (L320)", "Las fechas se comparan como texto (a &gt; b).",
     "Requiere revisión: funciona porque el campo date entrega el formato AAAA-MM-DD."),
]

MATRIZ = [
    ("H01", "app.js · ingreso (L261)", "Contraseña en texto plano en el cliente", "Vulnerabilidad", "Manual", "Crítica", "Acceso no autorizado al panel", "Validar en el servidor; en el prototipo, comparar con un hash"),
    ("H02", "app.js · ingreso (L262–263)", "El bloqueo tras 5 intentos no se aplica", "Defecto potencial", "Manual", "Alta", "Fuerza bruta de contraseñas", "Guardar la hora de bloqueo y rechazar intentos hasta que pase"),
    ("H03", "app.js · L236, 263, 272, 276, 297", "HTML insertado con innerHTML sin sanear", "Posible vulnerabilidad", "Ambas", "Media", "XSS si los datos vienen de la BD", "Usar textContent o crear nodos; escapar todo valor dinámico"),
    ("H04", "app.js · priceFor (L18) y textos", "Precios y talla límite como números mágicos repetidos", "Mantenibilidad", "Ambas", "Media", "Precios inconsistentes al cambiar uno", "Constantes únicas (PRECIO, STOCK_BAJO)"),
    ("H05", "app.js · bind (L245), upd (L269), submit (L284)", "Funciones largas y complejas (79 líneas; complejidad 14 a 17)", "Mantenibilidad", "Ambas", "Media", "Errores al modificar; difícil de probar", "Dividir en funciones por pantalla"),
    ("H06", "app.js · L275 / L291", "Dos formas distintas de leer la cantidad", "Defecto potencial", "Manual", "Media", "Resumen y validación contradictorios", "Una sola función leerCantidad"),
    ("H07", "app.js · L276–281", "Total calculado aunque la cantidad supere el stock", "Defecto potencial", "Manual", "Baja", "Información engañosa", "Mostrar “—” si la cantidad no es válida"),
    ("H08", "app.js · L304", "Stock desactualizado al confirmar la venta", "Defecto potencial", "Manual", "Media", "Stock negativo con ventas simultáneas", "Releer el stock al confirmar"),
    ("H09", "app.js · L316", "Fecha de aprobación fija", "Defecto potencial", "Manual", "Media", "Trazabilidad incorrecta", "Usar la fecha del día"),
    ("H10", "app.js · L32, 33, 233, 243, 245", "Funciones declaradas en el ámbito global", "Mantenibilidad", "Herramienta", "Baja", "Choque de nombres con otros scripts", "Encapsular en una función autoejecutable con “use strict”"),
    ("H11", "app.js · L249, 252, 254, 255, 302", "Funciones flecha que devuelven una asignación", "Estilo", "Herramienta", "Baja", "Código confuso (= vs ===)", "Usar llaves y sentencias explícitas"),
    ("H12", "app.js · L18, 29, 87, 98, 149, 274, 320", "Operadores ternarios anidados", "Estilo", "Herramienta", "Baja", "Lógica difícil de leer", "Extraer a if/else o funciones"),
    ("H13", "app.js · 90 avisos", "Identificadores de una letra", "Estilo", "Ambas", "Baja", "Baja legibilidad", "Nombres descriptivos"),
    ("H14", "app.js · 34 avisos", "Varias instrucciones en una línea", "Estilo", "Ambas", "Baja", "Baja legibilidad y depuración", "Una instrucción por línea"),
    ("H15", "app.js · reporte (L227–229)", "Reporte con datos fijos, no filtra por período", "Defecto potencial", "Manual", "Media", "Reporte incorrecto", "Filtrar los movimientos por fecha (pendiente)"),
    ("H16", "app.js · L32 (2600), L177 (6)", "Números mágicos de tiempo y formato", "Estilo", "Herramienta", "Baja", "Difícil de ajustar", "Constantes con nombre"),
]

CORREC = [
    ("C1", "H02 · Bloqueo de ingreso",
     "El contador de intentos solo cambiaba el texto del mensaje; nunca se consultaba antes de validar la contraseña.",
     "Guardar la hora de fin del bloqueo (lockedUntil) y rechazar cualquier intento mientras no pase.",
     "Prueba en navegador: 5 intentos fallidos y luego la clave correcta. Original: entra al panel. Corregido: “Cuenta bloqueada temporalmente”.",
     "Resuelto"),
    ("C2", "H01 · Contraseña en texto plano",
     "El prototipo se hizo sin servidor y la validación se escribió directamente en el navegador.",
     "Reemplazar la contraseña por su hash SHA-256 y dejar documentado que la validación real irá en el servidor.",
     "Inspección manual: la contraseña ya no aparece en el código. El usuario y el hash siguen en el cliente.",
     "Parcialmente resuelto"),
    ("C3", "H04 · Precios como números mágicos",
     "Los valores de negocio se escribieron directamente en cada lugar donde se usaban.",
     "Crear las constantes PRECIO, STOCK_BAJO, INTENTOS_MAX, DIGITOS_RECIBO y usarlas en el cálculo y en los textos.",
     "ESLint no-magic-numbers: de 7 avisos a 1 (el 16 de la base hexadecimal, que no es un defecto).",
     "Resuelto"),
    ("C4", "H03 · innerHTML sin sanear",
     "Era más rápido construir pantallas con plantillas de texto.",
     "Mensajes de error con textContent (mostrarAlerta), opciones de talla con new Option y limpieza con replaceChildren; escapar la talla.",
     "ESLint no-unsanitized: de 5 avisos a 3. Los 3 restantes se revisaron: todo valor dinámico pasa por esc() o es un número.",
     "Parcialmente resuelto"),
    ("C5", "H05, H10, H11 · Complejidad y ámbito global",
     "Toda la lógica de eventos creció dentro de una sola función bind.",
     "Dividir en bindCatalogo, bindLogin, bindVenta, bindContenidos, bindAprobacion y bindReporte, y encapsular el archivo en una función con “use strict”.",
     "ESLint: max-lines-per-function 1→0, cognitive-complexity 1→0, no-implicit-globals 5→0, no-return-assign 5→0, complexity 4→2.",
     "Resuelto"),
    ("C6", "H06, H07, H08 · Lógica de la venta",
     "Lectura duplicada de la cantidad y uso de un stock leído antes de confirmar.",
     "Función única leerCantidad; el resumen muestra “—” si la cantidad no es válida o supera el stock; el stock se vuelve a leer al confirmar.",
     "Prueba en navegador: venta de 2 camisetas talla 34 (stock 12→10) y error al pedir 5 de la talla 38 (hay 3).",
     "Resuelto"),
    ("C7", "H09 · Fecha de aprobación fija",
     "Se dejó un valor de ejemplo en el código.",
     "Usar new Date().toLocaleDateString(\"es-EC\").",
     "Inspección manual: ya no existe la fecha fija en el código.",
     "Resuelto"),
]

ANTES_C1 = '''if (u.value.trim() === "secretaria" && p.value === "parroquia2026") { S.user = "secretaria"; S.loginTries = 5; toast("Sesión iniciada"); go("panel"); return }
S.loginTries -= 1;
$("loginErr").innerHTML = `<div class="alert err" role="alert">Usuario o contraseña incorrectos. ${S.loginTries > 0 ? `Te quedan ...` : "Cuenta bloqueada por 15 minutos."}</div>`;'''
DESPUES_C1 = '''if (Date.now() < S.lockedUntil) {
  mostrarAlerta($("loginErr"), "err", `Cuenta bloqueada temporalmente. Intenta de nuevo en ${BLOQUEO_MINUTOS} minutos.`);
  return;
}
const valido = usuario.value.trim() === USUARIO_PRUEBA && await sha256(clave.value) === HASH_CLAVE_PRUEBA;
...
S.loginTries -= 1;
if (S.loginTries <= 0) {
  S.lockedUntil = Date.now() + BLOQUEO_MINUTOS * MS_POR_MINUTO;
  S.loginTries = INTENTOS_MAX;
  mostrarAlerta($("loginErr"), "err", `Usuario o contraseña incorrectos. Cuenta bloqueada por ${BLOQUEO_MINUTOS} minutos.`);
  return;
}'''
ANTES_C3 = '''const priceFor = (p, size) => p.sizes ? (Number(size) >= 38 ? 11 : 10) : p.price;
... money(10) ...
<p class="note">Tallas 30 a 36: USD 10. Tallas 38 y 40: USD 11.</p>'''
DESPUES_C3 = '''const PRECIO = { base: 10, grande: 11, tallaGrandeDesde: 38 };
const priceFor = (p, size) => {
  if (!p.sizes) return p.price;
  return Number(size) >= PRECIO.tallaGrandeDesde ? PRECIO.grande : PRECIO.base;
};
... money(PRECIO.base) ...
Tallas menores a ${PRECIO.tallaGrandeDesde}: ${money(PRECIO.base)}. Desde la talla ${PRECIO.tallaGrandeDesde}: ${money(PRECIO.grande)}.'''
ANTES_C7 = '''S.content.date = "21/11/2026";'''
DESPUES_C7 = '''// Corrección: la fecha de aprobación es la del día, no un valor fijo
S.content.date = new Date().toLocaleDateString("es-EC");'''


# ---------------------------------------------------------------- utilidades
def table(head, rows, widths=None, cls=""):
    cg = "".join(f'<col style="width:{w}">' for w in widths) if widths else ""
    th = "".join(f"<th>{h}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="{cls}"><colgroup>{cg}</colgroup><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>'

FIG = [0]; TAB = [0]
def fig(src, cap, w="100%"):
    FIG[0] += 1
    return f'<figure><img src="{src}" style="width:{w}"><figcaption><b>Figura {FIG[0]}.</b> {cap}</figcaption></figure>'
def cap(t):
    TAB[0] += 1
    return f'<div class="tcap"><b>Tabla {TAB[0]}.</b> {t}</div>'
def code(t, titulo):
    return f'<div class="code"><div class="ct">{titulo}</div><pre>{E(t)}</pre></div>'
SEV = {"Crítica": "err", "Alta": "err", "Media": "warn", "Baja": "low", "Resuelto": "ok", "Parcialmente resuelto": "warn"}
def b(t):
    return f'<span class="b {SEV.get(t, "low")}">{t}</span>'


def body():
    FIG[0] = 0; TAB[0] = 0
    s = []
    s.append(f"""<h1 id="s1" class="first-body">1. Introducción</h1>
<p>El análisis estático revisa el código fuente <b>sin ejecutarlo</b> para encontrar defectos potenciales, malas prácticas, vulnerabilidades y problemas de mantenibilidad. En esta práctica el Grupo 5 aplicó dos técnicas complementarias sobre el módulo JavaScript de la Web Parroquial: una inspección manual línea por línea y un análisis automatizado con ESLint. Luego se compararon ambos resultados, se corrigieron los hallazgos más relevantes y se repitió el análisis para comprobar las mejoras [1].</p>
<div class="box"><b>Repositorio del código evaluado:</b> <a href="{REPO}">{REPO}</a><br>
Commit <b>5a554b1</b>: código original analizado · Commit <b>87f3c9b</b>: código con las correcciones. Los resultados completos de ESLint están en la carpeta <code>resultados/</code>.</div>""")

    s.append("""<h1 id="s2">2. Descripción del módulo evaluado</h1>""")
    s.append(table(["Aspecto", "Descripción"], [
        ["Archivo", "<code>src/app.js</code> (325 líneas en la versión original), cargado por <code>index.html</code>."],
        ["Lenguaje", "JavaScript (ECMAScript 2022) ejecutado en el navegador, sin frameworks."],
        ["Propósito", "Lógica del prototipo de la Web Parroquial: catálogo de artículos con stock por talla, requisitos de sacramentos, ingreso del personal, registro de ventas presenciales, edición de contenidos con aprobación del párroco y reporte por período."],
        ["Funciones principales", "<code>priceFor</code> (precio por talla), <code>stockOf</code> y <code>stateOf</code> (disponibilidad), <code>esc</code> (escapado de HTML), <code>render</code> (dibuja la pantalla según la ruta), vistas <code>V.catalogo</code>, <code>V.venta</code>, <code>V.contenidos</code>, etc., y <code>bind</code> (eventos de formularios: ingreso, venta, contenidos, reporte)."],
        ["Características revisables", "Validaciones de formularios, reglas de negocio (precios, stock, bloqueo de ingreso), construcción de HTML con plantillas de texto e <code>innerHTML</code>, estado global mutable, complejidad de funciones y legibilidad de nombres."],
    ], ["22%", "78%"]))
    s.append(cap("Descripción del módulo."))

    s.append("""<h1 id="s3">3. Resultados de la inspección manual</h1>
<p>Antes de usar la herramienta, los integrantes revisaron el archivo completo con una lista de comprobación: legibilidad y organización, nombres, código duplicado, validaciones, errores lógicos, manejo de datos, buenas prácticas y seguridad. Cada hallazgo se anotó con su línea y su posible consecuencia.</p>""")
    s.append(table(["ID", "Ubicación", "Hallazgo", "Posible consecuencia"],
                   [[f"<b>{i}</b>", u, h, c] for i, u, h, c in MANUAL], ["7%", "19%", "40%", "34%"], "small"))
    s.append(cap("Hallazgos de la inspección manual."))
    s.append("""<p>Los dos hallazgos más graves (M01 y M02) afectan la seguridad del ingreso. El defecto M02 se <b>confirmó</b> después, con el código original: tras 5 intentos fallidos, la contraseña correcta todavía permite entrar al panel (figura 7).</p>""")

    s.append("""<h1 id="s4">4. Herramienta de análisis estático seleccionada</h1>
<p>Se eligió <b>ESLint 10.15</b>, el analizador estándar para JavaScript, porque se ejecuta localmente sin servidor, se configura en un solo archivo y admite complementos. Se combinaron tres conjuntos de reglas para cubrir los cuatro tipos de problema que pide la práctica:</p>""")
    s.append(table(["Conjunto de reglas", "Qué detecta", "Tipo de problema"], [
        ["<code>@eslint/js</code> recommended", "Variables no usadas, código inalcanzable, errores comunes", "Defectos potenciales"],
        ["<code>eslint-plugin-sonarjs</code> recommended", "Complejidad cognitiva, ternarios anidados, plantillas anidadas, duplicación [3]", "Mantenibilidad"],
        ["<code>eslint-plugin-no-unsanitized</code>", "Asignaciones a innerHTML con contenido dinámico [4]", "Posibles vulnerabilidades"],
        ["Reglas adicionales", "max-statements-per-line, id-length, complexity, max-lines-per-function, no-magic-numbers, eqeqeq, no-implicit-globals, no-return-assign", "Estilo y mantenibilidad"],
    ], ["30%", "48%", "22%"]))
    s.append(cap("Configuración de reglas de ESLint."))
    s.append('<h2 id="s41">4.1. Evidencias de configuración y ejecución</h2>')
    s.append(fig("img/01_instalacion.png", "Paquetes instalados y versión de ESLint.", "82%"))
    s.append(fig("img/02_configuracion.png", "Archivo de configuración <code>eslint.config.mjs</code>.", "82%"))
    s.append(fig("img/03_eslint_antes.png", "Ejecución sobre el código original: 162 problemas (26 errores, 136 advertencias)."))
    s.append(fig("img/03b_eslint_antes_relevantes.png", "Avisos del código original sin contar nombres cortos ni instrucciones por línea.", "92%"))
    s.append("""<p><b>Interpretación.</b> De los 162 avisos, 124 son de estilo (90 por nombres de una letra y 34 por varias instrucciones en una línea). Los avisos más relevantes son los de <code>no-unsanitized</code> (5), complejidad (bind con 79 líneas y complejidad 14; funciones de venta con complejidad 16 y 17), <code>no-implicit-globals</code> (5), <code>no-return-assign</code> (5) y números mágicos en el precio por talla (38 y 11). ESLint marca como “error” reglas de estilo de SonarJS: la severidad de la herramienta no equivale a la gravedad real del problema.</p>""")

    s.append("""<h1 id="s5">5. Matriz de hallazgos identificados</h1>
<p>Se consolidaron los hallazgos de ambos métodos y se clasificaron en <b>defecto potencial</b>, <b>advertencia de mantenibilidad</b>, <b>incumplimiento de estilo</b> y <b>posible vulnerabilidad</b>.</p>""")
    s.append(table(["ID", "Ubicación", "Descripción", "Tipo", "Origen", "Severidad", "Posible impacto", "Recomendación"],
                   [[f"<b>{r[0]}</b>", r[1], r[2], r[3], r[4], b(r[5]), r[6], r[7]] for r in MATRIZ],
                   ["5%", "14%", "17%", "11%", "9%", "9%", "16%", "19%"], "tiny"))
    s.append(cap("Matriz de hallazgos."))
    s.append("""<p><b>Resumen:</b> 16 hallazgos — 2 vulnerabilidades (una real y una posible), 6 defectos potenciales, 3 de mantenibilidad y 5 de estilo. Por origen: 7 solo de la inspección manual, 4 solo de la herramienta y 5 detectados por ambos métodos.</p>""")

    s.append("""<h1 id="s6">6. Comparación entre análisis manual y automatizado</h1>""")
    s.append(table(["Pregunta", "Respuesta del equipo"], [
        ["¿Qué problemas identificaron ambos métodos?", "innerHTML sin sanear (H03), precios como números mágicos (H04), funciones largas y complejas (H05), nombres cortos (H13) y varias instrucciones por línea (H14). Son problemas de <b>forma</b> visibles en la estructura del código."],
        ["¿Qué detectó solo la herramienta?", "Funciones en el ámbito global (H10), funciones flecha que devuelven una asignación (H11) —en L302 el botón Cancelar devolvía el resultado de <code>innerHTML = \"\"</code>—, ternarios anidados (H12) y los números 2600 y 6 (H16). También dio cifras exactas de complejidad que a simple vista solo se intuían."],
        ["¿Qué detectó solo la inspección manual?", "La contraseña en texto plano (H01), el bloqueo que no bloquea (H02), la doble lectura de la cantidad (H06), el total con stock insuficiente (H07), el stock desactualizado al confirmar (H08), la fecha fija (H09) y el reporte con datos fijos (H15). Son problemas de <b>significado</b>: el código es sintácticamente correcto pero no hace lo que el requisito pide."],
        ["¿Qué advertencias requieren revisión antes de considerarse defectos?", "<code>no-unsanitized</code> en <code>render</code> (L236): el HTML se arma con datos escapados con esc(), por lo que hoy no es explotable. <code>no-magic-numbers</code> con 16 (base hexadecimal) no es un defecto. Los 78 avisos de <code>id-length</code> por <code>e</code>, <code>p</code> o <code>n</code> en funciones cortas son de estilo. La comparación de fechas como texto (M12) es correcta por el formato ISO."],
        ["¿Por qué el análisis estático no garantiza el funcionamiento?", "La herramienta revisa patrones, no reglas del negocio: no sabe que el bloqueo debía impedir el ingreso ni que la fecha no puede ser fija. Tampoco ejecuta el programa, así que no ve datos reales, concurrencia ni la interacción con el usuario. Por eso se combinó con inspección manual y con una comprobación en el navegador [2]."],
    ], ["30%", "70%"]))
    s.append(cap("Comparación de los métodos."))

    s.append("""<h1 id="s7">7. Correcciones y nuevo análisis</h1>
<p>Se corrigieron siete grupos de hallazgos (más de los tres pedidos). Para cada uno se registró la causa, la solución, la comprobación y el resultado.</p>""")
    s.append(table(["ID", "Hallazgo", "Causa probable", "Solución aplicada", "Comprobación", "Estado"],
                   [[f"<b>{c[0]}</b>", c[1], c[2], c[3], c[4], b(c[5])] for c in CORREC],
                   ["5%", "14%", "19%", "24%", "26%", "12%"], "tiny"))
    s.append(cap("Correcciones aplicadas y su comprobación."))
    s.append('<h2 id="s71">7.1. Código antes y después</h2>')
    s.append(code(ANTES_C1, "C1 · Antes (commit 5a554b1, L261–263)") + code(DESPUES_C1, "C1 · Después (bindLogin)"))
    s.append(code(ANTES_C3, "C3 · Antes (L18, L66, L100)") + code(DESPUES_C3, "C3 · Después"))
    s.append(code(ANTES_C7, "C7 · Antes (L316)") + code(DESPUES_C7, "C7 · Después (bindAprobacion)"))
    s.append('<h2 id="s72">7.2. Evidencias del nuevo análisis</h2>')
    s.append(fig("img/04_eslint_despues.png", "ESLint sobre el código corregido: 93 problemas (8 errores, 85 advertencias)."))
    s.append(fig("img/05_resumen_reglas.png", "Avisos por regla antes y después de las correcciones.", "82%"))
    s.append(fig("img/06_comprobacion.png", "Comprobación en navegador del código corregido y confirmación del defecto H02 en el original.", "92%"))
    s.append(fig("img/07_git_log.png", "Historial del repositorio con el código original y las correcciones.", "92%"))
    s.append(table(["Indicador", "Antes", "Después", "Variación"], [
        ["Problemas totales", "162", "93", "−43 %"],
        ["Errores", "26", "8", "−69 %"],
        ["no-unsanitized (HTML sin sanear)", "5", "3", "−2 (revisados)"],
        ["Complejidad / funciones largas", "6", "2", "−4"],
        ["Globales implícitas y asignaciones en return", "10", "0", "−10"],
        ["Números mágicos", "7", "1", "−6"],
        ["Varias instrucciones por línea", "34", "4", "−30"],
        ["Nombres cortos (id-length)", "90", "78", "−12 (pendiente)"],
    ], ["46%", "16%", "16%", "22%"]))
    s.append(cap("Resultado del nuevo análisis."))
    s.append("""<p>Los avisos que permanecen se revisaron uno por uno: los 3 de <code>no-unsanitized</code> usan datos escapados; los 78 de nombres cortos son en su mayoría parámetros de una letra en funciones de una línea y se dejan para una refactorización posterior; las dos funciones con complejidad 11 superan el límite por un punto. La autenticación definitiva (H01) y el filtrado del reporte (H15) quedan pendientes para la implementación con servidor.</p>""")

    s.append("""<h1 id="s8">8. Conclusiones técnicas</h1>
<ol>
<li>La inspección manual encontró los problemas más graves: la contraseña en el código y el bloqueo que no bloqueaba. ESLint no puede detectarlos porque no conoce las reglas del negocio.</li>
<li>ESLint aportó precisión y alcance: midió la complejidad, encontró patrones que la revisión pasó por alto (globales implícitas, asignaciones devueltas) y permitió comprobar las mejoras con cifras, de 162 a 93 avisos y de 26 a 8 errores.</li>
<li>Una advertencia no es un defecto confirmado: varios avisos de seguridad y estilo se revisaron y se justificaron, y la severidad “error” de algunas reglas de estilo no reflejaba un riesgo real.</li>
<li>Las correcciones se comprobaron dos veces: con un nuevo análisis estático y con pruebas en el navegador. Esto confirma que el análisis estático debe complementarse con pruebas dinámicas para asegurar el funcionamiento.</li>
</ol>""")

    s.append("""<h1 id="ref">Referencias bibliográficas</h1>
<div class="ref">
<p>[1] <i>IEEE Standard for System, Software, and Hardware Verification and Validation</i>, IEEE Std 1012-2016, 2016.</p>
<p>[2] <i>Systems and software engineering — Systems and software Quality Requirements and Evaluation (SQuaRE) — Product quality model</i>, ISO/IEC 25010:2023, 2023.</p>
<p>[3] SonarSource, “eslint-plugin-sonarjs”. [En línea]. Disponible: https://www.npmjs.com/package/eslint-plugin-sonarjs. [Accedido: 25-nov-2026].</p>
<p>[4] Mozilla, “eslint-plugin-no-unsanitized”. [En línea]. Disponible: https://github.com/mozilla/eslint-plugin-no-unsanitized. [Accedido: 25-nov-2026].</p>
<p>[5] OpenJS Foundation, “ESLint — Find and fix problems in your JavaScript code”. [En línea]. Disponible: https://eslint.org/docs/latest/. [Accedido: 25-nov-2026].</p>
</div>""")
    out = "\n".join(s)
    def keep(m):
        return m.group(0) if m.group(1).count("<tr>") > 9 else f'<div class="tw">{m.group(1)}{m.group(2)}</div>'
    return re.sub(r'(<table class="[^"]*">(?:(?!</table>).)*</table>)\s*(<div class="tcap">.*?</div>)', keep, out, flags=re.S)


TOC = [("s1", "1. Introducción"), ("s2", "2. Descripción del módulo evaluado"), ("s3", "3. Resultados de la inspección manual"),
       ("s4", "4. Herramienta de análisis estático seleccionada"), ("s5", "5. Matriz de hallazgos identificados"),
       ("s6", "6. Comparación entre análisis manual y automatizado"), ("s7", "7. Correcciones y nuevo análisis"),
       ("s8", "8. Conclusiones técnicas"), ("ref", "Referencias bibliográficas")]


def page(pages):
    integ = "".join(f'<div class="person"><span>{E(n)}</span><span class="orcid"><i>iD</i> {o}</span></div>' for n, o in DATA["integrantes"])
    toc = "".join(f'<div class="toc-row"><span>{E(t)}</span><span class="dots"></span><span>{pages.get(i, "")}</span></div>' for i, t in TOC)
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{E(DATA['tema'])}</title>
<style>
@page {{ size: A4; margin: 24mm 22mm 22mm 24mm;
  @top-left {{ content: "UTEQ  |  Ingeniería de Software"; font: 700 9.5pt "Times New Roman", serif; border-bottom: .6pt solid #D8E2EB; vertical-align: bottom; padding-bottom: 4pt }}
  @top-right {{ content: "Informe académico"; font: 9.5pt "Times New Roman", serif; border-bottom: .6pt solid #D8E2EB; vertical-align: bottom; padding-bottom: 4pt }}
  @bottom-center {{ content: counter(page); font: 10pt "Times New Roman", serif }} }}
@page cover {{ margin: 0; @top-left {{ content: none; border: 0 }} @top-right {{ content: none; border: 0 }} @bottom-center {{ content: none }} }}
* {{ box-sizing: border-box }}
body {{ margin: 0; font-family: "Times New Roman", Times, serif; font-size: 12pt; line-height: 1.4; color: #000 }}
.cover {{ page: cover; height: 297mm; position: relative; display: flex; flex-direction: column; align-items: center; padding: 0 24mm }}
.band-top {{ position: absolute; inset: 0 0 auto 0; height: 10.5mm; background: #122A46; border-bottom: .7mm solid #008D95 }}
.band-bot {{ position: absolute; inset: auto 0 0 0; height: 10.5mm; background: #122A46 }}
.band-gold {{ position: absolute; bottom: 10.5mm; left: 18mm; width: 39mm; height: .7mm; background: #E2B45E }}
.cover .logo {{ margin-top: 17mm; height: 31mm }}
.u1 {{ font-weight: 700; font-size: 12pt; margin-top: 5.5mm }} .u2 {{ font-size: 10.5pt; margin-top: 1.6mm }} .u3 {{ font-weight: 700; font-size: 10.5pt; margin-top: 1.2mm }}
.ia {{ font-weight: 700; font-size: 10.5pt; margin-top: 12.5mm; letter-spacing: .02em }}
.tema {{ font-weight: 700; font-size: 23pt; line-height: 1.17; text-align: center; margin-top: 4.8mm; max-width: 160mm }}
.gold {{ width: 37mm; height: 2pt; background: #E2B45E; margin: 6.5mm 0 3.5mm }}
.materia {{ font-size: 14pt }}
.cbox {{ margin-top: auto; width: 100%; background: #F3F7FA; border: .7pt solid #D8E2EB; border-radius: 2mm; padding: 12pt 15pt }}
.cgrid {{ display: grid; grid-template-columns: 31mm 1fr; row-gap: 7pt; align-items: center; font-size: 11.5pt }}
.person {{ display: flex; justify-content: space-between; gap: 10pt }}
.orcid {{ white-space: nowrap; font-size: 10.5pt }}
.orcid i {{ display: inline-grid; place-items: center; width: 13pt; height: 13pt; border-radius: 50%; background: #A6CE39; color: #fff; font: 700 6.5pt Arial, sans-serif; font-style: normal; vertical-align: 1pt; margin-right: 3pt }}
.place {{ font-weight: 700; margin: 6.5mm 0 21mm }}
.toc-row {{ display: flex; gap: 6pt; font-weight: 700; margin: 9pt 0 }}
.toc-row .dots {{ flex: 1; border-bottom: 1.2pt dotted #555; transform: translateY(-4pt) }}
h1 {{ font-size: 16.5pt; margin: 19pt 0 10pt; break-after: avoid; page-break-before: always }}
h1.first {{ page-break-before: auto; margin-top: 0 }}
h2 {{ font-size: 13.5pt; margin: 13pt 0 5pt; break-after: avoid }}
p {{ margin: 0 0 7pt; text-align: justify }}
ol {{ margin: 0 0 7pt; padding-left: 20pt }} li {{ margin-bottom: 4pt; text-align: justify }}
a {{ color: #000 }}
code {{ font-family: Consolas, "Courier New", monospace; font-size: 9.5pt; background: #F3F7FA; padding: 0 2pt; border-radius: 2pt }}
.box {{ background: #F3F7FA; border: .6pt solid #D8E2EB; border-left: 3pt solid #008D95; border-radius: 2mm; padding: 8pt 11pt; margin: 8pt 0 10pt; font-size: 11.5pt; break-inside: avoid; word-break: break-word }}
table {{ width: 100%; border-collapse: collapse; font-size: 10.5pt; margin: 6pt 0 2pt; border-top: 1.2pt solid #000; border-bottom: 1.2pt solid #000 }}
table.small {{ font-size: 9.4pt }} table.tiny {{ font-size: 8.3pt; line-height: 1.25 }}
thead th {{ text-align: left; font-weight: 700; padding: 4pt 4pt; border-bottom: .8pt solid #000; vertical-align: bottom }}
td {{ padding: 3.5pt 4pt; vertical-align: top; border-bottom: .4pt solid #D8E2EB; text-align: left }}
tr {{ break-inside: avoid }} thead {{ display: table-header-group }}
td:first-child b {{ white-space: nowrap }}
.tw {{ break-inside: avoid }}
.tcap {{ font-size: 10.5pt; text-align: center; margin: 3pt 0 11pt }}
.b {{ display: inline-block; font-weight: 700; padding: 1pt 4pt; border-radius: 3pt; font-size: 8pt }}
.b.ok {{ background: #E1F2E7; color: #1F6B3E }} .b.warn {{ background: #FCEFD3; color: #8A5600 }} .b.err {{ background: #FBE4E2; color: #9E2E28 }} .b.low {{ background: #EAEFF4; color: #33475B }}
figure {{ margin: 6pt 0 10pt; text-align: center; break-inside: avoid }}
figure img {{ border: .6pt solid #D8E2EB; max-height: 205mm; object-fit: contain }}
figcaption {{ font-size: 10pt; margin-top: 3pt; text-align: center }}
.code {{ border: .6pt solid #D8E2EB; border-radius: 2mm; margin: 6pt 0 8pt; break-inside: avoid; overflow: hidden }}
.code .ct {{ background: #F3F7FA; font-size: 9.5pt; font-weight: 700; padding: 3pt 7pt; border-bottom: .6pt solid #D8E2EB }}
.code pre {{ margin: 0; padding: 6pt 8pt; font: 8.3pt/1.35 Consolas, "Courier New", monospace; white-space: pre-wrap; word-break: break-word; background: #F7F9FC }}
.ref p {{ padding-left: 24pt; text-indent: -24pt; text-align: left }}
</style></head><body>
<section class="cover">
  <div class="band-top"></div><div class="band-bot"></div><div class="band-gold"></div>
  <img class="logo" src="logo-uteq.png">
  <div class="u1">UNIVERSIDAD TÉCNICA ESTATAL DE QUEVEDO</div>
  <div class="u2">FACULTAD DE CIENCIAS DE LA COMPUTACIÓN</div>
  <div class="u3">CARRERA DE INGENIERÍA DE SOFTWARE</div>
  <div class="ia">INFORME ACADÉMICO</div>
  <div class="tema">{E(DATA['tema'])}</div>
  <div class="gold"></div>
  <div class="materia">Verificación y Validación de Software</div>
  <div class="cbox"><div class="cgrid">
    <b>Grupo:</b><span>{DATA['grupo']}</span>
    <b>Integrantes:</b><div style="display:grid;gap:6pt">{integ}</div>
    <b>Docente:</b><span>{DATA['docente']}</span>
    <b>Curso:</b><span>{DATA['curso']}</span>
    <b>Entrega:</b><span>{DATA['entrega']}</span>
  </div></div>
  <div class="place">Quevedo – Ecuador&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;2026</div>
</section>
<section><h1 class="first">Contenido</h1>{toc}</section>
{body()}
</body></html>"""


def build(pages):
    src = os.path.join(HERE, "informe.html")
    open(src, "w", encoding="utf-8").write(page(pages))
    out = os.path.join(os.path.dirname(HERE), "Informe_Analisis_Estatico_Grupo5.pdf")
    subprocess.run([r"C:\Program Files\Google\Chrome\Application\chrome.exe", "--headless=new", "--disable-gpu",
                    "--no-pdf-header-footer", f"--print-to-pdf={out}", "file:///" + src.replace("\\", "/")],
                   capture_output=True, timeout=120)
    return out


out = build({})
doc = fitz.open(out)
pages = {}
for key, title in TOC:
    for i in range(2, doc.page_count):
        if title in doc[i].get_text():
            pages[key] = i + 1
            break
doc.close()
out = build(pages)
print(out, pages, fitz.open(out).page_count)
