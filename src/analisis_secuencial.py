"""
analisis_secuencial.py
Análisis secuencial con Pandas — línea base para comparar con Ray.
Retorna un diccionario de DataFrames con todos los indicadores.
"""
import pandas as pd
import time
import os


def analizar(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """
    Ejecuta todos los análisis de forma secuencial (Pandas puro).
    Devuelve un dict con los resultados.
    """
    resultados = {}
    t_total = time.time()

    # ── 1. Resumen general ────────────────────────────────────────────────────
    t = time.time()
    resumen = pd.DataFrame([{
        "total_accidentes": len(df),
        "con_heridos":      df["con_heridos"].sum(),
        "con_fallecidos":   df["con_fallecidos"].sum(),
        "total_heridos":    df["heridos"].sum(),
        "total_fallecidos": df["fallecidos"].sum(),
        "anio_min":         df["anio"].min(),
        "anio_max":         df["anio"].max(),
    }])
    resultados["resumen_general"] = resumen
    print(f"  [seq] Resumen general        {time.time()-t:.3f}s")

    # ── 2. Por entidad federativa ─────────────────────────────────────────────
    t = time.time()
    por_estado = (
        df.groupby("entidad_nombre", as_index=False)
          .agg(
              accidentes  =("id_accidente", "count"),
              heridos     =("heridos",      "sum"),
              fallecidos  =("fallecidos",   "sum"),
          )
          .sort_values("accidentes", ascending=False)
          .reset_index(drop=True)
    )
    resultados["por_estado"] = por_estado
    print(f"  [seq] Por estado             {time.time()-t:.3f}s")

    # ── 3. Por municipio ──────────────────────────────────────────────────────
    t = time.time()
    por_municipio = (
        df.groupby(["entidad_nombre", "municipio"], as_index=False)
          .agg(accidentes=("id_accidente", "count"),
               heridos   =("heridos",      "sum"),
               fallecidos=("fallecidos",   "sum"))
          .sort_values("accidentes", ascending=False)
          .head(50)
          .reset_index(drop=True)
    )
    resultados["por_municipio"] = por_municipio
    print(f"  [seq] Por municipio (top 50) {time.time()-t:.3f}s")

    # ── 4. Por hora ───────────────────────────────────────────────────────────
    t = time.time()
    por_hora = (
        df.groupby("hora", as_index=False)
          .agg(accidentes=("id_accidente", "count"),
               heridos   =("heridos",      "sum"),
               fallecidos=("fallecidos",   "sum"))
          .sort_values("hora")
    )
    resultados["por_hora"] = por_hora
    print(f"  [seq] Por hora               {time.time()-t:.3f}s")

    # ── 5. Por causa ──────────────────────────────────────────────────────────
    t = time.time()
    por_causa = (
        df.groupby("causa", as_index=False)
          .agg(accidentes=("id_accidente", "count"),
               heridos   =("heridos",      "sum"),
               fallecidos=("fallecidos",   "sum"))
          .sort_values("accidentes", ascending=False)
    )
    resultados["por_causa"] = por_causa
    print(f"  [seq] Por causa              {time.time()-t:.3f}s")

    # ── 6. Por mes ────────────────────────────────────────────────────────────
    t = time.time()
    por_mes = (
        df.groupby("mes", as_index=False)
          .agg(accidentes=("id_accidente", "count"),
               heridos   =("heridos",      "sum"),
               fallecidos=("fallecidos",   "sum"))
          .sort_values("mes")
    )
    resultados["por_mes"] = por_mes
    print(f"  [seq] Por mes                {time.time()-t:.3f}s")

    # ── 7. Por tipo de accidente ──────────────────────────────────────────────
    t = time.time()
    por_tipo = (
        df.groupby("tipo_accidente", as_index=False)
          .agg(accidentes=("id_accidente", "count"),
               heridos   =("heridos",      "sum"),
               fallecidos=("fallecidos",   "sum"))
          .sort_values("accidentes", ascending=False)
    )
    resultados["por_tipo"] = por_tipo
    print(f"  [seq] Por tipo               {time.time()-t:.3f}s")

    # ── 8. Tendencia anual ────────────────────────────────────────────────────
    t = time.time()
    tendencia_anual = (
        df.groupby("anio", as_index=False)
          .agg(accidentes=("id_accidente", "count"),
               heridos   =("heridos",      "sum"),
               fallecidos=("fallecidos",   "sum"))
          .sort_values("anio")
    )
    resultados["tendencia_anual"] = tendencia_anual
    print(f"  [seq] Tendencia anual        {time.time()-t:.3f}s")

    # ── 9. Índice de gravedad por estado ──────────────────────────────────────
    t = time.time()
    gravedad = por_estado.copy()
    gravedad["indice_gravedad"] = (
        (gravedad["heridos"] + gravedad["fallecidos"] * 3)
        / gravedad["accidentes"].clip(lower=1)
    ).round(4)
    gravedad = gravedad.sort_values("indice_gravedad", ascending=False)
    resultados["gravedad_por_estado"] = gravedad
    print(f"  [seq] Índice de gravedad     {time.time()-t:.3f}s")

    tiempo_total = time.time() - t_total
    print(f"  [seq] TOTAL                  {tiempo_total:.3f}s")
    return resultados, tiempo_total


def guardar_resultados(resultados: dict, carpeta: str = "outputs/secuencial"):
    os.makedirs(carpeta, exist_ok=True)
    for nombre, df in resultados.items():
        ruta = f"{carpeta}/{nombre}.csv"
        df.to_csv(ruta, index=False)
    print(f"  Resultados guardados en {carpeta}/")


if __name__ == "__main__":
    import sys
    ruta = sys.argv[1] if len(sys.argv) > 1 else "data/accidentes_limpio.parquet"
    df   = pd.read_parquet(ruta)
    print(f"\n── Análisis SECUENCIAL ({len(df):,} registros) ──")
    res, t = analizar(df)
    guardar_resultados(res)
