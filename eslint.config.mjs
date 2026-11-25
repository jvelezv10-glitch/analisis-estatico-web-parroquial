// Configuración de ESLint para el módulo de la Web Parroquial (Grupo 5)
import js from "@eslint/js";
import globals from "globals";
import sonarjs from "eslint-plugin-sonarjs";
import nounsanitized from "eslint-plugin-no-unsanitized";

export default [
  js.configs.recommended,               // defectos potenciales (variables no usadas, errores lógicos)
  sonarjs.configs.recommended,          // mantenibilidad: complejidad, duplicación, código confuso
  nounsanitized.configs.recommended,    // seguridad: HTML insertado sin sanear (innerHTML)
  {
    files: ["src/**/*.js"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "script",
      globals: { ...globals.browser }
    },
    rules: {
      // Estilo y legibilidad
      "max-statements-per-line": ["warn", { max: 1 }],
      "max-len": ["warn", { code: 140, ignoreTemplateLiterals: true, ignoreStrings: true }],
      "id-length": ["warn", { min: 2, exceptions: ["$", "_", "e", "i"] }],
      // Mantenibilidad
      "max-lines-per-function": ["warn", { max: 50, skipBlankLines: true }],
      "complexity": ["warn", 10],
      "no-magic-numbers": ["warn", { ignore: [0, 1, -1, 2, 10, 100], ignoreArrayIndexes: true, enforceConst: true }],
      // Defectos potenciales
      "eqeqeq": "error",
      "no-implicit-globals": "error",
      "no-return-assign": "error"
    }
  }
];
