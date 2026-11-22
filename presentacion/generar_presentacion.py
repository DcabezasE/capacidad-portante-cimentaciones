"""
generar_presentacion.py
========================
Genera la presentación (.pptx) de la exposición grupal sobre el programa
de capacidad portante en cimentaciones superficiales (Terzaghi y Vesić).

Estructura basada en el guion de 5 personas / 15 minutos:
  Portada
  Persona 1 (0:00-3:00)  -> 2 diapositivas
  Persona 2 (3:00-6:00)  -> 2 diapositivas
  Persona 3 (6:00-9:00)  -> 2 diapositivas
  Persona 4 (9:00-12:00) -> 1 diapositiva + demo
  Persona 5 (12:00-15:00)-> 2 diapositivas

Ejecutar (con python-pptx disponible):
    python presentacion/generar_presentacion.py
El archivo se crea en:  presentacion/Capacidad_Portante.pptx
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR


# ---------------------------------------------------------------------------
# Paleta de colores (azul/gris académico, sobrio y profesional)
# ---------------------------------------------------------------------------
AZUL_OSCURO = RGBColor(0x1F, 0x3A, 0x5F)   # títulos / barras
AZUL_MEDIO = RGBColor(0x2E, 0x5E, 0x8C)    # acentos
GRIS = RGBColor(0x55, 0x55, 0x55)          # texto secundario
BLANCO = RGBColor(0xFF, 0xFF, 0xFF)
GRIS_CLARO = RGBColor(0xF0, 0xF3, 0xF7)    # fondos suaves


# ---------------------------------------------------------------------------
# DATOS EDITABLES  (cambia estos valores por los de tu grupo)
# ---------------------------------------------------------------------------
TITULO = "Capacidad Portante en Cimentaciones Superficiales"
SUBTITULO = "Métodos de Terzaghi y Vesić — Programa en Python"
MATERIA = "Geotecnia · Ingeniería Civil"
PROFESOR = "Profesor: [Nombre del profesor]"
UNIVERSIDAD = "[Nombre de la Universidad]"
FECHA = "[Fecha de la exposición]"
INTEGRANTES = [
    "[Integrante 1]",
    "[Integrante 2]",
    "[Integrante 3]",
    "[Integrante 4]",
    "[Integrante 5]",
]


# ---------------------------------------------------------------------------
# Utilidades de maquetado
# ---------------------------------------------------------------------------
def set_background(slide, color):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_top_bar(slide, prs, texto_persona, tiempo):
    """Barra superior con la etiqueta de persona y el tiempo asignado."""
    bar = slide.shapes.add_shape(
        1,  # MSO_SHAPE.RECTANGLE
        Inches(0), Inches(0), prs.slide_width, Inches(0.55),
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = AZUL_OSCURO
    bar.line.fill.background()
    tf = bar.text_frame
    tf.margin_left = Inches(0.3)
    tf.margin_top = Inches(0.05)
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = f"{texto_persona}    |    {tiempo}"
    run.font.size = Pt(12)
    run.font.color.rgb = BLANCO
    run.font.bold = True


def add_title(slide, texto, top=Inches(0.75)):
    box = slide.shapes.add_textbox(Inches(0.6), top, Inches(8.8), Inches(0.9))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = texto
    run.font.size = Pt(28)
    run.font.bold = True
    run.font.color.rgb = AZUL_OSCURO
    return box


def add_bullets(slide, bullets, top=Inches(1.8), left=Inches(0.8),
                width=Inches(8.4), height=Inches(4.6), size=18):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    for i, (texto, nivel) in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.level = nivel
        p.space_after = Pt(10)
        run = p.add_run()
        prefijo = "•  " if nivel == 0 else "–  "
        run.text = prefijo + texto
        run.font.size = Pt(size - nivel * 3)
        run.font.color.rgb = GRIS if nivel > 0 else RGBColor(0x22, 0x22, 0x22)
        if nivel == 0:
            run.font.bold = False
    return box


def add_footer(slide, prs, texto):
    box = slide.shapes.add_textbox(
        Inches(0.3), prs.slide_height - Inches(0.4),
        prs.slide_width - Inches(0.6), Inches(0.3))
    p = box.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    run = p.add_run()
    run.text = texto
    run.font.size = Pt(9)
    run.font.color.rgb = GRIS


# ---------------------------------------------------------------------------
# Construcción de la presentación
# ---------------------------------------------------------------------------
def build():
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]  # layout en blanco

    n_total = {"n": 0}

    def nueva(persona=None, tiempo=None):
        slide = prs.slides.add_slide(blank)
        set_background(slide, BLANCO)
        if persona:
            add_top_bar(slide, prs, persona, tiempo)
        n_total["n"] += 1
        add_footer(slide, prs, f"{TITULO} · Diapositiva {n_total['n']}")
        return slide

    # ----------------------------------------------------------- PORTADA
    s = prs.slides.add_slide(blank)
    set_background(s, AZUL_OSCURO)
    # Título
    box = s.shapes.add_textbox(Inches(0.8), Inches(2.0), Inches(8.4), Inches(1.8))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = TITULO
    r.font.size = Pt(34); r.font.bold = True; r.font.color.rgb = BLANCO
    p2 = tf.add_paragraph()
    r2 = p2.add_run(); r2.text = SUBTITULO
    r2.font.size = Pt(18); r2.font.color.rgb = RGBColor(0xBF, 0xD4, 0xE8)
    # Datos
    box2 = s.shapes.add_textbox(Inches(0.8), Inches(4.3), Inches(8.4), Inches(2.6))
    tf2 = box2.text_frame; tf2.word_wrap = True
    for i, linea in enumerate([MATERIA, PROFESOR, UNIVERSIDAD, FECHA, "",
                               "Integrantes:  " + " · ".join(INTEGRANTES)]):
        p = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
        r = p.add_run(); r.text = linea
        r.font.size = Pt(14); r.font.color.rgb = RGBColor(0xDD, 0xE6, 0xF0)
    n_total["n"] = 0  # la portada no cuenta en el pie

    # ------------------------------------------------ PERSONA 1 (0:00-3:00)
    P1 = "01 · Persona 1 — Introducción y objetivo"
    s = nueva(P1, "0:00 – 3:00")
    add_title(s, "El problema: capacidad portante")
    add_bullets(s, [
        ("¿Qué es la capacidad portante? La presión máxima que el suelo "
         "soporta bajo una cimentación sin fallar.", 0),
        ("Cimentaciones superficiales: zapatas que transmiten la carga de "
         "la estructura a un suelo relativamente cercano a la superficie.", 0),
        ("El reto: diseñar la zapata para que el suelo NO falle por corte "
         "y los asentamientos sean tolerables.", 0),
        ("Si la presión aplicada supera la capacidad del suelo → falla "
         "y colapso de la estructura.", 0),
    ])

    s = nueva(P1, "0:00 – 3:00")
    add_title(s, "Objetivo del programa")
    add_bullets(s, [
        ("Objetivo: calcular la capacidad portante última y admisible "
         "por dos métodos clásicos.", 0),
        ("Métodos implementados:", 0),
        ("Terzaghi (1943)", 1),
        ("Vesić (1973)", 1),
        ("Datos de entrada:", 0),
        ("Geometría (ancho B, largo L, profundidad Df, forma)", 1),
        ("Suelo (γ, φ, cohesión c), nivel freático", 1),
        ("Cargas y factor de seguridad", 1),
        ("Resultados esperados: q_última, q_admisible y carga admisible.", 0),
    ])

    # ------------------------------------------------ PERSONA 2 (3:00-6:00)
    P2 = "02 · Persona 2 — Fundamento teórico: Terzaghi y Vesić"
    s = nueva(P2, "3:00 – 6:00")
    add_title(s, "Ecuación general de capacidad portante")
    add_bullets(s, [
        ("q_u  =  c·Nc·sc·dc·ic  +  q·Nq·sq·dq·iq  +  ½·γ·B·Nγ·sγ·dγ·iγ", 0),
        ("Está formada por tres contribuciones (tres términos):", 0),
        ("Término de cohesión: resistencia por la cohesión del suelo (c)", 1),
        ("Término de sobrecarga: suelo situado a los lados, sobre la base (q)", 1),
        ("Término de peso: peso del suelo bajo la base (½·γ·B)", 1),
        ("s = factores de forma · d = profundidad · i = inclinación de carga.", 0),
    ])

    s = nueva(P2, "3:00 – 6:00")
    add_title(s, "Factores Nc, Nq, Nγ y diferencias")
    add_bullets(s, [
        ("Nc, Nq, Nγ son los factores de capacidad de carga; dependen solo "
         "del ángulo de fricción φ del suelo.", 0),
        ("Nc → acompaña a la cohesión · Nq → a la sobrecarga · "
         "Nγ → al peso del suelo.", 0),
        ("Terzaghi: ecuación más simple; NO incluye factores de profundidad "
         "ni de inclinación; usa factores de forma empíricos.", 0),
        ("Vesić: ecuación general completa; SÍ incluye factores de forma, "
         "profundidad e inclinación → resultado más refinado.", 0),
        ("Además, Terzaghi distingue falla general (suelo firme) y falla "
         "local (suelo suelto → reduce c y φ).", 0),
    ])

    # ------------------------------------------------ PERSONA 3 (6:00-9:00)
    P3 = "03 · Persona 3 — Desarrollo computacional en Python"
    s = nueva(P3, "6:00 – 9:00")
    add_title(s, "Python y entorno de desarrollo")
    add_bullets(s, [
        ("Lenguaje: Python, ideal para cálculo científico y de ingeniería, "
         "con sintaxis clara y legible.", 0),
        ("Entorno de desarrollo: Visual Studio Code (VS Code).", 0),
        ("Interfaz gráfica con Tkinter, incluida en Python: no requiere "
         "instalar librerías externas.", 0),
        ("El programa se ejecuta con un solo comando:  python app.py", 0),
    ])

    s = nueva(P3, "6:00 – 9:00")
    add_title(s, "Organización del código y flujo")
    add_bullets(s, [
        ("app.py → punto de entrada; abre la interfaz gráfica.", 0),
        ("core.py → el motor de cálculo: ecuaciones de Terzaghi y Vesić, "
         "factores, nivel freático y excentricidad.", 0),
        ("gui.py → la interfaz (Tkinter): formularios y resultados.", 0),
        ("ejemplos.py → casos de prueba para validar el programa.", 0),
        ("Secuencia de procesamiento:", 0),
        ("1) El usuario introduce los datos en la ventana", 1),
        ("2) gui.py recoge los datos y llama a core.py", 1),
        ("3) core.py calcula y devuelve los resultados", 1),
        ("4) gui.py muestra q_u, q_adm y los factores en pantalla", 1),
    ])

    # ----------------------------------------------- PERSONA 4 (9:00-12:00)
    P4 = "04 · Persona 4 — Interfaz gráfica y demostración"
    s = nueva(P4, "9:00 – 12:00  (1 diapositiva + demo en vivo)")
    add_title(s, "Interfaz gráfica (Tkinter) y demo")
    add_bullets(s, [
        ("Tkinter construye la ventana: campos de entrada, menús "
         "desplegables y el panel de resultados.", 0),
        ("Campos y opciones de la interfaz:", 0),
        ("Método (Terzaghi, Vesić o ambos) y forma de la zapata", 1),
        ("Geometría (B, L, Df) y propiedades del suelo (γ, φ, c)", 1),
        ("Nivel freático, cargas/excentricidad y factor de seguridad", 1),
        ("DEMOSTRACIÓN EN VIVO:", 0),
        ("Abrir el programa, introducir un caso de ejemplo y pulsar "
         "'Calcular' para mostrar los resultados en pantalla.", 1),
    ])

    # ----------------------------------------------- PERSONA 5 (12:00-15:00)
    P5 = "05 · Persona 5 — Verificación, limitaciones y conclusiones"
    s = nueva(P5, "12:00 – 15:00")
    add_title(s, "Verificación y comparación de métodos")
    add_bullets(s, [
        ("Se compararon los resultados de Terzaghi y Vesić para los mismos "
         "datos: Vesić suele dar mayor capacidad por incluir más factores.", 0),
        ("Validación frente a cálculos manuales y ejemplos del libro de "
         "Das: los factores Nc, Nq, Nγ coinciden con las tablas.", 0),
        ("Casos de prueba verificados:", 0),
        ("Zapata en arena y en suelo cohesivo-friccionante", 1),
        ("Efecto del nivel freático y de la excentricidad de carga", 1),
        ("El programa reproduce correctamente el comportamiento esperado.", 0),
    ])

    s = nueva(P5, "12:00 – 15:00")
    add_title(s, "Limitaciones, mejoras y conclusiones")
    add_bullets(s, [
        ("Limitaciones: calcula capacidad por corte, no verifica "
         "asentamientos; suelo homogéneo (una sola capa).", 0),
        ("Mejoras futuras: exportar informe en PDF, dibujar la zapata, "
         "analizar suelos estratificados.", 0),
        ("Conclusiones:", 0),
        ("El programa automatiza y agiliza un cálculo repetitivo y "
         "propenso a errores manuales.", 1),
        ("Permite comparar Terzaghi y Vesić de forma inmediata.", 1),
        ("Refuerza la comprensión de los factores que afectan la "
         "capacidad portante.", 1),
        ("¡Gracias!  ¿Preguntas?", 0),
    ])

    salida = "presentacion/Capacidad_Portante.pptx"
    prs.save(salida)
    print(f"Presentación generada: {salida}")
    print(f"Total de diapositivas: {len(prs.slides.__iter__.__self__._sldIdLst)}")


if __name__ == "__main__":
    build()
