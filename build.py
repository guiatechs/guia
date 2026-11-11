#!/usr/bin/env python3
"""Generador del sitio: lee datos.csv y crea una página por fila en dist/.
Solo usa la librería estándar de Python (3.8+). Uso: python build.py
"""
import csv
import html
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from string import Template

# ----------------------------------------------------------------------------
# CONFIGURACIÓN (cambiá esto o definí variables de entorno)
# ----------------------------------------------------------------------------
SITE_NAME = os.environ.get("SITE_NAME") or "GuíaTech"
SITE_URL = (os.environ.get("SITE_URL") or "https://tu-sitio.pages.dev").rstrip("/")
# Vacío si usás dominio propio o Cloudflare Pages. "/nombre-repo" si usás
# GitHub Pages sin dominio propio (https://usuario.github.io/nombre-repo).
BASE_PATH = (os.environ.get("BASE_PATH") or "").rstrip("/")
# Cuando te aprueben AdSense: "ca-pub-XXXXXXXXXXXXXXXX". Vacío = sin anuncios.
ADSENSE_CLIENT = os.environ.get("ADSENSE_CLIENT") or ""
# Cuadro de afiliados por tipo: (texto, enlace). Con enlace vacío no se muestra.
AFILIADOS = {
    "error": ("", ""),    # ej: ("Recuperá archivos perdidos con este programa", "https://...")
    "comando": ("", ""),
    "atajo": ("", ""),
}

TIPOS = {
    "error": dict(carpeta="errores", plural="Errores de Windows",
                  h_causas="Posibles causas", h_pasos="Cómo solucionarlo", ordenada=True),
    "comando": dict(carpeta="comandos", plural="Comandos de cmd",
                    h_causas="Para qué sirve", h_pasos="Opciones y ejemplos", ordenada=False),
    "atajo": dict(carpeta="atajos", plural="Atajos de teclado",
                  h_causas="Qué hace", h_pasos="Variantes y consejos", ordenada=False),
}

CAMPOS = ["slug", "tipo", "grupo", "nombre", "titulo", "resumen", "causas", "pasos", "relacionados"]
SEP = "||"
DIST = Path("dist")

CSS = """
:root{--bg:#f6f7f9;--panel:#fff;--ink:#16212c;--soft:#4c5a68;--line:#d9dee4;--accent:#0a58d6;--code:#e9eef5}
@media (prefers-color-scheme:dark){:root{--bg:#10161d;--panel:#18212b;--ink:#e8edf2;--soft:#9fb0c0;--line:#2b3947;--accent:#6ea8ff;--code:#223142}}
*{box-sizing:border-box}
html{font-size:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:1.0625rem/1.65 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:46rem;margin:0 auto;padding:0 1.1rem}
.top{background:var(--panel);border-bottom:1px solid var(--line)}
.top .wrap{display:flex;gap:1rem;align-items:center;justify-content:space-between;flex-wrap:wrap;padding-top:.7rem;padding-bottom:.7rem}
.brand{font-weight:700;font-size:1.15rem;color:var(--ink);text-decoration:none}
nav a{margin-left:1rem;color:var(--soft);text-decoration:none}
nav a:hover,nav a:focus-visible{color:var(--accent);text-decoration:underline}
a{color:var(--accent)}
a:focus-visible,input:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
h1{font-size:1.9rem;line-height:1.25;margin:1.8rem 0 .8rem}
h2{font-size:1.3rem;margin:2rem 0 .6rem}
h3{font-size:1.05rem;margin:1.4rem 0 .3rem;color:var(--soft)}
.resumen{font-size:1.15rem;color:var(--soft);margin:0 0 1rem}
code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.92em;background:var(--code);padding:.1em .38em;border-radius:4px}
li{margin:.45rem 0}
.crumbs{font-size:.92rem;color:var(--soft);margin-top:1.2rem}
.crumbs a{color:var(--soft)}
.aviso{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--accent);padding:.8rem 1rem;margin:1.8rem 0;border-radius:4px}
.rel ul{padding-left:1.2rem}
.buscar{width:100%;font:inherit;padding:.75rem .9rem;border:1px solid var(--line);border-radius:6px;background:var(--panel);color:var(--ink);margin:.5rem 0 1rem}
.lista{list-style:none;padding:0;margin:0}
.lista li{margin:0;border-bottom:1px solid var(--line)}
.lista a{display:block;padding:.65rem .1rem;text-decoration:none;color:var(--ink)}
.lista a:hover,.lista a:focus-visible{color:var(--accent)}
.lista small{display:block;color:var(--soft);font-size:.9rem}
[hidden]{display:none!important}
.foot{color:var(--soft);font-size:.9rem;padding-top:2rem;padding-bottom:2.5rem}
"""

