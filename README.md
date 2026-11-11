# Sitio de informática generado por script

Una fila de `datos.csv` = una página. `build.py` genera todo en `dist/` (páginas, buscador, sitemap, robots.txt, 404).
Solo usa Python 3.8+ sin instalar nada.

## Probarlo en tu PC
    python build.py
Abrí `dist/index.html` en el navegador.

## Publicarlo gratis y automático (GitHub Pages)
1. Creá un repositorio en GitHub y subí todo este contenido (incluida la carpeta `.github`).
2. En el repo: Settings, Pages, Source: **GitHub Actions**.
3. En Settings, Secrets and variables, Actions, pestaña **Variables**, creá:
   - `SITE_URL`: la dirección final (ej. `https://usuario.github.io` o tu dominio).
   - `BASE_PATH`: `/nombre-del-repo` si no usás dominio propio; vacío si tenés dominio propio.
   - `SITE_NAME`: el nombre del sitio (opcional).
   - `ADSENSE_CLIENT`: tu ID `ca-pub-...` cuando te aprueben (opcional).
4. Cada vez que hagas push a `main`, el sitio se regenera y se publica solo.

Alternativa: Cloudflare Pages, con comando de build `python build.py` y carpeta de salida `dist`.

## Agregar páginas
Sumá filas a `datos.csv` (todas las columnas entre comillas, sin comillas dobles dentro del texto).
- `tipo`: `error`, `comando` o `atajo`.
- `slug`: minúsculas, números y guiones; no puede repetirse.
- `causas`, `pasos`: ítems separados por `||`. Usá `` `así` `` para marcar código.
- `relacionados`: slugs separados por `;`.
El generador avisa si algo está mal (slug repetido, relacionado inexistente, campo vacío).

## Antes de publicar
- Verificá cada dato contra documentación oficial (Microsoft, Blender).
- Agregá tus enlaces de afiliado en `AFILIADOS` dentro de `build.py`.
- Páginas de Privacidad y Contacto: AdSense las pide para aprobar el sitio.
