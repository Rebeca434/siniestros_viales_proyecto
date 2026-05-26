"""
benchmark.py
Compara el tiempo de ejecución entre:
  1. Pandas secuencial
  2. Ray local (paralelo)
  3. Ray Cluster (distribuido) — solo si hay cluster activo

Genera outputs/benchmark_resultados.csv y outputs/benchmark_speedup.csv
"""
import pandas as pd
import time
import os
import sys
import json


def ejecutar_benchmark(
    ruta_datos: str = "data/accidentes_limpio.parquet",
    ray_address: str = None,
    n_repeticiones: int = 1,
) -> dict:
    """
    Ejecuta los tres modos y devuelve los tiempos.

    n_repeticiones: promedia los tiempos para mayor estabilidad.
    """
    import ray
    from analisis_secuencial import analizar as analizar_seq
    from analisis_ray import analizar_ray

    os.makedirs("outputs", exist_ok=True)

    df = pd.read_parquet(ruta_datos)
    n  = len(df)
    print(f"\n{'='*60}")
    print(f"  BENCHMARK — {n:,} registros  |  {n_repeticiones} repetición(es)")
    print(f"{'='*60}")

    tiempos = {}

    # ── 1. Secuencial ─────────────────────────────────────────────────────────
    print("\n[1/3] Pandas secuencial…")
    t_seq = []
    for i in range(n_repeticiones):
        _, t = analizar_seq(df)
        t_seq.append(t)
    tiempos["secuencial_s"] = sum(t_seq) / len(t_seq)
    print(f"  Promedio: {tiempos['secuencial_s']:.3f}s")

    # ── 2. Ray local ──────────────────────────────────────────────────────────
    print("\n[2/3] Ray local (paralelo)…")
    t_ray_local = []
    for i in range(n_repeticiones):
        if ray.is_initialized():
            ray.shutdown()
        _, t = analizar_ray(df, address=None)
        t_ray_local.append(t)
        ray.shutdown()
    tiempos["ray_local_s"] = sum(t_ray_local) / len(t_ray_local)
    print(f"  Promedio: {tiempos['ray_local_s']:.3f}s")

    # ── 3. Ray Cluster ────────────────────────────────────────────────────────
    if ray_address:
        print(f"\n[3/3] Ray Cluster ({ray_address})…")
        t_ray_cluster = []
        try:
            for i in range(n_repeticiones):
                if ray.is_initialized():
                    ray.shutdown()
                _, t = analizar_ray(df, address=ray_address)
                t_ray_cluster.append(t)
                ray.shutdown()
            tiempos["ray_cluster_s"] = sum(t_ray_cluster) / len(t_ray_cluster)
            print(f"  Promedio: {tiempos['ray_cluster_s']:.3f}s")
        except Exception as e:
            print(f"  Cluster no disponible: {e}")
            tiempos["ray_cluster_s"] = None
    else:
        tiempos["ray_cluster_s"] = None
        print("\n[3/3] Ray Cluster — no configurado (pasa ray_address para activarlo)")

    # ── Calcular speedup ──────────────────────────────────────────────────────
    base = tiempos["secuencial_s"]
    speedup_local   = round(base / tiempos["ray_local_s"], 2) if tiempos["ray_local_s"] else None
    speedup_cluster = (
        round(base / tiempos["ray_cluster_s"], 2)
        if tiempos.get("ray_cluster_s") else None
    )

    resumen = {
        "n_registros":          n,
        "secuencial_s":         round(tiempos["secuencial_s"], 3),
        "ray_local_s":          round(tiempos["ray_local_s"],  3),
        "ray_cluster_s":        tiempos["ray_cluster_s"],
        "speedup_local":        speedup_local,
        "speedup_cluster":      speedup_cluster,
    }

    # ── Guardar CSV ───────────────────────────────────────────────────────────
    pd.DataFrame([resumen]).to_csv("outputs/benchmark_resultados.csv", index=False)

    tabla_speedup = pd.DataFrame([
        {"modo": "Pandas Secuencial", "tiempo_s": resumen["secuencial_s"], "speedup": 1.0},
        {"modo": "Ray Local",         "tiempo_s": resumen["ray_local_s"],  "speedup": speedup_local},
    ])
    if speedup_cluster:
        tabla_speedup = pd.concat([
            tabla_speedup,
            pd.DataFrame([{
                "modo": "Ray Cluster",
                "tiempo_s": resumen["ray_cluster_s"],
                "speedup": speedup_cluster,
            }])
        ], ignore_index=True)
    tabla_speedup.to_csv("outputs/benchmark_speedup.csv", index=False)

    # ── Imprimir tabla resumen ────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  RESULTADOS DEL BENCHMARK")
    print(f"{'='*60}")
    print(f"  Registros analizados : {n:,}")
    print(f"  Secuencial (Pandas)  : {resumen['secuencial_s']:.3f}s")
    print(f"  Ray Local            : {resumen['ray_local_s']:.3f}s  (speedup {speedup_local}x)")
    if resumen["ray_cluster_s"]:
        print(f"  Ray Cluster          : {resumen['ray_cluster_s']:.3f}s  (speedup {speedup_cluster}x)")
    print(f"{'='*60}\n")

    return resumen


if __name__ == "__main__":
    ruta    = sys.argv[1] if len(sys.argv) > 1 else "data/accidentes_limpio.parquet"
    address = sys.argv[2] if len(sys.argv) > 2 else None
    ejecutar_benchmark(ruta, ray_address=address, n_repeticiones=1)
