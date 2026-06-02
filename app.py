# -*- coding: utf-8 -*-
import streamlit as st
from datetime import date
import calendar

st.set_page_config(
    page_title="Previplan — Generador de Parrilla",
    page_icon="📅",
    layout="wide",
)

MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
         "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

FORMATOS = ["Reel","Carrusel","Stories","Post estático","Video largo","Short"]
REDES    = ["Ig","Ig + Fb","Yt","Fb"]

PILARES_DEFAULT = [
    {"nombre": "Educativo",           "hashtags": "#SaludPreviplan #Prevencion #Bienestar"},
    {"nombre": "Problema/solución",   "hashtags": "#CosasQueDesesperan #TuSaludNoDaEspera"},
    {"nombre": "RTB y confianza",     "hashtags": "#TuSaludNoDaEspera #SomosPrevisalud"},
    {"nombre": "Comunidad y alianzas","hashtags": "#Previplan #AliadosDeSalud"},
    {"nombre": "Previplan",           "hashtags": "#Previplan #MembresiaDeSalud #AccesoSalud"},
]

SISTEMA_PROMPT = """Eres un consultor senior de marketing estratégico especializado en marcas de salud.
Trabajas para Previplan, una membresía médica colombiana que ofrece citas con especialistas
en 3 días o menos, por $50.000 al trimestre, para ti y hasta 4 beneficiarios,
con el respaldo de Previsalud.

EXPERIENCIA:
Eres experto en parrillas de contenido, calendarios editoriales, campañas educativas,
campañas de conversión, campañas de activación, campañas de fidelización, marketing relacional,
storytelling, copywriting emocional, redes sociales, WhatsApp Marketing, email marketing,
blogs, landing pages, video marketing y automatización de contenidos.

METODOLOGÍA:
Antes de construir cualquier pieza analiza:
- Qué quiere lograr la marca con este contenido.
- Qué necesita realmente la audiencia.
- Qué emoción moviliza la acción.
- Qué barreras pueden impedir la conversión.
- Qué mensaje tiene mayor probabilidad de generar respuesta.

ENFOQUE COMERCIAL:
Siempre identifica oportunidades para generar demanda, incrementar conversiones,
activar usuarios, mejorar retención y aumentar el Lifetime Value del cliente.
Equilibra valor para el usuario, credibilidad médica e impacto comercial.

ESTILO DE COMUNICACIÓN:
Humano, cercano, empático, claro, inspirador y profesional.
Conecta primero con la emoción, luego con el beneficio racional.
Nunca escribas contenido frío ni excesivamente técnico.
Idioma: español colombiano natural. Sin asteriscos ni markdown en el guion.
Siempre termina con un CTA claro hacia Previplan ($50.000 por 3 meses)."""

# ─── Helpers ─────────────────────────────────────────────────────────────────
def generar_fechas(año, mes_num):
    _, dias = calendar.monthrange(año, mes_num)
    return [date(año, mes_num, d) for d in range(1, dias+1)
            if date(año, mes_num, d).weekday() <= 5]

def llamar_groq(prompt, api_key):
    try:
        import requests
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": SISTEMA_PROMPT},
                    {"role": "user",   "content": prompt},
                ],
                "temperature": 0.75,
                "max_tokens": 1200,
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[Error Groq: {e}]"

