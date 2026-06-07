"""
SIMULACIÓN SISTEMA DE PARQUEADEROS - CENTRO COMERCIAL SUPERCENTRO
Modelo M/M/1 con 3 cajeros independientes
"""

import os
import sys

import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# Permitir caracteres Unicode (λ, μ, ρ, emojis) en la consola de Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except (AttributeError, ValueError):
    pass

# Carpeta de salida para las gráficas (junto a este script)
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# CONFIGURACIÓN DE SEMILLA PARA REPRODUCIBILIDAD
# ============================================================
np.random.seed(42)

# ============================================================
# PARÁMETROS DEL SISTEMA
# ============================================================
USUARIOS = {
    'rapido':    {'servicio': 1, 'llegada': 3, 'prob': 0.25,  'label': 'Rápido',    'color': 'green'},
    'normal':    {'servicio': 3, 'llegada': 3, 'prob': 0.20,  'label': 'Normal',    'color': 'blue'},
    'lento':     {'servicio': 4, 'llegada': 5, 'prob': 0.275, 'label': 'Lento',     'color': 'orange'},
    'muy_lento': {'servicio': 6, 'llegada': 7, 'prob': 0.275, 'label': 'Muy Lento', 'color': 'red'},
}

NUM_CAJEROS = 3
TIEMPO_SIMULACION = 2000   # minutos por réplica
NUM_REPLICAS = 10
VENTANA_MOVIL = 50         # ventana para promedios móviles


# ============================================================
# FUNCIÓN PRINCIPAL: SIMULACIÓN DE UN CAJERO M/M/1
# ============================================================
def simular_mm1(tipo_usuario, tiempo_sim):
    """
    Simula un cajero M/M/1 para un tipo de usuario dado.
    Retorna listas con los tiempos de espera en cola y tiempos totales en sistema,
    junto con el tipo de usuario atendido en cada evento.
    """
    lam = 1.0 / tipo_usuario['llegada']   # tasa de llegadas
    mu  = 1.0 / tipo_usuario['servicio']  # tasa de servicio

    t = 0.0
    prox_llegada = np.random.exponential(1 / lam)
    prox_salida  = float('inf')
    clientes_sistema = 0

    tiempos_espera  = []   # Wq por cliente
    tiempos_sistema = []   # W  por cliente
    inicio_servicio = {}   # {id_cliente: tiempo_inicio_servicio}
    tiempo_llegada  = {}   # {id_cliente: tiempo_llegada}
    id_cliente = 0

    while t < tiempo_sim:
        # Decidir próximo evento
        if prox_llegada <= prox_salida:
            t = prox_llegada

            # --- LLEGADA ---
            id_cliente += 1
            tiempo_llegada[id_cliente] = t
            clientes_sistema += 1

            if clientes_sistema == 1:
                # Pasa directo a ser atendido
                inicio_servicio[id_cliente] = t
                tiempos_espera.append(0.0)
                prox_salida = t + np.random.exponential(1 / mu)

            prox_llegada = t + np.random.exponential(1 / lam)

        else:
            t = prox_salida

            # --- SALIDA ---
            # Encontrar el cliente que sale (el que lleva más tiempo en servicio)
            cliente_sale = min(inicio_servicio, key=inicio_servicio.get)
            t_llegada    = tiempo_llegada.pop(cliente_sale)
            t_inicio     = inicio_servicio.pop(cliente_sale)

            tiempos_sistema.append(t - t_llegada)
            clientes_sistema -= 1

            if clientes_sistema > 0:
                # Siguiente cliente en cola pasa a servicio
                siguiente = min(tiempo_llegada, key=tiempo_llegada.get)
                inicio_servicio[siguiente] = t
                espera = t - tiempo_llegada[siguiente]
                tiempos_espera.append(max(0.0, espera))
                prox_salida = t + np.random.exponential(1 / mu)
            else:
                prox_salida = float('inf')

    return tiempos_espera, tiempos_sistema


# ============================================================
# FUNCIÓN: DETERMINAR ESTADO ESTABLE
# ============================================================
def determinar_estado_estable(datos, ventana=50):
    """
    Calcula promedios móviles y detecta el punto de corte
    donde la varianza se estabiliza (estado estable).
    """
    promedios = []
    for i in range(len(datos) - ventana):
        promedios.append(np.mean(datos[i:i + ventana]))

    varianzas = []
    for i in range(len(promedios) - ventana):
        varianzas.append(np.var(promedios[i:i + ventana]))

    if not varianzas:
        return ventana, promedios

    punto_corte = int(np.argmin(varianzas)) + ventana
    return punto_corte, promedios


