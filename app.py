# -*- coding: utf-8 -*-
import streamlit as st
from datetime import date
import calendar
import json

st.set_page_config(
    page_title="Previplan — Generador de Parrilla",
    page_icon="📅",
    layout="wide",
)

MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
         "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
FORMATOS = ["Reel","Carrusel","Stories","Post estático","Video largo","Short"]
REDES    = ["Ig","Ig + Fb","Yt","Fb"]
STATUS_OPTS = ["Por planear","En producción","En post-producción","En revisión","Aprobado","Programado","Publicado"]

PILARES_DEFAULT = [
    {"nombre": "Educativo",            "hashtags": "#SaludPreviplan #Prevencion #Bienestar"},
    {"nombre": "Problema/solución",    "hashtags": "#CosasQueDesesperan #TuSaludNoDaEspera"},
    {"nombre": "RTB y confianza",      "hashtags": "#TuSaludNoDaEspera #SomosPrevisalud"},
    {"nombre": "Comunidad y alianzas", "hashtags": "#Previplan #AliadosDeSalud"},
    {"nombre": "Previplan",            "hashtags": "#Previplan #MembresiaDeSalud #AccesoSalud"},
]

SISTEMA_PROMPT = """Eres un consultor senior de marketing estratégico especializado en marcas de salud.
Trabajas para Previplan, una membresía médica colombiana que ofrece citas con especialistas
en 3 días o menos, por $50.000 al trimestre, para ti y hasta 4 beneficiarios,
con el respaldo de Previsalud.

EXPERIENCIA: parrillas de contenido, calendarios editoriales, campañas educativas, campañas de
conversión y activación, marketing relacional, storytelling, copywriting emocional, redes sociales,
video marketing y automatización de contenidos.

METODOLOGÍA: Antes de construir cualquier pieza analiza qué quiere lograr la marca, qué necesita
la audiencia, qué emoción moviliza la acción, qué barreras impiden la conversión y qué mensaje
tiene mayor probabilidad de generar respuesta.

ESTILO: Humano, cercano, empático, claro, inspirador. Conecta primero con la emoción, luego con
el beneficio racional. Español colombiano natural. Sin asteriscos ni markdown.
Siempre termina con un CTA hacia Previplan ($50.000 por 3 meses)."""

# ─── Groq ─────────────────────────────────────────────────────────────────────
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
                "temperature": 0.8,
                "max_tokens": 1400,
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[Error: {e}]"

def generar_pieza_ia(pilar, subtema_amplio, formato, vocero, contexto, api_key):
    """La IA recibe el subtema amplio y genera ángulo, producción, caption y CTA."""
    fmt = formato.lower()

    if "reel" in fmt:
        instruccion_prod = "Guion de Reel (30-45 seg): GANCHO (3 seg) / DESARROLLO 3-4 puntos / CIERRE + CTA"
    elif "carrusel" in fmt:
        instruccion_prod = "Estructura de Carrusel (5-6 láminas): PORTADA / LÁMINAS con una idea cada una / CIERRE"
    elif "stories" in fmt:
        instruccion_prod = "4 Stories: Historia 1 gancho / Historia 2 desarrollo / Historia 3 solución / Historia 4 CTA"
    elif "video largo" in fmt:
        instruccion_prod = "Guion YouTube (10-15 min): INTRO / BLOQUES DE CONTENIDO (5 bloques) / CIERRE"
    elif "short" in fmt:
        instruccion_prod = "Short YouTube (60 seg): GANCHO / 3 puntos rápidos / CTA"
    else:
        instruccion_prod = "Post estático: COPY DE IMAGEN (título + subtítulo) / CAPTION completo"

    ctx = f"\nCONTEXTO DEL MES: {contexto}" if contexto.strip() else ""

    prompt = f"""Pilar de contenido: {pilar}
Subtema amplio: {subtema_amplio}
Formato: {formato}
Vocero: {vocero}{ctx}

Tu tarea es desarrollar UNA pieza de contenido concreta para Previplan. Responde en este formato exacto:

ANGULO:
[Un título/ángulo creativo y específico para esta pieza. Ej: "5 señales hormonales que normalizas y no deberías" o "Mitos y verdades sobre la salud femenina que nadie te dijo". Debe ser llamativo y concreto.]

PRODUCCION:
[{instruccion_prod}. Desarrolla el contenido completo listo para producir. Sé específico, no genérico.]

CAPTION:
[Caption completo para la publicación. 3-4 párrafos cortos. Tono humano y cercano. Incluye el precio $50.000 por 3 meses y llamado a acción al final.]

CTA:
[Una frase corta y directa de llamado a la acción. Ej: "Comenta QUIERO SABER MÁS" o "Guarda este video, lo vas a necesitar".]"""

    respuesta = llamar_groq(prompt, api_key)

    # Parsear la respuesta
    def extraer(clave, texto):
        try:
            inicio = texto.index(f"{clave}:") + len(f"{clave}:")
            partes = texto[inicio:]
            claves_resto = ["ANGULO:", "PRODUCCION:", "CAPTION:", "CTA:"]
            fin = len(partes)
            for k in claves_resto:
                if k != f"{clave}:" and k in partes:
                    fin = min(fin, partes.index(k))
            return partes[:fin].strip()
        except:
            return ""

    return {
        "angulo":     extraer("ANGULO", respuesta),
        "produccion": extraer("PRODUCCION", respuesta),
        "caption":    extraer("CAPTION", respuesta),
        "cta":        extraer("CTA", respuesta),
        "raw":        respuesta,
    }