def prompt_para_formato(fmt, pilar, subtema, vocero, contexto=""):
    fmt = fmt.lower()
    ctx = f"\nCONTEXTO DEL MES: {contexto.strip()}" if contexto.strip() else ""
    base = f"Pilar: {pilar} | Tema: {subtema} | Vocero: {vocero}{ctx}"
    if "reel" in fmt:
        return f"""Guion REEL Instagram (30-45 seg).
{base}

GANCHO (3 seg): [frase que detenga el scroll]
DESARROLLO (20-30 seg): [3-4 puntos numerados concretos]
CIERRE + CTA (5 seg): [cierre + Previplan $50.000/3 meses]
---
CTA engagement: [pregunta para comentarios]
NOTAS DE PRODUCCIÓN: subtítulos grandes, logo Previplan al final."""
    elif "carrusel" in fmt:
        n = 6 if pilar == "Educativo" else 5
        return f"""Carrusel Instagram ({n} láminas).
{base}
LÁMINA 1: Gancho + "Desliza →"
LÁMINAS 2 a {n-1}: Una idea clave por lámina (título + 2 líneas)
LÁMINA {n}: Cierre + CTA Previplan
NOTAS: colores corporativos, formato 1:1."""
    elif "stories" in fmt:
        return f"""4 Stories Instagram.
{base}
H1: Gancho | H2: Punto clave | H3: Solución Previplan | H4: CTA link bio
NOTAS: 9:16, texto grande, máx 15 seg cada una."""
    elif "video largo" in fmt:
        return f"""Video YouTube 10-15 min.
{base}
INTRO (1-2 min): gancho + promesa
CONTENIDO (7-10 min): 5 bloques con ejemplos concretos
CIERRE (1-2 min): resumen + CTA Previplan + suscripción"""
    elif "short" in fmt:
        return f"""Short YouTube máx 60 seg.
{base}
0-3s GANCHO | 3-45s CONTENIDO (3 puntos) | 45-60s CTA Previplan"""
    else:
        return f"""Post estático Instagram.
{base}
COPY IMAGEN: título gancho + subtítulo + CTA "link en bio"
CAPTION: 3-4 párrafos humanos. Precio: $50.000/3 meses.
DISEÑO: logo Previplan, paleta corporativa, 1080x1080px."""

# ─── Session state inicial ────────────────────────────────────────────────────
if "pilares" not in st.session_state:
    st.session_state.pilares = [
        {
            "nombre":   p["nombre"],
            "hashtags": p["hashtags"],
            "n":        4,
            "subtemas": [],   # lista de {"texto", "formato", "red", "vocero"}
        }
        for p in PILARES_DEFAULT
    ]

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Configuración")

    st.subheader("Período")
    mes_sel = st.selectbox("Mes", MESES, index=date.today().month - 1)
    año_sel = st.number_input("Año", value=date.today().year, min_value=2024, max_value=2030, step=1)

    st.subheader("🔑 Groq API Key")
    groq_key = st.text_input("API Key", type="password", placeholder="gsk_...")

    st.subheader("📝 Contexto del mes")
    contexto_mes = st.text_area(
        "Eventos, fechas clave, campañas...",
        placeholder="Ej: Julio es el mes de la salud masculina. Día del padre el 20. Lanzamos Check-Up para hombres.",
        height=110,
    )

    st.markdown("---")
    total_piezas = sum(p["n"] for p in st.session_state.pilares)
    st.metric("Total piezas", total_piezas)

# ─── Main ─────────────────────────────────────────────────────────────────────
st.title("📅 Previplan — Generador de Parrilla")
st.markdown("---")