LAYOUT = Template("""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title</title>
<meta name="description" content="$desc">
<link rel="canonical" href="$canonical">
<meta property="og:title" content="$title">
<meta property="og:description" content="$desc">
<meta property="og:type" content="website">
<meta property="og:url" content="$canonical">
<style>$css</style>
$ads
</head>
<body>
<header class="top"><div class="wrap"><a class="brand" href="$base/">$site</a><nav>$nav</nav></div></header>
<main class="wrap">
$body
</main>
<footer class="wrap foot">
<p>$site reúne soluciones y referencias rápidas de informática. Revisá siempre la documentación oficial antes de modificar tu sistema y hacé copia de seguridad de tus datos importantes.</p>
<p>Última actualización del sitio: $fecha</p>
</footer>
</body>
</html>
""")


def esc(texto):
    """Escapa HTML y convierte `código` en <code>."""
    texto = html.escape(texto, quote=False)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", texto)


def attr(texto):
    return html.escape(re.sub(r"`", "", texto), quote=True)


def url(tipo, slug=None):
    carpeta = TIPOS[tipo]["carpeta"]
    return f"{BASE_PATH}/{carpeta}/" + (f"{slug}/" if slug else "")


def cargar():
    with open("datos.csv", newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    errores, vistos = [], set()
    for n, fila in enumerate(filas, start=2):
        for campo in CAMPOS:
            if campo not in fila or fila[campo] is None:
                errores.append(f"Línea {n}: falta la columna «{campo}»")
        if errores:
            continue
        fila = {k: (v or "").strip() for k, v in fila.items()}
        if fila["tipo"] not in TIPOS:
            errores.append(f"Línea {n}: tipo desconocido «{fila['tipo']}»")
        if not re.fullmatch(r"[a-z0-9-]+", fila["slug"]):
            errores.append(f"Línea {n}: slug inválido «{fila['slug']}» (solo a-z, 0-9 y guiones)")
        if fila["slug"] in vistos:
            errores.append(f"Línea {n}: slug repetido «{fila['slug']}»")
        vistos.add(fila["slug"])
        for campo in ("nombre", "titulo", "resumen", "causas", "pasos"):
            if not fila[campo]:
                errores.append(f"Línea {n} ({fila['slug']}): «{campo}» vacío")
        filas[n - 2] = fila
    por_slug = {f["slug"]: f for f in filas if isinstance(f, dict) and "slug" in f}
    for f in por_slug.values():
        for r in [x for x in f["relacionados"].split(";") if x.strip()]:
            if r.strip() not in por_slug:
                errores.append(f"{f['slug']}: relacionado inexistente «{r.strip()}»")
    if errores:
        print("\n".join(errores))
        sys.exit(1)
    return filas, por_slug


def lista_items(items, ordenada):
    tag = "ol" if ordenada else "ul"
    lis = "".join(f"<li>{esc(i.strip())}</li>" for i in items.split(SEP) if i.strip())
    return f"<{tag}>{lis}</{tag}>"


def nav_html():
    return "".join(f'<a href="{url(t)}">{d["plural"]}</a>' for t, d in TIPOS.items())


def ads_head():
    if not ADSENSE_CLIENT:
        return ""
    return ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
            f'?client={attr(ADSENSE_CLIENT)}" crossorigin="anonymous"></script>')


def pagina(titulo, desc, ruta, body):
    return LAYOUT.substitute(
        title=attr(titulo), desc=attr(desc), canonical=SITE_URL + ruta, css=CSS,
        ads=ads_head(), base=BASE_PATH, site=esc(SITE_NAME), nav=nav_html(),
        body=body, fecha=date.today().strftime("%d/%m/%Y"))


def escribir(ruta, contenido):
    # ruta empieza con BASE_PATH; en disco va relativa a dist/
    rel = ruta[len(BASE_PATH):].lstrip("/")
    destino = DIST / rel / "index.html" if rel else DIST / "index.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(contenido, encoding="utf-8")


def listado(filas, tipo, con_titulo_tipo=True):
    d = TIPOS[tipo]
    propias = [f for f in filas if f["tipo"] == tipo]
    grupos = {}
    for f in propias:
        grupos.setdefault(f["grupo"] or "General", []).append(f)
    out = [f'<section><h2>{d["plural"]}</h2>' if con_titulo_tipo else "<section>"]
    for grupo, items in grupos.items():
        out.append(f"<h3>{esc(grupo)}</h3><ul class=\"lista\">")
        for f in sorted(items, key=lambda x: x["nombre"].lower()):
            buscable = attr(f"{f['nombre']} {f['titulo']} {f['resumen']}".lower())
            out.append(f'<li data-s="{buscable}"><a href="{url(tipo, f["slug"])}">'
                       f'{esc(f["nombre"])}<small>{esc(f["resumen"])}</small></a></li>')
        out.append("</ul>")
    out.append("</section>")
    return "\n".join(out)