# ============================================================
# PUNTO 5: GRÁFICA ESTADO TRANSITORIO vs ESTABLE
# ============================================================
def graficar_estado_estable(datos, promedios, punto_corte, titulo, nombre_archivo):
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))

    # -- Gráfico superior: datos completos con punto de corte --
    axes[0].plot(datos, color='steelblue', alpha=0.4, label='Datos originales')
    axes[0].plot(range(len(promedios)), promedios, color='darkorange',
                linewidth=2, label='Promedio móvil')
    axes[0].axvline(x=punto_corte, color='red', linestyle='--', linewidth=2,
                    label=f'Punto de corte: {punto_corte}')
    axes[0].set_title(f'{titulo} - Con estado transitorio', fontsize=12)
    axes[0].set_xlabel('Número de cliente')
    axes[0].set_ylabel('Tiempo en sistema (min)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # -- Gráfico inferior: solo estado estable --
    datos_estables = datos[punto_corte:]
    axes[1].plot(datos_estables, color='green', alpha=0.6, label='Estado estable')
    axes[1].axhline(y=np.mean(datos_estables), color='darkgreen', linewidth=2,
                    linestyle='-', label=f'Media estable: {np.mean(datos_estables):.2f} min')
    axes[1].set_title(f'{titulo} - Sin estado transitorio (después del corte)', fontsize=12)
    axes[1].set_xlabel('Número de cliente (relativo)')
    axes[1].set_ylabel('Tiempo en sistema (min)')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(nombre_archivo, dpi=120)
    plt.close()
    print(f"  Gráfica guardada: {nombre_archivo}")


# ============================================================
# SIMULACIÓN PRINCIPAL
# ============================================================
def ejecutar_simulacion():
    print("=" * 65)
    print("  SIMULACIÓN PARQUEADERO - CENTRO COMERCIAL SUPERCENTRO")
    print("=" * 65)

    # Resultados agregados
    resultados_cajeros  = {i: [] for i in range(NUM_CAJEROS)}
    conteo_usuarios     = {k: 0 for k in USUARIOS}
    tiempos_por_tipo    = {k: [] for k in USUARIOS}

    # Para validación teórica (punto 4)
    validacion = {}

    tipos = list(USUARIOS.keys())
    probs = [USUARIOS[t]['prob'] for t in tipos]

    print(f"\nEjecutando {NUM_REPLICAS} réplicas de {TIEMPO_SIMULACION} minutos cada una...")

    for replica in range(NUM_REPLICAS):
        for cajero in range(NUM_CAJEROS):
            # Asignar un tipo de usuario aleatorio a este cajero en esta réplica
            tipo_key = np.random.choice(tipos, p=probs)
            tipo     = USUARIOS[tipo_key]

            esperas, sistema = simular_mm1(tipo, TIEMPO_SIMULACION)

            if sistema:
                media_w = np.mean(sistema)
                resultados_cajeros[cajero].append(media_w)
                conteo_usuarios[tipo_key] += len(sistema)
                tiempos_por_tipo[tipo_key].extend(sistema)

    # =======================================================
    # PUNTO 4: VERIFICACIÓN, CALIBRACIÓN Y VALIDACIÓN
    # =======================================================
    print("\n" + "=" * 65)
    print("PUNTO 4 - VERIFICACIÓN, CALIBRACIÓN Y VALIDACIÓN")
    print("=" * 65)

    print("\n[VERIFICACIÓN] Comprobando parámetros del modelo:")
    for k, v in USUARIOS.items():
        lam = 1 / v['llegada']
        mu  = 1 / v['servicio']
        rho = lam / mu
        estado = "ESTABLE ✓" if rho < 1 else "CRÍTICO ⚠️"
        print(f"  {v['label']:10s} | λ={lam:.3f} | μ={mu:.3f} | ρ={rho:.3f} | {estado}")

    print("\n[CALIBRACIÓN] Comparando simulación vs teoría M/M/1:")
    print(f"  {'Tipo':<12} {'W_teórico':>12} {'W_simulado':>12} {'Error%':>8} {'Validado':>10}")
    print("  " + "-" * 58)

    for k, v in USUARIOS.items():
        lam = 1 / v['llegada']
        mu  = 1 / v['servicio']
        if mu > lam:
            W_teo = 1 / (mu - lam)
        else:
            W_teo = float('inf')

        datos_sim = tiempos_por_tipo[k]
        if datos_sim and W_teo != float('inf'):
            W_sim = np.mean(datos_sim)
            error = abs(W_sim - W_teo) / W_teo * 100
            # Prueba t de validación
            t_stat, p_val = stats.ttest_1samp(datos_sim[:500] if len(datos_sim) > 500 else datos_sim,
            W_teo)
            validado = "SÍ ✓" if p_val > 0.05 else "NO ✗"
            print(f"  {v['label']:<12} {W_teo:>12.3f} {W_sim:>12.3f} {error:>7.1f}% {validado:>10}")
            validacion[k] = {'W_teo': W_teo, 'W_sim': W_sim, 'p_val': p_val}
        else:
            print(f"  {v['label']:<12} {'∞':>12} {'N/A':>12} {'N/A':>7}  {'N/A':>10}")

    # =======================================================
    # PUNTO 5: ESTADO TRANSITORIO (con el tipo MÁS ESTRESADO)
    # =======================================================
    print("\n" + "=" * 65)
    print("PUNTO 5 - ELIMINACIÓN DEL ESTADO TRANSITORIO")
    print("=" * 65)

    tipo_demo = 'lento'
    esperas_demo, sistema_demo = simular_mm1(USUARIOS[tipo_demo], TIEMPO_SIMULACION * 2)
    punto_corte, promedios = determinar_estado_estable(sistema_demo, VENTANA_MOVIL)
    print(f"  Tipo de usuario para demo: {USUARIOS[tipo_demo]['label']}")
    print(f"  Punto de corte detectado: cliente #{punto_corte}")
    print(f"  Media CON transitorio:    {np.mean(sistema_demo):.3f} min")
    print(f"  Media SIN transitorio:    {np.mean(sistema_demo[punto_corte:]):.3f} min")

    graficar_estado_estable(
        sistema_demo, promedios, punto_corte,
        f"Estado Estable - Usuario {USUARIOS[tipo_demo]['label']}",
        os.path.join(OUTPUT_DIR, "punto5_estado_estable.png")
    )

    # =======================================================
    # PUNTO 1: ESTADÍSTICAS POR CAJERO
    # =======================================================
    print("\n" + "=" * 65)
    print("PUNTO 1 - ESTADÍSTICAS POR CAJERO (Tiempo promedio de atención)")
    print("=" * 65)

    stats_cajeros = {}
    for i in range(NUM_CAJEROS):
        datos = resultados_cajeros[i]
        if not datos:
            continue
        media  = np.mean(datos)
        desvio = np.std(datos, ddof=1)
        minimo = np.min(datos)
        maximo = np.max(datos)
        n      = len(datos)
        t_crit = stats.t.ppf(0.975, n - 1)
        margen = t_crit * (desvio / np.sqrt(n))
        stats_cajeros[i] = {
            'media': media, 'std': desvio,
            'min': minimo, 'max': maximo,
            'ic_inf': media - margen, 'ic_sup': media + margen
        }
        print(f"\n  Cajero {i+1}:")
        print(f"    Media:      {media:.3f} min")
        print(f"    Desv. Std:  {desvio:.3f} min")
        print(f"    Mín/Máx:    {minimo:.3f} / {maximo:.3f} min")
        print(f"    IC 95%:     [{media - margen:.3f}, {media + margen:.3f}]")

    mejor_cajero = min(stats_cajeros, key=lambda x: stats_cajeros[x]['media'])
    peor_cajero  = max(stats_cajeros, key=lambda x: stats_cajeros[x]['media'])
    print(f"\n  ✅ Cajero más eficiente:   Cajero {mejor_cajero + 1} ({stats_cajeros[mejor_cajero]['media']:.3f} min)")
    print(f"  ❌ Cajero menos eficiente: Cajero {peor_cajero  + 1} ({stats_cajeros[peor_cajero]['media']:.3f} min)")

    # Gráfica punto 1
    fig, ax = plt.subplots(figsize=(9, 5))
    cajeros_labels = [f'Cajero {i+1}' for i in range(NUM_CAJEROS)]
    medias = [stats_cajeros[i]['media'] for i in range(NUM_CAJEROS)]
    errores = [stats_cajeros[i]['media'] - stats_cajeros[i]['ic_inf'] for i in range(NUM_CAJEROS)]
    colores = ['#2ecc71' if i == mejor_cajero else ('#e74c3c' if i == peor_cajero else '#3498db')
            for i in range(NUM_CAJEROS)]
    bars = ax.bar(cajeros_labels, medias, color=colores, yerr=errores,
                capsize=6, edgecolor='black', linewidth=0.8)
    ax.set_title('Tiempo Promedio de Atención por Cajero\n(con IC 95%)', fontsize=13)
    ax.set_ylabel('Tiempo promedio (min)')
    ax.set_xlabel('Cajero')
    for bar, m in zip(bars, medias):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                f'{m:.2f}', ha='center', fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'punto1_cajeros.png'), dpi=120)
    plt.close()
    print("  Gráfica guardada: punto1_cajeros.png")

    # =======================================================
    # PUNTO 2: PROMEDIO DE USUARIOS POR TIPO
    # =======================================================
    print("\n" + "=" * 65)
    print("PUNTO 2 - USUARIOS POR TIPO EN TODOS LOS CAJEROS")
    print("=" * 65)

    total_usuarios = sum(conteo_usuarios.values())
    print(f"\n  {'Tipo':<12} {'Cantidad':>10} {'Porcentaje':>12} {'Esperado':>10} {'W_promedio':>12}")
    print("  " + "-" * 58)

    for k, v in USUARIOS.items():
        cant    = conteo_usuarios[k]
        pct     = cant / total_usuarios * 100 if total_usuarios else 0
        esp_pct = v['prob'] * 100
        w_prom  = np.mean(tiempos_por_tipo[k]) if tiempos_por_tipo[k] else 0
        print(f"  {v['label']:<12} {cant:>10} {pct:>11.1f}% {esp_pct:>9.1f}% {w_prom:>11.3f} min")

    # Gráfica punto 2
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    tipos_labels = [USUARIOS[k]['label'] for k in USUARIOS]
    porcentajes  = [conteo_usuarios[k] / total_usuarios * 100 if total_usuarios else 0 for k in USUARIOS]
    esperados    = [USUARIOS[k]['prob'] * 100 for k in USUARIOS]
    colores_tipo = [USUARIOS[k]['color'] for k in USUARIOS]

    x = np.arange(len(tipos_labels))
    w = 0.35
    axes[0].bar(x - w/2, esperados, w, label='Esperado', color='lightgray', edgecolor='black')
    axes[0].bar(x + w/2, porcentajes, w, label='Simulado', color=colores_tipo, edgecolor='black')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(tipos_labels)
    axes[0].set_title('Distribución de Usuarios\nEsperado vs Simulado')
    axes[0].set_ylabel('Porcentaje (%)')
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)

    w_promedios = [np.mean(tiempos_por_tipo[k]) if tiempos_por_tipo[k] else 0 for k in USUARIOS]
    axes[1].bar(tipos_labels, w_promedios, color=colores_tipo, edgecolor='black')
    axes[1].set_title('Tiempo Promedio en Sistema\npor Tipo de Usuario')
    axes[1].set_ylabel('Tiempo promedio (min)')
    axes[1].grid(axis='y', alpha=0.3)
    for bar, val in zip(axes[1].patches, w_promedios):
        axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
        f'{val:.2f}', ha='center', fontsize=9)

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'punto2_usuarios.png'), dpi=120)
    plt.close()
    print("  Gráfica guardada: punto2_usuarios.png")

    # =======================================================
    # PUNTO 3: ESTRATEGIA DE MEJORA
    # =======================================================
    print("\n" + "=" * 65)
    print("PUNTO 3 - ESTRATEGIA DE MEJORA")
    print("=" * 65)

    # Criterios de decisión
    CRITERIOS = {
        'Wq_max': 3.0,      # tiempo en cola máximo aceptable (min)
        'W_max': 5.0,       # tiempo en sistema máximo aceptable (min)
        'rho_max': 0.85,    # utilización máxima aceptable
    }

    print(f"\n  Criterios de aceptación:")
    print(f"    Wq máximo: {CRITERIOS['Wq_max']} min")
    print(f"    W  máximo: {CRITERIOS['W_max']} min")
    print(f"    ρ  máximo: {CRITERIOS['rho_max']*100:.0f}%")

    print(f"\n  {'Tipo':<12} {'ρ':>8} {'Wq_teo':>10} {'W_teo':>10} {'¿OK?':>8}")
    print("  " + "-" * 52)

    problemas = []
    for k, v in USUARIOS.items():
        lam = 1 / v['llegada']
        mu  = 1 / v['servicio']
        rho = lam / mu
        if rho < 1:
            Wq = rho / (mu - lam)
            W  = 1   / (mu - lam)
        else:
            Wq = W = float('inf')

        ok = (rho < CRITERIOS['rho_max'] and
            (Wq == float('inf') or Wq < CRITERIOS['Wq_max']) and
            (W  == float('inf') or W  < CRITERIOS['W_max']))

        estado = "✓ OK" if ok else "✗ MEJORA"
        Wq_str = f"{Wq:.3f}" if Wq != float('inf') else "∞"
        W_str  = f"{W:.3f}"  if W  != float('inf') else "∞"
        print(f"  {v['label']:<12} {rho:>8.3f} {Wq_str:>10} {W_str:>10} {estado:>8}")

        if not ok:
            problemas.append(v['label'])

    if problemas:
        print(f"\n  ⚠️  Tipos que requieren mejora: {', '.join(problemas)}")
        print("\n  RECOMENDACIONES:")
        print("  1. Usuario Normal (ρ=1.0): Agregar un cajero exclusivo para usuarios normales.")
        print("     Un cajero adicional baja el ρ efectivo a ~0.5, estabilizando el sistema.")
        print("  2. Implementar cajero exprés para usuarios Rápidos.")
        print("  3. Capacitar operadores para reducir μ en usuarios Lentos/Muy Lentos.")
    else:
        print("\n  ✅ El sistema actual con 3 cajeros es SUFICIENTE.")

    # Gráfica comparativa ρ
    fig, ax = plt.subplots(figsize=(9, 5))
    rhos = [1/USUARIOS[k]['llegada'] / (1/USUARIOS[k]['servicio']) for k in USUARIOS]
    colores_rho = ['green' if r < 0.85 else ('orange' if r < 1 else 'red') for r in rhos]
    bars = ax.bar(tipos_labels, rhos, color=colores_rho, edgecolor='black')
    ax.axhline(y=0.85, color='orange', linestyle='--', linewidth=1.5, label='Límite aceptable (85%)')
    ax.axhline(y=1.0,  color='red',    linestyle='--', linewidth=1.5, label='Límite estabilidad (100%)')
    ax.set_title('Factor de Utilización (ρ) por Tipo de Usuario', fontsize=13)
    ax.set_ylabel('ρ (Utilización)')
    ax.set_ylim(0, 1.2)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    for bar, rho in zip(bars, rhos):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{rho:.3f}', ha='center', fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'punto3_mejora.png'), dpi=120)
    plt.close()
    print("  Gráfica guardada: punto3_mejora.png")

    # =======================================================
    # PUNTO 4: GRÁFICA V&V (SIMULADO vs TEÓRICO)
    # =======================================================
    tipos_val = [k for k in validacion]
    W_teos = [validacion[k]['W_teo'] for k in tipos_val]
    W_sims = [validacion[k]['W_sim'] for k in tipos_val]
    labels_val = [USUARIOS[k]['label'] for k in tipos_val]

    x_v = np.arange(len(labels_val))
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x_v - 0.2, W_teos, 0.35, label='Teórico M/M/1', color='steelblue', edgecolor='black')
    ax.bar(x_v + 0.2, W_sims, 0.35, label='Simulado',       color='coral',     edgecolor='black')
    ax.set_xticks(x_v)
    ax.set_xticklabels(labels_val)
    ax.set_title('Validación: Tiempo en Sistema W\nTeórico vs Simulado (M/M/1)', fontsize=13)
    ax.set_ylabel('W (minutos)')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'punto4_validacion.png'), dpi=120)
    plt.close()
    print("  Gráfica guardada: punto4_validacion.png")

    print("\n" + "=" * 65)
    print("  SIMULACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 65)


# ============================================================
# EJECUCIÓN
# ============================================================
if __name__ == '__main__':
    ejecutar_simulacion()