tab_pilares, tab_parrilla, tab_guiones = st.tabs([
    "📌 Pilares y Subtemas",
    "📋 Parrilla",
    "✍️ Guiones",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PILARES Y SUBTEMAS
# ══════════════════════════════════════════════════════════════════════════════
with tab_pilares:

    # ── Agregar / quitar pilares ──────────────────────────────────────────────
    col_add, col_space = st.columns([2, 3])
    with col_add:
        with st.expander("➕ Agregar nuevo pilar"):
            nuevo_pilar = st.text_input("Nombre del pilar", key="nuevo_pilar_nombre")
            if st.button("Agregar pilar", type="primary"):
                if nuevo_pilar.strip():
                    nombres = [p["nombre"] for p in st.session_state.pilares]
                    if nuevo_pilar.strip() not in nombres:
                        st.session_state.pilares.append({
                            "nombre":   nuevo_pilar.strip(),
                            "hashtags": "",
                            "n":        4,
                            "subtemas": [],
                        })
                        st.success(f"Pilar '{nuevo_pilar.strip()}' agregado.")
                        st.rerun()
                    else:
                        st.warning("Ya existe un pilar con ese nombre.")
                else:
                    st.error("Escribe el nombre del pilar.")

    st.markdown("---")

    # ── Configurar cada pilar ─────────────────────────────────────────────────
    for pi, pilar in enumerate(st.session_state.pilares):
        with st.expander(f"**{pilar['nombre']}** — {pilar['n']} piezas · {len(pilar['subtemas'])} subtemas", expanded=False):

            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                nuevo_nombre = st.text_input("Nombre del pilar", value=pilar["nombre"], key=f"pnombre_{pi}")
                if nuevo_nombre != pilar["nombre"]:
                    st.session_state.pilares[pi]["nombre"] = nuevo_nombre
            with col2:
                nuevo_n = st.number_input("Piezas/mes", min_value=0, max_value=30, value=pilar["n"], key=f"pn_{pi}")
                st.session_state.pilares[pi]["n"] = nuevo_n
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                if len(st.session_state.pilares) > 1:
                    if st.button("🗑️ Eliminar pilar", key=f"del_pilar_{pi}"):
                        st.session_state.pilares.pop(pi)
                        st.rerun()

            nuevo_ht = st.text_input("Hashtags del pilar", value=pilar["hashtags"], key=f"pht_{pi}")
            st.session_state.pilares[pi]["hashtags"] = nuevo_ht

            st.markdown("##### Subtemas")
            st.caption("Define los subtemas para este pilar. La parrilla rotará entre ellos.")

            # Mostrar subtemas existentes
            for si, sub in enumerate(pilar["subtemas"]):
                sc1, sc2, sc3, sc4, sc5 = st.columns([3, 2, 1, 2, 1])
                sc1.write(f"**{sub['texto']}**")
                sc2.write(sub["formato"])
                sc3.write(sub["red"])
                sc4.write(sub["vocero"])
                if sc5.button("🗑️", key=f"del_sub_{pi}_{si}"):
                    st.session_state.pilares[pi]["subtemas"].pop(si)
                    st.rerun()

            # Formulario para agregar subtema
            with st.form(key=f"form_sub_{pi}", clear_on_submit=True):
                fc1, fc2, fc3, fc4 = st.columns([3, 2, 1, 2])
                with fc1:
                    sub_texto = st.text_input("Subtema", placeholder="Ej: Salud hormonal femenina", key=f"stxt_{pi}")
                with fc2:
                    sub_fmt = st.selectbox("Formato", FORMATOS, key=f"sfmt_{pi}")
                with fc3:
                    sub_red = st.selectbox("Red", REDES, key=f"sred_{pi}")
                with fc4:
                    sub_vocero = st.text_input("Vocero", value="General - marca", key=f"svoc_{pi}")
                submitted = st.form_submit_button("Agregar subtema ✓", type="primary")
                if submitted:
                    if sub_texto.strip():
                        st.session_state.pilares[pi]["subtemas"].append({
                            "texto":   sub_texto.strip(),
                            "formato": sub_fmt,
                            "red":     sub_red,
                            "vocero":  sub_vocero or "General - marca",
                        })
                        st.rerun()
                    else:
                        st.error("Escribe el subtema.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PARRILLA
# ══════════════════════════════════════════════════════════════════════════════
with tab_parrilla:
    st.subheader(f"Parrilla — {mes_sel} {int(año_sel)}")

    pilares_con_subtemas = [p for p in st.session_state.pilares if p["subtemas"] and p["n"] > 0]

    if not pilares_con_subtemas:
        st.warning("Ve a **Pilares y Subtemas** y agrega al menos un subtema a cada pilar antes de generar.")
    else:
        col_gen, col_clear = st.columns([2, 1])
        with col_gen:
            generar_btn = st.button("🚀 Generar parrilla", type="primary")
        with col_clear:
            if st.button("🗑️ Limpiar parrilla"):
                st.session_state.pop("piezas", None)
                st.rerun()

        if generar_btn:
            mes_num = MESES.index(mes_sel) + 1
            fechas  = generar_fechas(int(año_sel), mes_num)
            piezas  = []
            fecha_idx = 0
            for pilar in st.session_state.pilares:
                if not pilar["subtemas"] or pilar["n"] == 0:
                    continue
                subtemas = pilar["subtemas"]
                for i in range(pilar["n"]):
                    sub = subtemas[i % len(subtemas)]
                    f   = fechas[fecha_idx % len(fechas)]
                    fecha_idx += 1
                    piezas.append({
                        "pilar":    pilar["nombre"],
                        "hashtags": pilar["hashtags"],
                        "subtema":  sub["texto"],
                        "formato":  sub["formato"],
                        "red":      sub["red"],
                        "vocero":   sub["vocero"],
                        "fecha":    f,
                        "status":   "Por planear",
                        "guion":    "",
                        "caption":  "",
                    })
            st.session_state.piezas      = piezas
            st.session_state.contexto_guardado = contexto_mes
            st.success(f"✅ {len(piezas)} piezas generadas.")
            if contexto_mes.strip():
                st.info(f"📝 Contexto: {contexto_mes[:120]}...")

        if "piezas" in st.session_state and st.session_state.piezas:
            piezas = st.session_state.piezas
            import pandas as pd
            df = pd.DataFrame([{
                "Fecha":   p["fecha"].strftime("%d %b"),
                "Pilar":   p["pilar"],
                "Formato": p["formato"],
                "Red":     p["red"],
                "Subtema": p["subtema"],
                "Vocero":  p["vocero"],
                "Status":  p["status"],
            } for p in piezas])
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("🤖 Generar guiones con IA")
            if not groq_key:
                st.warning("Ingresa tu Groq API Key en el panel izquierdo.")
            else:
                if st.button("Generar todos los guiones", type="primary"):
                    ctx = st.session_state.get("contexto_guardado", "")
                    progress = st.progress(0, text="Generando guiones...")
                    for idx, p in enumerate(piezas):
                        prompt = prompt_para_formato(p["formato"], p["pilar"], p["subtema"], p["vocero"], ctx)
                        p["guion"] = llamar_groq(prompt, groq_key)
                        lineas = [l.strip() for l in p["guion"].split("\n") if l.strip() and len(l) > 20 and not l.isupper()]
                        p["caption"] = " ".join(lineas[:3])[:280]
                        progress.progress((idx+1)/len(piezas), text=f"Generando {idx+1}/{len(piezas)}...")
                    st.session_state.piezas = piezas
                    progress.empty()
                    st.success("✅ Guiones generados. Ve a la pestaña Guiones.")

            st.markdown("---")
            st.subheader("📊 Subir a Google Sheets")
            if st.text_input("ID del Spreadsheet", placeholder="1AihVeH-...", key="sheet_id_tab2"):
                st.info("Configuración de Google Sheets próximamente.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — GUIONES
# ══════════════════════════════════════════════════════════════════════════════
with tab_guiones:
    st.subheader("Guiones generados")
    piezas = st.session_state.get("piezas", [])
    con_guion = [p for p in piezas if p.get("guion")]

    if not con_guion:
        st.info("Genera los guiones desde la pestaña Parrilla.")
    else:
        st.markdown(f"**{len(con_guion)} guiones listos**")
        for i, p in enumerate(piezas):
            if not p.get("guion"):
                continue
            ht = p.get("hashtags","") + " #TuSaludNoDaEspera #Previplan #Previsalud"
            with st.expander(f"#{i+1} · {p['pilar']} · {p['formato']} · {p['subtema'][:55]}"):
                st.markdown(f"📅 **{p['fecha'].strftime('%d %B %Y')}** · 📱 {p['red']} · 🎤 {p['vocero']}")
                st.text_area("Guión completo", value=p["guion"], height=320, key=f"g_{i}")
                st.text_area("Caption", value=p.get("caption",""), height=90, key=f"c_{i}")
                st.code(ht.strip(), language=None)
