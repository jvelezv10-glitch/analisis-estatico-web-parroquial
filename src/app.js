(function () {
"use strict";

// Reglas de negocio en un solo lugar (antes estaban repetidas como números sueltos)
const PRECIO = { base: 10, grande: 11, tallaGrandeDesde: 38 };
const STOCK_BAJO = 3;
const INTENTOS_MAX = 5;
const BLOQUEO_MINUTOS = 15;
const MS_POR_MINUTO = 60000;
const DURACION_AVISO_MS = 2600;
const DIGITOS_RECIBO = 6;
// Solo para el prototipo: el hash reemplaza la contraseña en texto plano.
// En la implementación real la validación debe hacerse en el servidor.
const USUARIO_PRUEBA = "secretaria";
const HASH_CLAVE_PRUEBA = "b4f7f6fea7dd6d05e4a43a5eba32ad19ae2a77b599bac190c7fa2f1b4288870d";

const ICON = {
  box: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M3 7l9-4 9 4-9 4-9-4z"/><path d="M3 7v10l9 4 9-4V7"/></svg>',
  check: '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>'
};
const S = {
  user: null, query: "", cat: "Todos", onlyAvail: false, sel: "camiseta", size: null, tab: "Bautismo",
  receipt: 124, lastSale: null, content: { status: "Publicado", text: "", by: "Secretaría", date: "12/11/2026" },
  loginTries: INTENTOS_MAX, lockedUntil: 0
};
const PRODUCTS = [
  { id: "camiseta", name: "Camiseta de catequesis", cat: "Camisetas", sizes: { 30: 6, 32: 9, 34: 12, 36: 4, 38: 3, 40: 0 } },
  { id: "libro", name: "Libro de catequesis – Primera comunión", cat: "Libros", price: 5, stock: 18 },
  { id: "rosario-madera", name: "Rosario de madera", cat: "Rosarios", price: 3.5, stock: 25 },
  { id: "rosario-cristal", name: "Rosario de cristal", cat: "Rosarios", price: 6, stock: 2 },
  { id: "medalla", name: "Medalla de la Virgen", cat: "Medallas", price: 2.5, stock: 40 },
  { id: "biblia", name: "Biblia de bolsillo", cat: "Libros", price: 12, stock: 0 },
  { id: "vela", name: "Vela bautismal", cat: "Velas", price: 4, stock: 11 }
];
const priceFor = (p, size) => {
  if (!p.sizes) return p.price;
  return Number(size) >= PRECIO.tallaGrandeDesde ? PRECIO.grande : PRECIO.base;
};
const stockOf = p => p.sizes ? Object.values(p.sizes).reduce((a, b) => a + b, 0) : p.stock;
const money = n => "USD " + n.toFixed(2).replace(".", ",");
const BAUTISMO = [
  "Partida de nacimiento del niño o niña (original y copia).",
  "Cédula de identidad de los padres y padrinos (copia).",
  "Padrinos católicos, mayores de 16 años y confirmados.",
  "Certificado de la charla prebautismal (padres y padrinos).",
  "Inscripción en secretaría con al menos 15 días de anticipación."
];
S.content.text = BAUTISMO.join("\n");
const stateOf = n => {
  if (n === 0) return ["err", "Agotado"];
  if (n <= STOCK_BAJO) return ["warn", "Pocas unidades"];
  return ["ok", "Disponible"];
};
const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function toast(msg) {
  const aviso = document.createElement("div");
  aviso.className = "toast";
  aviso.setAttribute("role", "status");
  aviso.textContent = msg;
  document.body.appendChild(aviso);
  setTimeout(() => aviso.remove(), DURACION_AVISO_MS);
}
function go(ruta) {
  if (location.hash === "#" + ruta) render();
  else location.hash = ruta;
}
// Muestra un mensaje usando textContent (sin insertar HTML)
function mostrarAlerta(contenedor, tipo, texto) {
  const alerta = document.createElement("div");
  alerta.className = "alert " + tipo;
  alerta.setAttribute("role", "alert");
  alerta.textContent = texto;
  contenedor.replaceChildren(alerta);
}
async function sha256(texto) {
  const datos = new TextEncoder().encode(texto);
  const hash = await crypto.subtle.digest("SHA-256", datos);
  return [...new Uint8Array(hash)].map(b => b.toString(16).padStart(2, "0")).join("");
}
// Una sola forma de leer la cantidad (antes se usaba parseInt en un lugar y Number en otro)
const leerCantidad = valor => {
  const qty = Number(valor);
  return Number.isInteger(qty) && qty > 0 ? qty : 0;
};

const V = {};
V.inicio = () => `
  <section class="hero">
    <div class="lead">
      <span class="pill" style="background:rgba(255,255,255,.18);color:inherit;justify-self:start">Despacho parroquial</span>
      <h1>Consulta requisitos, horarios y artículos sin ir a la iglesia</h1>
      <p>Revisa qué documentos necesitas para cada sacramento, las convocatorias de catequesis y la disponibilidad de artículos religiosos.</p>
      <div class="toolbar"><a class="btn gold" href="#sacramentos">Ver requisitos</a><a class="btn ghost" style="color:inherit;border-color:rgba(255,255,255,.4)" href="#catalogo">Ver catálogo</a></div>
    </div>
    <div class="card hours">
      <h3>Horario de secretaría</h3>
      <div class="row"><span>Martes a sábado</span><b>15:00 – 19:00</b></div>
      <div class="row"><span>Domingo y lunes</span><span class="pill err">Cerrado</span></div>
      <p class="note" style="margin:0">Las ventas e inscripciones se realizan de forma presencial en secretaría.</p>
    </div>
  </section>
  <section class="grid quick">
    <a class="card" href="#sacramentos"><span class="k">Sacramentos</span><h3>Requisitos de bautismo</h3><span style="color:var(--muted)">Documentos, padrinos y charla prebautismal.</span></a>
    <a class="card" href="#catequesis"><span class="k">Catequesis</span><h3>Convocatoria 2026–2027</h3><span><span class="pill ok">Abierta</span> hasta el 30/11/2026</span></a>
    <a class="card" href="#catalogo"><span class="k">Catálogo</span><h3>Camisetas por talla</h3><span style="color:var(--muted)">Consulta qué tallas quedan disponibles.</span></a>
  </section>`;

V.catalogo = () => {
  const cats = ["Todos", "Camisetas", "Libros", "Rosarios", "Medallas", "Velas"];
  const q = S.query.trim().toLowerCase();
  const list = PRODUCTS.filter(p => (S.cat === "Todos" || p.cat === S.cat) && (!q || p.name.toLowerCase().includes(q)) && (!S.onlyAvail || stockOf(p) > 0));
  const cards = list.map(p => { const [k, t] = stateOf(stockOf(p)); return `
    <a class="card prod" href="#articulo" data-id="${p.id}">
      <div class="img">${ICON.box}</div>
      <span style="font-size:.8rem;color:var(--muted)">${p.cat}</span>
      <h3>${esc(p.name)}</h3>
      <div class="meta"><span class="price">${p.sizes ? "<small>desde</small> " + money(PRECIO.base) : money(p.price)}</span><span class="pill ${k}">${t}</span></div>
    </a>` }).join("");
  return `
  <div class="crumbs"><a href="#inicio">Inicio</a> / Catálogo</div>
  <h1>Catálogo de artículos religiosos</h1>
  <div class="card" style="display:grid;gap:12px">
    <form class="search" id="fSearch" role="search"><input id="q" type="search" placeholder="Buscar por nombre, por ejemplo: rosario" value="${esc(S.query)}" aria-label="Buscar artículos"><button class="btn primary">Buscar</button></form>
    <div class="toolbar"><div class="chips">${cats.map(c => `<button class="chip ${c === S.cat ? "on" : ""}" data-cat="${c}">${c}</button>`).join("")}</div>
    <label style="display:flex;gap:6px;align-items:center;font-size:.88rem;margin-left:auto"><input id="avail" type="checkbox" style="width:auto" ${S.onlyAvail ? "checked" : ""}> Solo disponibles</label></div>
  </div>
  <p style="margin:0;color:var(--muted)" aria-live="polite">${list.length} ${list.length === 1 ? "artículo encontrado" : "artículos encontrados"}${q ? ` para “${esc(S.query)}”` : ""}</p>
  ${list.length ? `<div class="grid">${cards}</div>` : `
  <div class="card empty"><h3>No encontramos artículos para “${esc(S.query)}”</h3>
    <p style="margin:0;color:var(--muted)">Revisa la ortografía, prueba con otra categoría o desactiva el filtro “Solo disponibles”.</p>
    <button class="btn ghost" id="clear">Ver todo el catálogo</button></div>`}
  <p class="note">Los precios y la disponibilidad son referenciales. La compra se realiza en secretaría.</p>`;
};

V.articulo = () => {
  const p = PRODUCTS.find(x => x.id === S.sel) || PRODUCTS[0];
  const sizes = p.sizes ? Object.entries(p.sizes).map(([s, n]) => `<button class="size ${S.size === s ? "on" : ""}" data-size="${s}" ${n === 0 ? "disabled" : ""}><b>${s}</b><small>${n === 0 ? "agotada" : n + " u."}</small></button>`).join("") : "";
  const n = p.sizes ? (S.size ? p.sizes[S.size] : null) : p.stock;
  const st = n === null ? null : stateOf(n);
  return `
  <div class="crumbs"><a href="#inicio">Inicio</a> / <a href="#catalogo">Catálogo</a> / ${esc(p.name)}</div>
  <section class="two">
    <div class="card prod"><div class="img" style="aspect-ratio:1">${ICON.box}</div></div>
    <div style="display:grid;gap:14px;align-content:start">
      <span style="color:var(--muted)">${p.cat}</span><h1>${esc(p.name)}</h1>
      ${p.sizes ? `<div><b>Elige una talla</b><div class="sizes" style="margin-top:8px">${sizes}</div></div>` : ""}
      ${p.sizes && !S.size ? `<div class="card sum"><div class="row"><span>Precio</span><span class="price"><small>desde</small> ${money(PRECIO.base)}</span></div>
      <div class="row"><span>Disponibilidad</span><span style="color:var(--muted)">Elige una talla para ver el precio exacto y las unidades</span></div></div>` : `
      <div class="card sum"><div class="row"><span>Precio${p.sizes ? " talla " + S.size : ""}</span><span class="price">${money(priceFor(p, S.size))}</span></div>
      <div class="row"><span>Disponibilidad</span><span class="pill ${st[0]}">${st[1]} · ${n} u.</span></div></div>`}
      ${p.sizes ? `<p class="note" style="margin:0">Tallas menores a ${PRECIO.tallaGrandeDesde}: ${money(PRECIO.base)}. Desde la talla ${PRECIO.tallaGrandeDesde}: ${money(PRECIO.grande)}.</p>` : ""}
      <p class="note" style="margin:0">Para comprar, acércate a secretaría de martes a sábado, de 15:00 a 19:00.</p>
    </div>
  </section>`;
};

V.sacramentos = () => {
  const tabs = ["Bautismo", "Primera comunión", "Confirmación", "Matrimonio"];
  const body = S.tab === "Bautismo" ? `
    <div class="two">
      <div style="display:grid;gap:10px"><h3>Requisitos</h3><ul class="req">${S.content.text.split("\n").filter(Boolean).map(r => `<li>${esc(r)}</li>`).join("")}</ul></div>
      <div style="display:grid;gap:10px;align-content:start">
        <h3>Charla prebautismal</h3><p style="margin:0">Primer sábado de cada mes, 16:00, salón parroquial.</p>
        <h3>Celebración</h3><p style="margin:0">Segundo domingo de cada mes, 11:00.</p>
        <p class="note" style="margin:0">Última actualización: ${S.content.date} · ${S.content.by}</p>
      </div></div>` : `<p style="margin:0;color:var(--muted)">La información de ${S.tab.toLowerCase()} se publicará en la siguiente versión del prototipo.</p>`;
  return `
  <div class="crumbs"><a href="#inicio">Inicio</a> / Sacramentos</div>
  <h1>Requisitos de los sacramentos</h1>
  <div class="card" style="display:grid;gap:16px"><div class="tabs" role="tablist">${tabs.map(t => `<button class="tab ${t === S.tab ? "on" : ""}" role="tab" data-tab="${t}">${t}</button>`).join("")}</div>${body}</div>`;
};

V.catequesis = () => `
  <div class="crumbs"><a href="#inicio">Inicio</a> / Catequesis</div>
  <h1>Convocatorias de catequesis</h1>
  <div class="card table-wrap"><table>
    <thead><tr><th>Convocatoria</th><th>Inscripción</th><th>Cierre</th><th>Estado</th></tr></thead>
    <tbody>
      <tr><td>Primera comunión 2026–2027</td><td>USD 5 + libro USD 5</td><td>30/11/2026</td><td><span class="pill ok">Abierta</span></td></tr>
      <tr><td>Confirmación 2026–2027</td><td>USD 5 + libro USD 5</td><td>15/12/2026</td><td><span class="pill ok">Abierta</span></td></tr>
      <tr><td>Catequesis familiar 2026</td><td>USD 5</td><td>31/08/2026</td><td><span class="pill err">Cerrada</span></td></tr>
    </tbody></table></div>
  <p class="note">La inscripción es presencial en secretaría. La camiseta se adquiere aparte (${money(PRECIO.base)} u ${money(PRECIO.grande)} según talla).</p>`;

V.ingresar = () => S.user ? V.panel() : `
  <div class="login">
    <div class="crumbs"><a href="#inicio">Inicio</a> / Ingreso secretaría / personal</div>
    <h1>Ingreso de secretaría y personal</h1>
    <p style="margin:0;color:var(--muted)">Para secretaría, párroco y administrador. Si eres visitante, no necesitas iniciar sesión.</p>
    <form class="card form" id="fLogin" novalidate>
      <div id="loginErr"></div>
      <label class="f" for="u">Usuario<input id="u" autocomplete="username"><span class="err-msg" id="eu"></span></label>
      <label class="f" for="p">Contraseña<input id="p" type="password" autocomplete="current-password"><span class="err-msg" id="ep"></span></label>
      <button class="btn primary">Ingresar</button>
    </form>
  </div>`;

V.panel = () => !S.user ? V.ingresar() : `
  <div class="staffbar"><div><span class="crumbs">Panel del personal</span><h1>Hola, Secretaría</h1></div><button class="btn ghost" id="logout">Cerrar sesión</button></div>
  ${PRODUCTS.some(p => stockOf(p) <= STOCK_BAJO || (p.sizes && Object.values(p.sizes).some(n => n <= STOCK_BAJO))) ? `<div class="alert warn">Hay artículos con pocas unidades o agotados. Revisa el inventario.</div>` : ""}
  <div class="panel-grid">
    <a class="card" href="#venta"><span class="pill info" style="justify-self:start">Ventas</span><h3>Registrar venta</h3><span style="color:var(--muted)">Descuenta el stock de la talla vendida y genera el recibo.</span></a>
    <a class="card" href="#inventario"><span class="pill info" style="justify-self:start">Inventario</span><h3>Inventario por talla</h3><span style="color:var(--muted)">Consulta existencias y registra entradas.</span></a>
    <a class="card" href="#contenidos"><span class="pill info" style="justify-self:start">Contenidos</span><h3>Editar requisitos</h3><span style="color:var(--muted)">Propone cambios que aprueba el párroco.</span></a>
    <a class="card" href="#reporte"><span class="pill info" style="justify-self:start">Reportes</span><h3>Reporte por período</h3><span style="color:var(--muted)">Movimientos para el archivo parroquial.</span></a>
  </div>`;

V.venta = () => {
  if (!S.user) return V.ingresar();
  const opts = PRODUCTS.map(p => `<option value="${p.id}">${esc(p.name)}</option>`).join("");
  return `
  <div class="crumbs"><a href="#panel">Panel</a> / Registrar venta</div>
  <h1>Registrar venta</h1>
  <section class="two">
    <form class="card form" id="fVenta" novalidate>
      <label class="f" for="vp">Artículo<select id="vp"><option value="">Selecciona un artículo</option>${opts}</select><span class="err-msg" id="evp"></span></label>
      <label class="f" for="vs" id="wrapSize" hidden>Talla<select id="vs"></select><span class="err-msg" id="evs"></span></label>
      <label class="f" for="vq">Cantidad<input id="vq" type="number" min="1" step="1" value="1" inputmode="numeric"><span class="err-msg" id="evq"></span></label>
      <button class="btn primary">Revisar y confirmar</button>
    </form>
    <div class="card sum" id="vSum"><h3>Resumen</h3><p style="margin:0;color:var(--muted)">Elige un artículo para ver el precio y el stock.</p></div>
  </section>`;
};

V["venta-ok"] = () => {
  const s = S.lastSale; if (!s) return V.venta();
  return `<div class="card done"><div class="ico">${ICON.check}</div><h2>Venta registrada</h2>
    <p style="margin:0">Recibo N.º <b>${String(s.receipt).padStart(DIGITOS_RECIBO, "0")}</b> · ${esc(s.name)}${s.size ? " talla " + s.size : ""} × ${s.qty} · <b>${money(s.total)}</b></p>
    <p class="note" style="margin:0">Stock actualizado: ${s.before} → ${s.after} unidades${s.size ? " de la talla " + s.size : ""}.</p>
    <div class="toolbar"><button class="btn primary" id="printRec">Imprimir recibo</button><a class="btn ghost" href="#venta">Registrar otra venta</a><a class="btn ghost" href="#inventario">Ver inventario</a></div></div>`;
};

V.inventario = () => {
  if (!S.user) return V.ingresar();
  const rows = PRODUCTS.flatMap(p => p.sizes ? Object.entries(p.sizes).map(([s, n]) => [p.name, "Talla " + s, n]) : [[p.name, "—", p.stock]])
    .map(([n, v, q]) => { const [k, t] = stateOf(q); return `<tr><td>${esc(n)}</td><td>${v}</td><td>${q}</td><td><span class="pill ${k}">${t}</span></td></tr>` }).join("");
  return `
  <div class="crumbs"><a href="#panel">Panel</a> / Inventario</div>
  <div class="staffbar"><h1>Inventario por talla</h1><a class="btn primary" href="#venta">Registrar venta</a></div>
  <div class="card table-wrap"><table><thead><tr><th>Artículo</th><th>Variante</th><th>Stock</th><th>Estado</th></tr></thead><tbody>${rows}</tbody></table></div>`;
};

V.contenidos = () => {
  if (!S.user) return V.ingresar();
  const st = S.content.status;
  return `
  <div class="crumbs"><a href="#panel">Panel</a> / Contenidos</div>
  <div class="staffbar"><h1>Editar requisitos de bautismo</h1><span class="pill ${st === "Publicado" ? "ok" : "warn"}">${st}</span></div>
  ${st === "Pendiente de aprobación" ? `
  <div class="card" style="display:grid;gap:12px">
    <div class="alert warn">El cambio espera la aprobación del párroco. Mientras tanto, la web sigue mostrando la versión publicada.</div>
    <h3>Vista del párroco</h3><pre style="white-space:pre-wrap;margin:0;font:inherit" class="note">${esc(S.content.draft)}</pre>
    <div class="toolbar"><button class="btn primary" id="approve">Aprobar y publicar</button><button class="btn ghost" id="reject">Devolver a secretaría</button></div>
  </div>` : `
  <form class="card form" id="fCont" novalidate>
    <label class="f" for="ct">Requisitos (uno por línea)<textarea id="ct" rows="7">${esc(S.content.text)}</textarea><span class="err-msg" id="ect"></span></label>
    <button class="btn primary">Enviar a aprobación del párroco</button>
    <p class="note" style="margin:0">Último cambio: ${S.content.date} · ${S.content.by}</p>
  </form>`}`;
};

V.publicado = () => `<div class="card done"><div class="ico">${ICON.check}</div><h2>Requisitos publicados</h2>
  <p style="margin:0">El párroco aprobó el cambio. Los visitantes ya ven la nueva versión.</p>
  <div class="toolbar"><a class="btn primary" href="#sacramentos">Ver como visitante</a><a class="btn ghost" href="#panel">Volver al panel</a></div></div>`;

V.reporte = () => {
  if (!S.user) return V.ingresar();
  return `
  <div class="crumbs"><a href="#panel">Panel</a> / Reporte</div>
  <h1>Reporte de movimientos por período</h1>
  <form class="card form" id="fRep" novalidate style="grid-template-columns:1fr 1fr auto;align-items:end">
    <label class="f" for="d1">Desde<input id="d1" type="date" value="2026-11-01"></label>
    <label class="f" for="d2">Hasta<input id="d2" type="date" value="2026-11-15"></label>
    <button class="btn primary">Generar</button>
    <span class="err-msg" id="erep" style="grid-column:1/-1"></span>
  </form>
  <div class="card table-wrap" id="repOut"><table><thead><tr><th>Fecha</th><th>Movimiento</th><th>Artículo</th><th>Cant.</th><th>Recibo</th><th>Importe</th></tr></thead><tbody>
    <tr><td>04/11/2026</td><td>Entrada</td><td>Camiseta talla 34</td><td>10</td><td>—</td><td>—</td></tr>
    <tr><td>08/11/2026</td><td>Venta</td><td>Libro de catequesis</td><td>2</td><td>000122</td><td>USD 10,00</td></tr>
    <tr><td>12/11/2026</td><td>Venta</td><td>Camiseta talla 38</td><td>1</td><td>000123</td><td>USD 11,00</td></tr>
  </tbody></table></div>`;
};

function render() {
  const r = (location.hash || "#inicio").slice(1);
  const view = V[r] ? r : "inicio";
  document.getElementById("app").innerHTML = `<div class="view">${V[view]()}</div>`;
  document.querySelectorAll("#nav a").forEach(a => a.classList.toggle("on", a.dataset.r === view || (a.dataset.r === "catalogo" && view === "articulo") || (a.dataset.r === "ingresar" && ["panel", "venta", "venta-ok", "inventario", "contenidos", "reporte", "publicado"].includes(view))));
  document.getElementById("staffLink").textContent = S.user ? "Panel del personal" : "Ingreso secretaría / personal";
  document.getElementById("staffLink").setAttribute("href", S.user ? "#panel" : "#ingresar");
  bind(view); window.scrollTo(0, 0);
}

function setErr(inp, msgEl, msg) {
  inp.classList.toggle("invalid", Boolean(msg));
  inp.setAttribute("aria-invalid", msg ? "true" : "false");
  document.getElementById(msgEl).textContent = msg || "";
}
const $ = id => document.getElementById(id);
const alHacerClic = (id, accion) => {
  const boton = $(id);
  if (boton) boton.onclick = accion;
};

function bindCatalogo() {
  $("fSearch").onsubmit = e => {
    e.preventDefault();
    S.query = $("q").value;
    render();
  };
  document.querySelectorAll("[data-cat]").forEach(b => {
    b.onclick = () => {
      S.cat = b.dataset.cat;
      render();
    };
  });
  $("avail").onchange = e => {
    S.onlyAvail = e.target.checked;
    render();
  };
  alHacerClic("clear", () => {
    S.query = "";
    S.cat = "Todos";
    S.onlyAvail = false;
    render();
  });
  document.querySelectorAll("[data-id]").forEach(a => {
    a.onclick = () => {
      S.sel = a.dataset.id;
      S.size = null;
    };
  });
}

function bindLogin() {
  $("fLogin").onsubmit = async e => {
    e.preventDefault();
    const usuario = $("u"), clave = $("p");
    setErr(usuario, "eu", usuario.value.trim() ? "" : "Escribe tu usuario.");
    setErr(clave, "ep", clave.value ? "" : "Escribe tu contraseña.");
    if (!usuario.value.trim() || !clave.value) return;
    // Corrección: el bloqueo ahora impide nuevos intentos durante el tiempo indicado
    if (Date.now() < S.lockedUntil) {
      mostrarAlerta($("loginErr"), "err", `Cuenta bloqueada temporalmente. Intenta de nuevo en ${BLOQUEO_MINUTOS} minutos.`);
      return;
    }
    const valido = usuario.value.trim() === USUARIO_PRUEBA && await sha256(clave.value) === HASH_CLAVE_PRUEBA;
    if (valido) {
      S.user = USUARIO_PRUEBA;
      S.loginTries = INTENTOS_MAX;
      toast("Sesión iniciada");
      go("panel");
      return;
    }
    S.loginTries -= 1;
    if (S.loginTries <= 0) {
      S.lockedUntil = Date.now() + BLOQUEO_MINUTOS * MS_POR_MINUTO;
      S.loginTries = INTENTOS_MAX;
      mostrarAlerta($("loginErr"), "err", `Usuario o contraseña incorrectos. Cuenta bloqueada por ${BLOQUEO_MINUTOS} minutos.`);
      return;
    }
    mostrarAlerta($("loginErr"), "err", `Usuario o contraseña incorrectos. Te quedan ${S.loginTries} intentos antes del bloqueo temporal.`);
  };
}

function llenarTallas(select, producto) {
  const vacia = new Option("Selecciona una talla", "");
  const opciones = Object.entries(producto.sizes).map(([talla, unidades]) => {
    const texto = `Talla ${talla} · ${unidades === 0 ? "agotada" : unidades + " u."}`;
    const opcion = new Option(texto, talla);
    opcion.disabled = unidades === 0;
    return opcion;
  });
  select.replaceChildren(vacia, ...opciones);
  select.dataset.for = producto.id;
}

function stockDe(producto, talla) {
  if (!producto.sizes) return producto.stock;
  return talla ? producto.sizes[talla] : null;
}

function resumenVenta(producto, talla, qty) {
  const stock = stockDe(producto, talla);
  const sinTalla = producto.sizes && !talla;
  const excede = stock !== null && qty > stock;
  const unit = priceFor(producto, talla);
  // Corrección: el total no se muestra si la cantidad no es válida o supera el stock
  const total = sinTalla || !qty || excede ? "—" : money(unit * qty);
  return `<h3>Resumen</h3>
    <div class="row"><span>Artículo</span><b>${esc(producto.name)}${talla ? " · talla " + esc(talla) : ""}</b></div>
    <div class="row"><span>Stock disponible</span><span>${stock === null ? "elige talla" : stock + " u."}</span></div>
    <div class="row"><span>Precio unitario</span><span>${sinTalla ? "—" : money(unit)}</span></div>
    <div class="row"><span>Cantidad</span><span>${qty || "—"}</span></div>
    <div class="row total"><span>Total</span><span>${total}</span></div>`;
}

function validarVenta(producto, talla, qty) {
  setErr($("vp"), "evp", producto ? "" : "Selecciona el artículo vendido.");
  if (!producto) return false;
  if (producto.sizes) setErr($("vs"), "evs", talla ? "" : "Selecciona la talla vendida.");
  if (producto.sizes && !talla) return false;
  const stock = stockDe(producto, talla);
  let msg = "";
  if (!qty) msg = "La cantidad debe ser un número entero mayor que 0.";
  else if (qty > stock) msg = `Solo hay ${stock} ${stock === 1 ? "unidad" : "unidades"}${talla ? " de la talla " + talla : ""}. Corrige la cantidad.`;
  setErr($("vq"), "evq", msg);
  return !msg;
}

function confirmarVenta(producto, talla, qty) {
  const capa = $("layer");
  const total = priceFor(producto, talla) * qty;
  capa.innerHTML = `<div class="modal-bg"><div class="modal" role="dialog" aria-modal="true" aria-labelledby="mt">
    <h2 id="mt">Confirmar venta</h2>
    <div class="sum"><div class="row"><span>${esc(producto.name)}${talla ? " · talla " + esc(talla) : ""}</span><span>× ${qty}</span></div><div class="row total"><span>Total</span><span>${money(total)}</span></div></div>
    <p class="note" style="margin:0">Al confirmar se descontará el stock y se generará el recibo.</p>
    <div class="toolbar"><button class="btn primary" id="ok">Confirmar venta</button><button class="btn ghost" id="cancel">Cancelar</button></div></div></div>`;
  alHacerClic("cancel", () => capa.replaceChildren());
  alHacerClic("ok", () => {
    // Corrección: se vuelve a leer el stock al confirmar para no usar un valor desactualizado
    const before = stockDe(producto, talla);
    capa.replaceChildren();
    if (qty > before) {
      setErr($("vq"), "evq", `El stock cambió: ahora hay ${before} unidades. Corrige la cantidad.`);
      return;
    }
    if (producto.sizes) producto.sizes[talla] -= qty;
    else producto.stock -= qty;
    S.receipt += 1;
    S.lastSale = { receipt: S.receipt, name: producto.name, size: talla, qty, total, before, after: before - qty };
    go("venta-ok");
  });
}

function bindVenta() {
  const vp = $("vp"), vs = $("vs"), vq = $("vq");
  const actual = () => PRODUCTS.find(x => x.id === vp.value);
  const actualizar = () => {
    const producto = actual();
    $("wrapSize").hidden = !(producto && producto.sizes);
    if (producto && producto.sizes && vs.dataset.for !== producto.id) llenarTallas(vs, producto);
    if (!producto) {
      $("vSum").innerHTML = `<h3>Resumen</h3><p style="margin:0;color:var(--muted)">Elige un artículo para ver el precio y el stock.</p>`;
      return;
    }
    $("vSum").innerHTML = resumenVenta(producto, producto.sizes ? vs.value : null, leerCantidad(vq.value));
  };
  vp.onchange = actualizar;
  vs.onchange = actualizar;
  vq.oninput = actualizar;
  actualizar();
  $("fVenta").onsubmit = e => {
    e.preventDefault();
    const producto = actual();
    const talla = producto && producto.sizes ? vs.value : null;
    const qty = leerCantidad(vq.value);
    if (validarVenta(producto, talla, qty)) confirmarVenta(producto, talla, qty);
  };
}

function bindContenidos() {
  $("fCont").onsubmit = e => {
    e.preventDefault();
    const campo = $("ct");
    const lines = campo.value.split("\n").filter(x => x.trim());
    setErr(campo, "ect", lines.length ? "" : "Escribe al menos un requisito antes de enviar.");
    if (!lines.length) return;
    S.content.draft = lines.join("\n");
    S.content.status = "Pendiente de aprobación";
    toast("Enviado al párroco para su aprobación");
    render();
  };
}

function bindAprobacion() {
  alHacerClic("approve", () => {
    S.content.text = S.content.draft;
    S.content.status = "Publicado";
    S.content.by = "Aprobado por el párroco";
    // Corrección: la fecha de aprobación es la del día, no un valor fijo
    S.content.date = new Date().toLocaleDateString("es-EC");
    go("publicado");
  });
  alHacerClic("reject", () => {
    S.content.status = "Publicado";
    toast("Cambio devuelto a secretaría");
    render();
  });
}

function mensajeRango(desde, hasta) {
  if (!desde || !hasta) return "Elige las dos fechas del período.";
  // Las fechas vienen en formato ISO (AAAA-MM-DD), por eso la comparación de texto es válida
  if (desde > hasta) return "La fecha “Desde” no puede ser posterior a “Hasta”.";
  return "";
}

function bindReporte() {
  $("fRep").onsubmit = e => {
    e.preventDefault();
    const msg = mensajeRango($("d1").value, $("d2").value);
    setErr($("d2"), "erep", msg);
    if (!msg) toast("Reporte generado para el período elegido");
  };
}

function bind(view) {
  if (view === "catalogo") bindCatalogo();
  if ($("fLogin")) bindLogin();
  if (view === "venta" && $("fVenta")) bindVenta();
  if ($("fCont")) bindContenidos();
  if ($("approve")) bindAprobacion();
  if ($("fRep")) bindReporte();
  if (view === "articulo") {
    document.querySelectorAll("[data-size]").forEach(b => {
      b.onclick = () => {
        S.size = b.dataset.size;
        render();
      };
    });
  }
  if (view === "sacramentos") {
    document.querySelectorAll("[data-tab]").forEach(b => {
      b.onclick = () => {
        S.tab = b.dataset.tab;
        render();
      };
    });
  }
  alHacerClic("printRec", () => toast("Recibo enviado a la impresora de secretaría (simulado)"));
  alHacerClic("logout", () => {
    S.user = null;
    toast("Sesión cerrada");
    go("inicio");
  });
}
window.addEventListener("hashchange", render);
render();
})();
