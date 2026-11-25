# Análisis estático – Web Parroquial (Grupo 5)

Módulo evaluado: `src/app.js` (lógica del prototipo: catálogo, ingreso del personal, ventas por talla, contenidos y reportes).

- Herramienta: ESLint 10 con `@eslint/js` (recomendado), `eslint-plugin-sonarjs` y `eslint-plugin-no-unsanitized`. Configuración en `eslint.config.mjs`.
- Resultados: `resultados/eslint_antes.txt` (commit original) y `resultados/eslint_despues.txt` (después de las correcciones).
- Comprobación en navegador: `pruebas/comprobar.py`.

## Ejecutar el análisis

```
npm install
npx eslint src
```

Commits: el primero contiene el código original; el segundo, las correcciones.
