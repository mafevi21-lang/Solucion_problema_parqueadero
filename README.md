<<<<<<< HEAD
Simulación Sistema de Parqueaderos — Centro Comercial Supercentro
Laboratorio Final · Actividad Didáctica 2
Modelo M/M/1 con 3 cajeros independientes

Descripción
Este proyecto simula el sistema de pago de parqueaderos del Centro Comercial Supercentro
usando el modelo de colas M/M/1. Cada uno de los 3 cajeros se simula de forma independiente
con cuatro tipos de usuarios (Rápido, Normal, Lento, Muy Lento) que siguen distribuciones
exponenciales en sus tiempos de llegada y servicio.

Requisitos

Python 3.8 o superior
NumPy
SciPy
Matplotlib

Instalar dependencias:
pip install numpy scipy matplotlib

Cómo ejecutar
python parqueadero_simulacion.py
El script imprime todos los resultados en consola y guarda 4 gráficas en la misma carpeta.

Parámetros del sistema
Tipo de usuarioTiempo servicio (μ)Tiempo llegada (λ)ρDistribuciónRápido1 min3 min0.333ExponencialNormal3 min3 min1.000 ⚠️ExponencialLento4 min5 min0.800ExponencialMuy Lento6 min7 min0.857Exponencial

NUM_CAJEROS = 3
TIEMPO_SIMULACION = 2000 minutos por réplica
NUM_REPLICAS = 10
VENTANA_MOVIL = 50 (para promedios móviles)

Todos estos valores pueden modificarse al inicio del archivo.

Estructura del código
parqueadero_simulacion.py
│
├── PARÁMETROS          → Diccionario USUARIOS con λ, μ, proporción y color
├── simular_mm1()       → Motor de simulación por eventos discretos (M/M/1)
├── determinar_estado_estable() → Promedio móvil + detección de punto de corte
├── graficar_estado_estable()   → Gráfica antes/después del transitorio
└── ejecutar_simulacion()
    ├── Punto 4 — Verificación, Calibración y Validación
    ├── Punto 5 — Eliminación del estado transitorio
    ├── Punto 1 — Estadísticas por cajero (IC 95%)
    ├── Punto 2 — Distribución de usuarios por tipo
    └── Punto 3 — Estrategia de mejora

Salidas generadas
ArchivoContenidopunto1_cajeros.pngTiempo promedio por cajero con IC 95%punto2_usuarios.pngDistribución y tiempos por tipo de usuariopunto3_mejora.pngFactor de utilización ρ por tipopunto4_validacion.pngComparación teórico M/M/1 vs simuladopunto5_estado_estable.pngTransitorio vs estado estable (promedio móvil)

Puntos resueltos
Punto 1 — Estadísticas por cajero
Se calculan media, desviación estándar, mínimo, máximo e intervalo de confianza al 95%
para el tiempo promedio de atención de cada cajero. Se identifican el cajero más eficiente
y el menos eficiente.
Punto 2 — Usuarios por tipo
Se contabilizan y promedian los usuarios atendidos de cada tipo en los 3 cajeros.
Se verifica que las proporciones simuladas sean cercanas a las teóricas
(25%, 20%, 27.5%, 27.5%).
Punto 3 — Estrategia de mejora
Se evalúan criterios de aceptación (Wq < 3 min, W < 5 min, ρ < 85%).
El análisis muestra que los usuarios Normal, Lento y Muy Lento superan estos límites.
Se recomiendan: cajero adicional para usuarios Normales, cajero exprés para Rápidos
y capacitación para reducir tiempos de servicio.
Punto 4 — Verificación, Calibración y Validación

Verificación: comprobación de parámetros λ, μ y ρ de cada tipo de usuario.
Calibración: comparación de W simulado vs W teórico M/M/1 con cálculo del error %.
Validación: prueba t de una muestra (H₀: W_sim = W_teórico, α = 0.05).

Punto 5 — Eliminación del estado transitorio
Se aplica promedio móvil con ventana de 50 observaciones para detectar
el punto de corte donde la varianza se estabiliza. Se grafican los datos
con y sin el período transitorio, y se recalcula la media solo con el estado estable.

Observación importante
El usuario Normal tiene ρ = 1.0, lo que en teoría genera colas infinitas.
En la simulación esto se manifiesta con tiempos en sistema muy elevados (~63 min promedio).
Este es el principal cuello de botella del sistema y la razón más urgente de mejora.
=======
# Solucion_problema_parqueadero
>>>>>>> 86c34114c8f0a8ab13a8d6b3a0f20506d519318b