BUSCADOR_JS = """<script>
(function(){
var q=document.getElementById('q');if(!q)return;
var items=document.querySelectorAll('li[data-s]'),secs=document.querySelectorAll('main section');
q.addEventListener('input',function(){
var t=q.value.toLowerCase().trim();
items.forEach(function(li){li.hidden=!!t&&li.dataset.s.indexOf(t)===-1;});
secs.forEach(function(s){var v=s.querySelectorAll('li[data-s]:not([hidden])').length;s.hidden=!v;});
});})();
</script>"""

BUSCADOR = ('<label for="q" class="resumen">Buscá un código de error, un comando o un atajo</label>'
            '<input id="q" class="buscar" type="search" placeholder="Por ejemplo: 0x80070057, ipconfig, Win + V" autocomplete="off">')


def pagina_detalle(f, por_slug):
    d = TIPOS[f["tipo"]]
    ruta = url(f["tipo"], f["slug"])
    partes = [
        f'<p class="crumbs"><a href="{BASE_PATH}/">Inicio</a> / <a href="{url(f["tipo"])}">{d["plural"]}</a></p>',
        f'<h1>{esc(f["titulo"])}</h1>',
        f'<p class="resumen">{esc(f["resumen"])}</p>',
        f'<h2>{d["h_causas"]}</h2>{lista_items(f["causas"], False)}',
        f'<h2>{d["h_pasos"]}</h2>{lista_items(f["pasos"], d["ordenada"])}',
    ]
    texto, enlace = AFILIADOS.get(f["tipo"], ("", ""))
    if enlace:
        partes.append(f'<div class="aviso"><a href="{attr(enlace)}" rel="sponsored noopener">{esc(texto)}</a>'
                      '<br><small>Enlace de afiliado: puede darnos una comisión sin costo extra para vos.</small></div>')
    rel = [r.strip() for r in f["relacionados"].split(";") if r.strip()]
    if rel:
        lis = "".join(f'<li><a href="{url(por_slug[r]["tipo"], r)}">{esc(por_slug[r]["nombre"])}</a>: '
                      f'{esc(por_slug[r]["titulo"])}</li>' for r in rel)
        partes.append(f'<section class="rel"><h2>Temas relacionados</h2><ul>{lis}</ul></section>')
    return pagina(f"{f['titulo']} | {SITE_NAME}", f["resumen"], ruta, "\n".join(partes))


def main():
    filas, por_slug = cargar()
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()

    # Inicio
    cuerpo = (f"<h1>{esc(SITE_NAME)}: errores, comandos y atajos de informática</h1>"
              '<p class="resumen">Respuestas cortas y ordenadas para problemas de Windows, comandos de cmd y atajos de teclado.</p>'
              + BUSCADOR + "\n".join(listado(filas, t) for t in TIPOS) + BUSCADOR_JS)
    escribir(BASE_PATH + "/", pagina(f"{SITE_NAME}: errores, comandos y atajos de informática",
             "Soluciones a errores de Windows, comandos de cmd y atajos de teclado explicados de forma simple.",
             BASE_PATH + "/", cuerpo))

    # Listados por tipo
    for t, d in TIPOS.items():
        cuerpo = (f'<p class="crumbs"><a href="{BASE_PATH}/">Inicio</a></p><h1>{d["plural"]}</h1>'
                  + BUSCADOR + listado(filas, t, con_titulo_tipo=False) + BUSCADOR_JS)
        escribir(url(t), pagina(f"{d['plural']} | {SITE_NAME}",
                 f"Lista de {d['plural'].lower()} con explicación y solución.", url(t), cuerpo))

    # Páginas de detalle
    for f in filas:
        escribir(url(f["tipo"], f["slug"]), pagina_detalle(f, por_slug))

    # 404, sitemap, robots
    (DIST / "404.html").write_text(pagina(f"Página no encontrada | {SITE_NAME}", "Página no encontrada.", BASE_PATH + "/404.html",
        f'<h1>No encontramos esa página</h1><p class="resumen">Probá buscándola desde el <a href="{BASE_PATH}/">inicio</a>.</p>'),
        encoding="utf-8")
    rutas = [BASE_PATH + "/"] + [url(t) for t in TIPOS] + [url(f["tipo"], f["slug"]) for f in filas]
    hoy = date.today().isoformat()
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + "".join(f"<url><loc>{SITE_URL}{r}</loc><lastmod>{hoy}</lastmod></url>\n" for r in rutas) + "</urlset>\n")
    (DIST / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}{BASE_PATH}/sitemap.xml\n", encoding="utf-8")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")

    print(f"Listo: {len(filas)} páginas de contenido, {len(rutas) + 1} archivos HTML en dist/")


if __name__ == "__main__":
    main()
