# -*- coding: utf-8 -*-
import streamlit as st
import json
from datetime import date
import calendar

# ─── Configuración de página ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Previplan — Generador de Parrilla",
    page_icon="📅",
    layout="wide",
)

MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
         "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

PILARES_DEFAULT = [
    "Educativo",
    "Problema/solución",
    "RTB y confianza",
    "Comunidad y alianzas",
    "Previplan",
]

FORMATOS = ["Reel","Carrusel","Stories","Post estático","Video largo","Short"]
REDES    = ["Ig","Ig + Fb","Yt","Fb"]

HASHTAGS_PILAR = {
    "Educativo":            "#SaludPreviplan #Prevencion #Bienestar",
    "Problema/solución":    "#CosasQueDesesperan #TuSaludNoDaEspera",
    "RTB y confianza":      "#TuSaludNoDaEspera #SomosPrevisalud",
    "Comunidad y alianzas": "#Previplan #AliadosDeSalud",
    "Previplan":            "#Previplan #MembresiaDeSalud #AccesoSalud",
}

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

Cada pieza debe incluir: objetivo, audiencia, mensaje principal, insight emocional, CTA, formato y canal.

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
    fechas = []
    for d in range(1, dias+1):
        dt = date(año, mes_num, d)
        if dt.weekday() <= 5:
            fechas.append(dt)
    return fechas

def llamar_groq(prompt, api_key, model="llama-3.3-70b-versatile"):
    try:
        import requests
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": SISTEMA_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            "temperature": 0.75,
            "max_tokens": 1200,
        }
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                          headers=headers, json=body, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[Error Groq: {e}]"

def prompt_para_formato(fmt, pilar, subtema, vocero):
    fmt = fmt.lower()
    if "reel" in fmt:
        return f"""Guion REEL Instagram (30-45 seg).
Pilar: {pilar} | Tema: {subtema} | Vocero: {vocero}

GANCHO (3 seg): [frase que detenga el scroll]
DESARROLLO (20-30 seg): [3-4 puntos numerados]
CIERRE + CTA (5 seg): [cierre + Previplan $50.000/3 meses]
---
CTA engagement: [pregunta para comentarios]
NOTAS: subtítulos grandes, logo Previplan al final."""
    elif "carrusel" in fmt:
        n = 6 if pilar == "Educativo" else 5
        return f"""Carrusel Instagram ({n} láminas).
Pilar: {pilar} | Tema: {subtema}
LÁMINA 1: Gancho + "Desliza →"
LÁMINAS 2-{n-1}: Una idea por lámina
LÁMINA {n}: Cierre + CTA Previplan
NOTAS: colores corporativos, formato 1:1."""
    elif "stories" in fmt:
        return f"""4 Stories Instagram.
Pilar: {pilar} | Tema: {subtema}
H1: Gancho | H2: Punto clave | H3: Solución Previplan | H4: CTA link bio"""
    elif "video largo" in fmt:
        return f"""Video YouTube 10-15 min.
Tema: {subtema} | Vocero: {vocero}
INTRO (1-2 min) | CONTENIDO (7-10 min, 5 bloques) | CIERRE + CTA Previplan"""
    elif "short" in fmt:
        return f"""Short YouTube máx 60 seg.
Tema: {subtema}
0-3s GANCHO | 3-45s CONTENIDO (3 puntos) | 45-60s CTA Previplan"""
    else:
        return f"""Post estático Instagram.
Pilar: {pilar} | Tema: {subtema}
COPY IMAGEN: título + subtítulo + CTA
CAPTION: 3-4 párrafos. Precio: $50.000/3 meses."""

