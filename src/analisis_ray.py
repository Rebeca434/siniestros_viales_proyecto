"""
analisis_ray.py
Análisis distribuido con Ray — versión paralela y distribuida.

Modos de ejecución:
  • ray.init()                → local paralelo (80 %)
  • ray.init("ray://head:10001") → Ray Cluster (100 %)

El script detecta automáticamente si ya hay un cluster activo.
"""
import ray
import pandas as pd
import numpy as np
import time
import os
import sys


# ══════════════════════════════════════════════════════════════════════════════
# TAREAS RAY (Remote Functions)
# Cada función es una tarea independiente que Ray puede ejecutar en paralelo
# o en nodos distintos del cluster.
# ══════════════════════════════════════════════════════════════════════════════

@ray.remote
def tarea_resumen_general(df_ref):
    """Calcula métricas globales."""
    df = ray.get(df_ref) if not isinstance(df_ref, pd.DataFrame) else df_ref
    return pd.DataFrame([{
        "total_accidentes": len(df),
        "con_heridos":      int(df["con_heridos"].sum()),
        "con_fallecidos":   int(df["con_fallecidos"].sum()),
        "total_heridos":    int(df["heridos"].sum()),
        "total_fallecidos": int(df["fallecidos"].sum()),
        "anio_min":         int(df["anio"].min()),
        "anio_max":         int(df["anio"].max()),
    }])


@ray.remote
def tarea_por_estado(particion: pd.DataFrame) -> pd.DataFrame:
    """Agrega accidentes por entidad federativa en una partición."""
    return (
        particion.groupby("entidad_nombre", as_index=False)
                 .agg(accidentes  =("id_accidente", "count"),
                      heridos     =("heridos",      "sum"),
                      fallecidos  =("fallecidos",   "sum"))
    )


@ray.remote
def tarea_por_municipio(particion: pd.DataFrame) -> pd.DataFrame:
    return (
        particion.groupby(["entidad_nombre", "municipio"], as_index=False)
                 .agg(accidentes=("id_accidente", "count"),
                      heridos   =("heridos",      "sum"),
                      fallecidos=("fallecidos",   "sum"))
    )


@ray.remote
def tarea_por_hora(particion: pd.DataFrame) -> pd.DataFrame:
    return (
        particion.groupby("hora", as_index=False)
                 .agg(accidentes=("id_accidente", "count"),
                      heridos   =("heridos",      "sum"),
                      fallecidos=("fallecidos",   "sum"))
    )


@ray.remote
def tarea_por_causa(particion: pd.DataFrame) -> pd.DataFrame:
    return (
        particion.groupby("causa", as_index=False)
                 .agg(accidentes=("id_accidente", "count"),
                      heridos   =("heridos",      "sum"),
                      fallecidos=("fallecidos",   "sum"))
    )


@ray.remote
def tarea_por_mes(particion: pd.DataFrame) -> pd.DataFrame:
    return (
        particion.groupby("mes", as_index=False)
                 .agg(accidentes=("id_accidente", "count"),
                      heridos   =("heridos",      "sum"),
                      fallecidos=("fallecidos",   "sum"))
    )


@ray.remote
def tarea_por_tipo(particion: pd.DataFrame) -> pd.DataFrame:
    return (
        particion.groupby("tipo_accidente", as_index=False)
                 .agg(accidentes=("id_accidente", "count"),
                      heridos   =("heridos",      "sum"),
                      fallecidos=("fallecidos",   "sum"))
    )


@ray.remote
def tarea_por_anio(particion: pd.DataFrame) -> pd.DataFrame:
    return (
        particion.groupby("anio", as_index=False)
                 .agg(accidentes=("id_accidente", "count"),
                      heridos   =("heridos",      "sum"),
                      fallecidos=("fallecidos",   "sum"))
    )


@ray.remote
def reducir(parciales: list[pd.DataFrame], group_cols, sort_col="accidentes") -> pd.DataFrame:
    """Combina resultados parciales de distintas particiones."""
    combinado = pd.concat(parciales, ignore_index=True)
    return (
        combinado.groupby(group_cols, as_index=False)
                 .sum(numeric_only=True)
                 .sort_values(sort_col, ascending=(sort_col != "accidentes"))
                 .reset_index(drop=True)
    )


# ══════════════════════════════════════════════════════════════════════════════
# ORQUESTADOR PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def particionar(df: pd.DataFrame, n_particiones: int) -> list[pd.DataFrame]:
    """Divide el DataFrame en bloques de tamaño similar."""
    return np.array_split(df, n_particiones)


