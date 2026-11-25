# Compara cuántos avisos dio cada regla de ESLint antes y después de las correcciones
import json, collections, pathlib
aqui = pathlib.Path(__file__).parent
leer = lambda n: collections.Counter(m["ruleId"] for m in json.load(open(aqui / n, encoding="utf-8"))[0]["messages"])
antes, despues = leer("eslint_antes.json"), leer("eslint_despues.json")
for regla in sorted(set(antes) | set(despues), key=lambda r: -antes[r]):
    print(f"{regla:34s} antes={antes[regla]:3d}  despues={despues[regla]:3d}")
print(f"{'TOTAL':34s} antes={sum(antes.values()):3d}  despues={sum(despues.values()):3d}")