def distribuir_piezas(ideas, pilares_config, ig_total, fechas):
    piezas = []
    ideas_por_pilar = {}
    for idea in ideas:
        ideas_por_pilar.setdefault(idea["pilar"], []).append(idea)

    fecha_idx = 0
    for pc in pilares_config:
        pilar = pc["pilar"]
        n     = pc["n"]
        banco = ideas_por_pilar.get(pilar, [])
        for i in range(n):
            idea = banco[i % len(banco)] if banco else {"subtema": f"Contenido {pilar}", "formato": "Reel", "red": "Ig", "vocero": "General - marca"}
            f = fechas[fecha_idx % len(fechas)] if fechas else date.today()
            fecha_idx += 1
            piezas.append({
                "pilar":   pilar,
                "subtema": idea.get("subtema",""),
                "formato": idea.get("formato","Reel"),
                "red":     idea.get("red","Ig"),
                "vocero":  idea.get("vocero","General - marca"),
                "fecha":   f,
                "status":  "Por planear",
                "guion":   "",
                "caption": "",
            })
    return piezas

# ─── Sidebar — Configuración ──────────────────────────────────────────────────
with st.sidebar:
    st.image("https://i.imgur.com/placeholder.png", width=160)  # logo placeholder
    st.title("⚙️ Configuración")

    st.subheader("Período")
    mes_sel  = st.selectbox("Mes", MESES, index=date.today().month - 1)
    año_sel  = st.number_input("Año", value=date.today().year, min_value=2024, max_value=2030, step=1)
    ig_total = st.number_input("Piezas Instagram / mes", value=20, min_value=5, max_value=60, step=1)

    st.subheader("🔑 API Key Groq")
    groq_key = st.text_input("Groq API Key", type="password",
                              placeholder="gsk_...",
                              help="Obtén tu key gratis en console.groq.com/keys")

    st.subheader("📊 Google Sheets")
    sheet_id = st.text_input("ID del Spreadsheet",
                              placeholder="1AihVeH-VAVT8RxoRubK6gaeWJTOhg4kzrG3dgu6CHMg",
                              help="El ID está en la URL de tu Google Sheet")

    st.subheader("📌 Pilares y distribución")
    pilares_config = []
    total_piezas   = 0
    for p in PILARES_DEFAULT:
        col1, col2 = st.columns([3,1])
        with col1:
            st.markdown(f"**{p}**")
        with col2:
            n = st.number_input("", min_value=0, max_value=20, value=4, key=f"n_{p}", label_visibility="collapsed")
        pilares_config.append({"pilar": p, "n": n})
        total_piezas += n
    if total_piezas != ig_total:
        st.warning(f"Total asignado: {total_piezas} ≠ {ig_total} configuradas")

# ─── Main — Banco de Ideas ───────────────────────────────────────────────────
st.title("📅 Previplan — Generador de Parrilla")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["💡 Banco de Ideas", "📋 Parrilla", "✍️ Guiones"])

with tab1:
    st.subheader("Banco de Ideas")
    st.caption("Agrega las ideas para el mes. La parrilla se distribuirá automáticamente.")

    if "ideas" not in st.session_state:
        st.session_state.ideas = []

    with st.expander("➕ Agregar idea", expanded=len(st.session_state.ideas) == 0):
        c1, c2, c3 = st.columns(3)
        with c1:
            idea_pilar   = st.selectbox("Pilar", PILARES_DEFAULT, key="idea_pilar")
            idea_subtema = st.text_input("Subtema / Idea principal", key="idea_subtema")
        with c2:
            idea_formato = st.selectbox("Formato", FORMATOS, key="idea_fmt")
            idea_red     = st.selectbox("Red", REDES, key="idea_red")
        with c3:
            idea_vocero  = st.text_input("Vocero", value="General - marca", key="idea_vocero")

        if st.button("Agregar idea ✓", type="primary"):
            if idea_subtema.strip():
                st.session_state.ideas.append({
                    "pilar":   idea_pilar,
                    "subtema": idea_subtema.strip(),
                    "formato": idea_formato,
                    "red":     idea_red,
                    "vocero":  idea_vocero or "General - marca",
                })
                st.success("Idea agregada.")
                st.rerun()
            else:
                st.error("Escribe el subtema.")

    if st.session_state.ideas:
        st.markdown(f"**{len(st.session_state.ideas)} ideas en el banco**")
        for i, idea in enumerate(st.session_state.ideas):
            c1, c2, c3, c4 = st.columns([3,2,2,1])
            c1.write(f"**{idea['subtema']}**")
            c2.write(idea["pilar"])
            c3.write(f"{idea['formato']} · {idea['red']}")
            if c4.button("🗑️", key=f"del_{i}"):
                st.session_state.ideas.pop(i)
                st.rerun()
    else:
        st.info("Aún no hay ideas. Agrega al menos una por pilar.")