def analizar_ray(df: pd.DataFrame,
                 n_particiones: int = None,
                 address: str = None) -> tuple[dict, float]:
    """
    Ejecuta el análisis completo con Ray.

    Args:
        df:             DataFrame limpio
        n_particiones:  Número de particiones (default = CPUs disponibles)
        address:        "ray://head:10001" para cluster; None para local
    """
    # ── Inicializar Ray ──────────────────────────────────────────────────────
    if not ray.is_initialized():
        if address:
            ray.init(address=address, ignore_reinit_error=True)
            print(f"  Ray Cluster conectado: {address}")
        else:
            ray.init(ignore_reinit_error=True)
            print("  Ray local inicializado")

    n_cpus = int(ray.available_resources().get("CPU", 4))
    n_particiones = n_particiones or n_cpus
    print(f"  CPUs disponibles: {n_cpus}  |  Particiones: {n_particiones}")

    t_total = time.time()

    # ── Poner el dataset completo en el Object Store de Ray ──────────────────
    df_ref = ray.put(df)

    # ── Crear particiones ────────────────────────────────────────────────────
    particiones = particionar(df, n_particiones)
    refs_particiones = [ray.put(p) for p in particiones]

    # ══ FASE 1 — lanzar TODAS las tareas en paralelo ═════════════════════════
    t1 = time.time()

    fut_resumen   = tarea_resumen_general.remote(df_ref)

    futs_estado    = [tarea_por_estado.remote(r)    for r in refs_particiones]
    futs_municipio = [tarea_por_municipio.remote(r) for r in refs_particiones]
    futs_hora      = [tarea_por_hora.remote(r)      for r in refs_particiones]
    futs_causa     = [tarea_por_causa.remote(r)     for r in refs_particiones]
    futs_mes       = [tarea_por_mes.remote(r)       for r in refs_particiones]
    futs_tipo      = [tarea_por_tipo.remote(r)      for r in refs_particiones]
    futs_anio      = [tarea_por_anio.remote(r)      for r in refs_particiones]

    print(f"  Tareas lanzadas en {time.time()-t1:.3f}s")

    # ══ FASE 2 — reducción (combinar parciales) ═══════════════════════════════
    fut_estado    = reducir.remote(ray.get(futs_estado),    "entidad_nombre")
    fut_municipio = reducir.remote(ray.get(futs_municipio), ["entidad_nombre", "municipio"])
    fut_hora      = reducir.remote(ray.get(futs_hora),      "hora", sort_col="hora")
    fut_causa     = reducir.remote(ray.get(futs_causa),     "causa")
    fut_mes       = reducir.remote(ray.get(futs_mes),       "mes", sort_col="mes")
    fut_tipo      = reducir.remote(ray.get(futs_tipo),      "tipo_accidente")
    fut_anio      = reducir.remote(ray.get(futs_anio),      "anio", sort_col="anio")

    # ══ FASE 3 — recolectar ═══════════════════════════════════════════════════
    resumen        = ray.get(fut_resumen)
    por_estado     = ray.get(fut_estado)
    por_municipio  = ray.get(fut_municipio).head(50)
    por_hora       = ray.get(fut_hora)
    por_causa      = ray.get(fut_causa)
    por_mes        = ray.get(fut_mes)
    por_tipo       = ray.get(fut_tipo)
    tendencia_anual = ray.get(fut_anio)

    # Índice de gravedad
    gravedad = por_estado.copy()
    gravedad["indice_gravedad"] = (
        (gravedad["heridos"] + gravedad["fallecidos"] * 3)
        / gravedad["accidentes"].clip(lower=1)
    ).round(4)
    gravedad = gravedad.sort_values("indice_gravedad", ascending=False)

    tiempo_total = time.time() - t_total
    print(f"  [ray] TOTAL                  {tiempo_total:.3f}s")

    resultados = {
        "resumen_general":    resumen,
        "por_estado":         por_estado,
        "por_municipio":      por_municipio,
        "por_hora":           por_hora,
        "por_causa":          por_causa,
        "por_mes":            por_mes,
        "por_tipo":           por_tipo,
        "tendencia_anual":    tendencia_anual,
        "gravedad_por_estado": gravedad,
    }
    return resultados, tiempo_total


def guardar_resultados(resultados: dict, carpeta: str = "outputs/ray"):
    os.makedirs(carpeta, exist_ok=True)
    for nombre, df in resultados.items():
        df.to_csv(f"{carpeta}/{nombre}.csv", index=False)
    print(f"  Resultados guardados en {carpeta}/")


if __name__ == "__main__":
    ruta    = sys.argv[1] if len(sys.argv) > 1 else "data/accidentes_limpio.parquet"
    address = sys.argv[2] if len(sys.argv) > 2 else None   # ej: ray://head:10001

    df = pd.read_parquet(ruta)
    print(f"\n── Análisis RAY ({len(df):,} registros) ──")
    res, t = analizar_ray(df, address=address)
    guardar_resultados(res)
    ray.shutdown()