def generar_fechas(año, mes_num):
    _, dias = calendar.monthrange(año, mes_num)
    return [date(año, mes_num, d) for d in range(1, dias+1)
            if date(año, mes_num, d).weekday() <= 5]

# ─── Session state ────────────────────────────────────────────────────────────
if "pilares" not in st.session_state:
    st.session_state.pilares = [
        {"nombre": p["nombre"], "hashtags": p["hashtags"], "n": 4, "subtemas": []}
        for p in PILARES_DEFAULT
    ]
if "piezas" not in st.session_state:
    st.session_state.piezas = []

# ─── Sidebar ──────────────────────────────────────────────────────────────────
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
    total = sum(p["n"] for p in st.session_state.pilares)
    st.metric("Total piezas configuradas", total)

# ─── Tabs ─────────────────────────────────────────────────────────────────────
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
    st.caption("Define tus pilares y los subtemas amplios para cada uno. La IA generará el ángulo concreto, guión, caption y CTA de cada pieza.")

    # Agregar pilar
    with st.expander("➕ Agregar nuevo pilar"):
        np_nombre = st.text_input("Nombre del pilar", key="np_nombre")
        np_ht     = st.text_input("Hashtags (opcional)", key="np_ht")
        if st.button("Crear pilar", type="primary"):
            if np_nombre.strip():
                nombres = [p["nombre"] for p in st.session_state.pilares]
                if np_nombre.strip() not in nombres:
                    st.session_state.pilares.append({"nombre": np_nombre.strip(), "hashtags": np_ht.strip(), "n": 4, "subtemas": []})
                    st.rerun()
                else:
                    st.warning("Ya existe ese pilar.")

    st.markdown("---")

    for pi, pilar in enumerate(st.session_state.pilares):
        n_sub = len(pilar["subtemas"])
        with st.expander(f"**{pilar['nombre']}** — {pilar['n']} piezas/mes · {n_sub} subtema{'s' if n_sub!=1 else ''}", expanded=False):

            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                nn = st.text_input("Nombre", value=pilar["nombre"], key=f"pn_{pi}")
                st.session_state.pilares[pi]["nombre"] = nn
            with c2:
                nv = st.number_input("Piezas/mes", min_value=0, max_value=30, value=pilar["n"], key=f"pnum_{pi}")
                st.session_state.pilares[pi]["n"] = nv
            with c3:
                st.markdown("<br>", unsafe_allow_html=True)
                if len(st.session_state.pilares) > 1:
                    if st.button("🗑️ Eliminar", key=f"delp_{pi}"):
                        st.session_state.pilares.pop(pi)
                        st.rerun()

            nh = st.text_input("Hashtags", value=pilar["hashtags"], key=f"pht_{pi}")
            st.session_state.pilares[pi]["hashtags"] = nh

            st.markdown("##### Subtemas")
            st.caption("Escribe temas amplios. La IA los convierte en piezas concretas.")

            # Listar subtemas
            for si, sub in enumerate(pilar["subtemas"]):
                sc1, sc2, sc3, sc4, sc5 = st.columns([3, 2, 1, 2, 1])
                sc1.markdown(f"**{sub['texto']}**")
                sc2.write(sub["formato"])
                sc3.write(sub["red"])
                sc4.write(sub["vocero"])
                if sc5.button("🗑️", key=f"dels_{pi}_{si}"):
                    st.session_state.pilares[pi]["subtemas"].pop(si)
                    st.rerun()

            # Formulario agregar subtema
            with st.form(key=f"fsub_{pi}", clear_on_submit=True):
                fa, fb, fc, fd = st.columns([3, 2, 1, 2])
                with fa:
                    st_txt = st.text_input("Subtema amplio", placeholder="Ej: Salud femenina", key=f"stxt_{pi}")
                with fb:
                    st_fmt = st.selectbox("Formato", FORMATOS, key=f"sfmt_{pi}")
                with fc:
                    st_red = st.selectbox("Red", REDES, key=f"sred_{pi}")
                with fd:
                    st_voc = st.text_input("Vocero", value="General - marca", key=f"svoc_{pi}")
                if st.form_submit_button("Agregar subtema ✓", type="primary"):
                    if st_txt.strip():
                        st.session_state.pilares[pi]["subtemas"].append({
                            "texto":   st_txt.strip(),
                            "formato": st_fmt,
                            "red":     st_red,
                            "vocero":  st_voc or "General - marca",
                        })
                        st.rerun()
                    else:
                        st.error("Escribe el subtema.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PARRILLA
# ══════════════════════════════════════════════════════════════════════════════
with tab_parrilla:
    st.subheader(f"Parrilla — {mes_sel} {int(año_sel)}")

    pilares_ok = [p for p in st.session_state.pilares if p["subtemas"] and p["n"] > 0]

    if not pilares_ok:
        st.warning("Ve a **Pilares y Subtemas** y agrega al menos un subtema antes de generar.")
    else:
        col_gen, col_ia, col_clear = st.columns([2, 2, 1])
        with col_gen:
            btn_estructura = st.button("📋 Generar estructura", type="primary",
                                       help="Crea la parrilla con fechas y subtemas. Sin IA.")
        with col_ia:
            btn_ia = st.button("🤖 Generar con IA (completo)", type="primary",
                               disabled=not groq_key,
                               help="Genera estructura + ángulo, producción, caption y CTA con IA.")
        with col_clear:
            if st.button("🗑️ Limpiar"):
                st.session_state.piezas = []
                st.rerun()

        # ── Generar solo estructura ──
        if btn_estructura or btn_ia:
            mes_num   = MESES.index(mes_sel) + 1
            fechas    = generar_fechas(int(año_sel), mes_num)
            piezas    = []
            fecha_idx = 0
            for pilar in st.session_state.pilares:
                if not pilar["subtemas"] or pilar["n"] == 0:
                    continue
                subtemas = pilar["subtemas"]
                for i in range(pilar["n"]):
                    sub = subtemas[i % len(subtemas)]
                    piezas.append({
                        "pilar":      pilar["nombre"],
                        "hashtags":   pilar["hashtags"],
                        "subtema":    sub["texto"],
                        "formato":    sub["formato"],
                        "red":        sub["red"],
                        "vocero":     sub["vocero"],
                        "fecha":      fechas[fecha_idx % len(fechas)],
                        "status":     "Por planear",
                        "angulo":     "",
                        "produccion": "",
                        "caption":    "",
                        "cta":        "",
                    })
                    fecha_idx += 1
            st.session_state.piezas = piezas
            st.session_state.ctx_guardado = contexto_mes

            # Si eligió IA, generamos todo
            if btn_ia:
                ctx = contexto_mes
                prog = st.progress(0, text="Generando con IA...")
                for idx, p in enumerate(piezas):
                    resultado = generar_pieza_ia(
                        p["pilar"], p["subtema"], p["formato"], p["vocero"], ctx, groq_key
                    )
                    p["angulo"]     = resultado["angulo"]
                    p["produccion"] = resultado["produccion"]
                    p["caption"]    = resultado["caption"]
                    p["cta"]        = resultado["cta"]
                    prog.progress((idx+1)/len(piezas), text=f"Pieza {idx+1}/{len(piezas)}: {p['subtema'][:40]}...")
                prog.empty()
                st.session_state.piezas = piezas
                st.success(f"✅ {len(piezas)} piezas generadas con IA.")
            else:
                st.success(f"✅ Estructura de {len(piezas)} piezas creada. Puedes generar los contenidos IA desde la pestaña Guiones.")

        # ── Mostrar parrilla ──
        if st.session_state.piezas:
            piezas = st.session_state.piezas
            st.markdown(f"**{len(piezas)} piezas** · {mes_sel} {int(año_sel)}")

            # Tabla con status editable
            for idx, p in enumerate(piezas):
                with st.container():
                    h1, h2, h3, h4, h5, h6 = st.columns([1.2, 2, 1.5, 1, 2, 2])
                    h1.markdown(f"**{p['fecha'].strftime('%d %b')}**")
                    h2.markdown(f"**{p['pilar']}**")
                    h3.write(p["formato"])
                    h4.write(p["red"])
                    h5.write(p["subtema"])

                    # Status desplegable
                    status_idx = STATUS_OPTS.index(p["status"]) if p["status"] in STATUS_OPTS else 0
                    nuevo_status = h6.selectbox(
                        "", STATUS_OPTS, index=status_idx,
                        key=f"status_{idx}", label_visibility="collapsed"
                    )
                    st.session_state.piezas[idx]["status"] = nuevo_status

                    if p.get("angulo"):
                        st.markdown(f"&nbsp;&nbsp;&nbsp;📌 *{p['angulo'][:100]}*")
                    st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — GUIONES
# ══════════════════════════════════════════════════════════════════════════════
with tab_guiones:
    st.subheader("Contenido detallado por pieza")
    piezas = st.session_state.piezas

    if not piezas:
        st.info("Genera la parrilla primero desde la pestaña Parrilla.")
    else:
        # Botón para generar IA solo en piezas sin contenido
        sin_contenido = [p for p in piezas if not p.get("angulo")]
        if sin_contenido and groq_key:
            if st.button(f"🤖 Generar IA para {len(sin_contenido)} piezas pendientes", type="primary"):
                ctx  = st.session_state.get("ctx_guardado", "")
                prog = st.progress(0, text="Generando...")
                done = 0
                for idx, p in enumerate(piezas):
                    if not p.get("angulo"):
                        resultado = generar_pieza_ia(p["pilar"], p["subtema"], p["formato"], p["vocero"], ctx, groq_key)
                        st.session_state.piezas[idx]["angulo"]     = resultado["angulo"]
                        st.session_state.piezas[idx]["produccion"] = resultado["produccion"]
                        st.session_state.piezas[idx]["caption"]    = resultado["caption"]
                        st.session_state.piezas[idx]["cta"]        = resultado["cta"]
                        done += 1
                        prog.progress(done/len(sin_contenido), text=f"Generando {done}/{len(sin_contenido)}...")
                prog.empty()
                st.success("✅ Listo.")
                st.rerun()
        elif not groq_key:
            st.warning("Ingresa tu Groq API Key en el panel izquierdo.")

        st.markdown("---")

        for idx, p in enumerate(piezas):
            label_color = "🟢" if p.get("angulo") else "⚪"
            titulo = p.get("angulo") or p["subtema"]
            with st.expander(f"{label_color} #{idx+1} · {p['pilar']} · {p['formato']} · {titulo[:60]}"):

                col_info, col_status = st.columns([4, 1])
                col_info.markdown(f"📅 **{p['fecha'].strftime('%d %B %Y')}** · 📱 {p['red']} · 🎤 {p['vocero']}")
                status_idx = STATUS_OPTS.index(p["status"]) if p["status"] in STATUS_OPTS else 0
                nuevo_st = col_status.selectbox("Status", STATUS_OPTS, index=status_idx, key=f"gst_{idx}")
                st.session_state.piezas[idx]["status"] = nuevo_st

                st.markdown(f"**Subtema amplio:** {p['subtema']}")

                if p.get("angulo"):
                    st.markdown(f"**📌 Ángulo / Título:** {p['angulo']}")
                    st.markdown("**🎬 Guía de Producción**")
                    prod = st.text_area("", value=p["produccion"], height=280, key=f"prod_{idx}", label_visibility="collapsed")
                    st.session_state.piezas[idx]["produccion"] = prod

                    st.markdown("**📝 Caption**")
                    cap = st.text_area("", value=p["caption"], height=140, key=f"cap_{idx}", label_visibility="collapsed")
                    st.session_state.piezas[idx]["caption"] = cap

                    st.markdown("**🎯 CTA**")
                    cta = st.text_input("", value=p["cta"], key=f"cta_{idx}", label_visibility="collapsed")
                    st.session_state.piezas[idx]["cta"] = cta

                    ht = p.get("hashtags","") + " #TuSaludNoDaEspera #Previplan #Previsalud"
                    st.code(ht.strip(), language=None)
                else:
                    st.info("Sin contenido IA aún. Genera desde el botón de arriba.")

                    # Generar solo esta pieza
                    if groq_key and st.button("🤖 Generar solo esta pieza", key=f"gen1_{idx}"):
                        ctx = st.session_state.get("ctx_guardado", "")
                        resultado = generar_pieza_ia(p["pilar"], p["subtema"], p["formato"], p["vocero"], ctx, groq_key)
                        st.session_state.piezas[idx]["angulo"]     = resultado["angulo"]
                        st.session_state.piezas[idx]["produccion"] = resultado["produccion"]
                        st.session_state.piezas[idx]["caption"]    = resultado["caption"]
                        st.session_state.piezas[idx]["cta"]        = resultado["cta"]
                        st.rerun()