with tab2:
    st.subheader(f"Parrilla — {mes_sel} {int(año_sel)}")

    col_gen, col_clear = st.columns([2,1])
    with col_gen:
        generar_btn = st.button("🚀 Generar parrilla", type="primary",
                                disabled=len(st.session_state.ideas) == 0)
    with col_clear:
        if st.button("🗑️ Limpiar"):
            st.session_state.pop("piezas", None)
            st.rerun()

    if generar_btn:
        mes_num = MESES.index(mes_sel) + 1
        fechas  = generar_fechas(int(año_sel), mes_num)
        piezas  = distribuir_piezas(
            st.session_state.ideas,
            pilares_config,
            int(ig_total),
            fechas,
        )
        st.session_state.piezas = piezas
        st.success(f"✅ {len(piezas)} piezas generadas.")

    if "piezas" in st.session_state and st.session_state.piezas:
        piezas = st.session_state.piezas

        # Tabla resumen
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
        st.subheader("✍️ Generar guiones con IA")
        if not groq_key:
            st.warning("Ingresa tu Groq API Key en el panel izquierdo para generar guiones.")
        else:
            if st.button("🤖 Generar todos los guiones", type="primary"):
                progress = st.progress(0, text="Generando guiones...")
                for idx, p in enumerate(piezas):
                    prompt = prompt_para_formato(p["formato"], p["pilar"], p["subtema"], p["vocero"])
                    p["guion"] = llamar_groq(prompt, groq_key)
                    lineas = [l.strip() for l in p["guion"].split("\n") if l.strip() and len(l)>20 and not l.isupper()]
                    p["caption"] = " ".join(lineas[:3])[:280]
                    progress.progress((idx+1)/len(piezas), text=f"Generando {idx+1}/{len(piezas)}...")
                st.session_state.piezas = piezas
                st.success("✅ Guiones generados. Ve a la pestaña Guiones.")
                progress.empty()

        # Subir a Sheets
        st.markdown("---")
        st.subheader("📊 Subir a Google Sheets")
        if not sheet_id:
            st.warning("Ingresa el ID de tu Google Sheet en el panel izquierdo.")
        else:
            if st.button("⬆️ Subir parrilla a Google Sheets"):
                st.info("Para subir a Sheets necesitas el archivo credentials.json de tu cuenta de servicio Google. Consulta la documentación de configuración.")

with tab3:
    st.subheader("Guiones generados")
    if "piezas" not in st.session_state or not any(p.get("guion") for p in st.session_state.piezas):
        st.info("Genera los guiones desde la pestaña Parrilla.")
    else:
        piezas = st.session_state.piezas
        for i, p in enumerate(piezas):
            if p.get("guion"):
                with st.expander(f"#{i+1} · {p['pilar']} · {p['formato']} · {p['subtema'][:60]}"):
                    st.markdown(f"**Fecha:** {p['fecha'].strftime('%d %B %Y')} · **Red:** {p['red']} · **Vocero:** {p['vocero']}")
                    st.text_area("Guión", value=p["guion"], height=300, key=f"g_{i}")
                    st.text_area("Caption", value=p.get("caption",""), height=80, key=f"c_{i}")
                    ht = HASHTAGS_PILAR.get(p["pilar"],"") + " #TuSaludNoDaEspera #Previplan #Previsalud"
                    st.code(ht, language=None)
