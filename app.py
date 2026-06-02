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

STATUS_OPTS = ["Por planear","En producción","En post-producción",
               "En revisión","Aprobado","Programado","Publicado"]

# ── Distribución estratégica de formatos y canales por pilar ─────────────────
# El sistema rota estos formatos automáticamente según el orden de las piezas
DISTRIBUCION_PILAR = {
    "Educativo":            ["Reel","Carrusel","Reel","Video largo","Carrusel","Stories","Reel","Post estático"],
    "Problema/solución":    ["Reel","Stories","Reel","Post estático","Stories","Reel"],
    "RTB y confianza":      ["Carrusel","Reel","Post estático","Reel","Carrusel"],
    "Comunidad y alianzas": ["Post estático","Reel","Carrusel","Post estático","Reel"],
    "Previplan":            ["Reel","Short","Carrusel","Reel","Post estático","Short"],
}
CANAL_POR_FORMATO = {
    "Reel":          "Ig + Fb",
    "Carrusel":      "Ig",
    "Video largo":   "Yt",
    "Short":         "Yt",
    "Stories":       "Ig",
    "Post estático": "Ig + Fb",
}

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
                "temperature": 0.85,
                "max_tokens": 1400,
            },
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[Error: {e}]"

def instruccion_produccion(fmt):
    fmt = fmt.lower()
    if "reel" in fmt:
        return "Guion de Reel (30-45 seg): GANCHO impactante (3 seg) / DESARROLLO con 3-4 puntos numerados / CIERRE + CTA"
    elif "carrusel" in fmt:
        return "Carrusel (5-6 láminas): LÁMINA 1 portada con gancho / LÁMINAS 2-5 una idea concreta cada una / LÁMINA final CTA"
    elif "stories" in fmt:
        return "4 Stories: H1 gancho + sticker encuesta / H2 punto clave + caja preguntas / H3 solución Previplan / H4 CTA link bio"
    elif "video largo" in fmt:
        return "Video YouTube 10-15 min: INTRO gancho + promesa / 5 BLOQUES de contenido con ejemplos / CIERRE + CTA + suscripción"
    elif "short" in fmt:
        return "Short YouTube 60 seg: GANCHO (3 seg) / 3 puntos rápidos / CTA Previplan"
    else:
        return "Post estático: COPY IMAGEN título gancho + subtítulo / CAPTION 3-4 párrafos humanos / CTA final"

def generar_pieza_ia(pilar, subtema, formato, vocero, contexto, angulos_usados, api_key):
    """Genera ángulo único, producción, caption y CTA. Evita repetir ángulos previos."""

    no_repetir = ""
    if angulos_usados:
        lista = "\n".join(f"- {a}" for a in angulos_usados)
        no_repetir = f"""
ÁNGULOS YA USADOS PARA ESTE SUBTEMA (NO repitas ni parafrasees ninguno):
{lista}

Debes crear un ángulo completamente diferente en enfoque, gancho y estructura narrativa."""

    ctx = f"\nCONTEXTO DEL MES: {contexto.strip()}" if contexto.strip() else ""

    prompt = f"""Pilar: {pilar}
Subtema amplio: {subtema}
Formato: {formato}
Vocero: {vocero}{ctx}{no_repetir}

Desarrolla UNA pieza de contenido concreta y original para Previplan.
Responde EXACTAMENTE con este formato (sin agregar nada antes ni después):

ANGULO:
[Título creativo y específico. Ej: "5 señales hormonales que normalizas y no deberías" o "Lo que nadie te dijo sobre la salud femenina después de los 30". Debe ser diferente a los ya usados.]

PRODUCCION:
[{instruccion_produccion(formato)}. Desarrolla el contenido COMPLETO listo para producir. Específico, concreto, sin frases genéricas.]

CAPTION:
[Caption completo para la red social. 3-4 párrafos cortos. Tono humano y cercano. Incluye precio $50.000 por 3 meses y llamado claro al final.]

CTA:
[Frase corta y directa. Ej: "Comenta QUIERO SABER MÁS" o "Guarda este video, lo vas a necesitar".]"""

    respuesta = llamar_groq(prompt, api_key)

    def extraer(clave, texto):
        try:
            inicio = texto.index(f"{clave}:") + len(f"{clave}:")
            partes = texto[inicio:]
            for k in ["ANGULO:", "PRODUCCION:", "CAPTION:", "CTA:"]:
                if k != f"{clave}:" and k in partes:
                    partes = partes[:partes.index(k)]
            return partes.strip()
        except:
            return ""

    return {
        "angulo":     extraer("ANGULO", respuesta),
        "produccion": extraer("PRODUCCION", respuesta),
        "caption":    extraer("CAPTION", respuesta),
        "cta":        extraer("CTA", respuesta),
    }

def generar_csv(piezas):
    import io, csv
    buf = io.StringIO()
    campos = ["Fecha","Pilar","Formato","Canal","Subtema","Ángulo / Título",
              "Producción","Caption","CTA","Hashtags","Vocero","Status"]
    writer = csv.DictWriter(buf, fieldnames=campos)
    writer.writeheader()
    for p in piezas:
        writer.writerow({
            "Fecha":           p["fecha"].strftime("%d/%m/%Y"),
            "Pilar":           p["pilar"],
            "Formato":         p["formato"],
            "Canal":           p["red"],
            "Subtema":         p["subtema"],
            "Ángulo / Título": p.get("angulo",""),
            "Producción":      p.get("produccion",""),
            "Caption":         p.get("caption",""),
            "CTA":             p.get("cta",""),
            "Hashtags":        (p.get("hashtags","") + " #TuSaludNoDaEspera #Previplan #Previsalud").strip(),
            "Vocero":          p.get("vocero",""),
            "Status":          p.get("status","Por planear"),
        })
    return buf.getvalue().encode("utf-8-sig")  # utf-8-sig abre bien en Excel

def generar_fechas(año, mes_num):
    _, dias = calendar.monthrange(año, mes_num)
    return [date(año, mes_num, d) for d in range(1, dias+1)
            if date(año, mes_num, d).weekday() <= 5]

def formato_para_pilar(pilar_nombre, indice):
    """Devuelve el formato estratégico según el pilar e índice de la pieza."""
    dist = DISTRIBUCION_PILAR.get(pilar_nombre)
    if not dist:
        # Si es un pilar personalizado, rotación genérica
        dist = ["Reel","Carrusel","Post estático","Reel","Stories"]
    return dist[indice % len(dist)]

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
    st.caption("Define tus pilares y subtemas amplios. El sistema distribuye formatos y canales estratégicamente. La IA genera el ángulo concreto de cada pieza.")

    with st.expander("➕ Agregar nuevo pilar"):
        np_nombre = st.text_input("Nombre del pilar", key="np_nombre")
        np_ht     = st.text_input("Hashtags (opcional)", key="np_ht")
        if st.button("Crear pilar", type="primary"):
            if np_nombre.strip():
                nombres = [p["nombre"] for p in st.session_state.pilares]
                if np_nombre.strip() not in nombres:
                    st.session_state.pilares.append({
                        "nombre": np_nombre.strip(), "hashtags": np_ht.strip(),
                        "n": 4, "subtemas": []
                    })
                    st.rerun()
                else:
                    st.warning("Ya existe ese pilar.")

    st.markdown("---")

    for pi, pilar in enumerate(st.session_state.pilares):
        n_sub = len(pilar["subtemas"])
        with st.expander(f"**{pilar['nombre']}** — {pilar['n']} piezas/mes · {n_sub} subtema{'s' if n_sub!=1 else ''}", expanded=False):

            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                nn = st.text_input("Nombre del pilar", value=pilar["nombre"], key=f"pn_{pi}")
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

            nh = st.text_input("Hashtags del pilar", value=pilar["hashtags"], key=f"pht_{pi}")
            st.session_state.pilares[pi]["hashtags"] = nh

            voc = st.text_input("Vocero por defecto", value=pilar.get("vocero","General - marca"), key=f"pvoc_{pi}")
            st.session_state.pilares[pi]["vocero"] = voc

            st.markdown("##### Subtemas")
            st.caption("Escribe el tema amplio. El sistema elige el formato y canal. La IA crea el ángulo específico.")

            for si, sub in enumerate(pilar["subtemas"]):
                sc1, sc2 = st.columns([5, 1])
                sc1.markdown(f"**{sub['texto']}**")
                if sc2.button("🗑️", key=f"dels_{pi}_{si}"):
                    st.session_state.pilares[pi]["subtemas"].pop(si)
                    st.rerun()

            with st.form(key=f"fsub_{pi}", clear_on_submit=True):
                st_txt = st.text_input("Nuevo subtema", placeholder="Ej: Salud femenina / Salud masculina / Cómo funciona Previplan")
                if st.form_submit_button("Agregar subtema ✓", type="primary"):
                    if st_txt.strip():
                        st.session_state.pilares[pi]["subtemas"].append({"texto": st_txt.strip()})
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
                                       help="Crea fechas, formatos y canales. Sin IA.")
        with col_ia:
            btn_ia = st.button("🤖 Generar completo con IA", type="primary",
                               disabled=not groq_key,
                               help="Genera todo: ángulo, producción, caption y CTA.")
        with col_clear:
            if st.button("🗑️ Limpiar"):
                st.session_state.piezas = []
                st.rerun()

        if btn_estructura or btn_ia:
            mes_num   = MESES.index(mes_sel) + 1
            fechas    = generar_fechas(int(año_sel), mes_num)
            piezas    = []
            fecha_idx = 0

            for pilar in st.session_state.pilares:
                if not pilar["subtemas"] or pilar["n"] == 0:
                    continue
                subtemas  = pilar["subtemas"]
                vocero    = pilar.get("vocero", "General - marca")
                for i in range(pilar["n"]):
                    sub     = subtemas[i % len(subtemas)]
                    fmt     = formato_para_pilar(pilar["nombre"], i)
                    canal   = CANAL_POR_FORMATO.get(fmt, "Ig")
                    piezas.append({
                        "pilar":      pilar["nombre"],
                        "hashtags":   pilar["hashtags"],
                        "subtema":    sub["texto"],
                        "formato":    fmt,
                        "red":        canal,
                        "vocero":     vocero,
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

            if btn_ia:
                # Rastrear ángulos usados por subtema para evitar repetición
                angulos_por_subtema = {}
                prog = st.progress(0, text="Generando contenido con IA...")
                for idx, p in enumerate(piezas):
                    key_sub = f"{p['pilar']}::{p['subtema']}"
                    usados  = angulos_por_subtema.get(key_sub, [])
                    resultado = generar_pieza_ia(
                        p["pilar"], p["subtema"], p["formato"],
                        p["vocero"], contexto_mes, usados, groq_key
                    )
                    p["angulo"]     = resultado["angulo"]
                    p["produccion"] = resultado["produccion"]
                    p["caption"]    = resultado["caption"]
                    p["cta"]        = resultado["cta"]
                    # Registrar ángulo usado
                    if resultado["angulo"]:
                        angulos_por_subtema.setdefault(key_sub, []).append(resultado["angulo"])
                    prog.progress((idx+1)/len(piezas), text=f"Pieza {idx+1}/{len(piezas)}: {p['subtema'][:40]}...")
                prog.empty()
                st.session_state.piezas = piezas
                st.success(f"✅ {len(piezas)} piezas generadas con IA.")
            else:
                st.success(f"✅ Estructura de {len(piezas)} piezas creada. Genera los contenidos IA desde la pestaña Guiones.")

        if st.session_state.piezas:
            piezas = st.session_state.piezas
            st.markdown(f"**{len(piezas)} piezas** · {mes_sel} {int(año_sel)}")

            # ── Descarga Excel ────────────────────────────────────────────
            csv_data = generar_csv(piezas)
            st.download_button(
                label="⬇️ Descargar CSV (abre en Excel)",
                data=csv_data,
                file_name=f"Parrilla_{mes_sel}_{int(año_sel)}.csv",
                mime="text/csv",
            )

            st.markdown("---")

            # ── Tarjetas de parrilla ───────────────────────────────────────
            for idx, p in enumerate(piezas):
                angulo_txt = p["angulo"] if p["angulo"] else p["subtema"]
                status_idx = STATUS_OPTS.index(p["status"]) if p["status"] in STATUS_OPTS else 0

                with st.container(border=True):
                    # Fila 1: metadata + status
                    col_fecha, col_pilar, col_fmt, col_canal, col_status = st.columns([1.2, 2, 1.5, 1.2, 2])
                    col_fecha.markdown(f"**{p['fecha'].strftime('%d %b')}**")
                    col_pilar.markdown(f"**{p['pilar']}**")
                    col_fmt.write(p["formato"])
                    col_canal.write(p["red"])
                    nuevo_st = col_status.selectbox(
                        "", STATUS_OPTS, index=status_idx,
                        key=f"st_{idx}", label_visibility="collapsed"
                    )
                    st.session_state.piezas[idx]["status"] = nuevo_st

                    # Fila 2: ángulo
                    st.markdown(f"📌 **{angulo_txt}**")

                    # Fila 3: caption y CTA en columnas si existen
                    if p.get("caption") or p.get("cta"):
                        col_cap, col_cta = st.columns([3, 1])
                        if p.get("caption"):
                            cap_preview = p["caption"][:200] + ("..." if len(p["caption"]) > 200 else "")
                            col_cap.caption(f"📝 {cap_preview}")
                        if p.get("cta"):
                            col_cta.info(f"🎯 {p['cta']}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — GUIONES
# ══════════════════════════════════════════════════════════════════════════════
with tab_guiones:
    st.subheader("Contenido detallado por pieza")
    piezas = st.session_state.piezas

    if not piezas:
        st.info("Genera la parrilla primero desde la pestaña Parrilla.")
    else:
        sin_contenido = [p for p in piezas if not p.get("angulo")]
        if sin_contenido and groq_key:
            if st.button(f"🤖 Generar IA para {len(sin_contenido)} piezas pendientes", type="primary"):
                ctx = st.session_state.get("ctx_guardado", "")
                angulos_por_subtema = {}
                # Pre-cargar ángulos ya existentes
                for p in piezas:
                    if p.get("angulo"):
                        key = f"{p['pilar']}::{p['subtema']}"
                        angulos_por_subtema.setdefault(key, []).append(p["angulo"])
                prog = st.progress(0, text="Generando...")
                done = 0
                for idx, p in enumerate(piezas):
                    if not p.get("angulo"):
                        key    = f"{p['pilar']}::{p['subtema']}"
                        usados = angulos_por_subtema.get(key, [])
                        res    = generar_pieza_ia(p["pilar"], p["subtema"], p["formato"], p["vocero"], ctx, usados, groq_key)
                        st.session_state.piezas[idx]["angulo"]     = res["angulo"]
                        st.session_state.piezas[idx]["produccion"] = res["produccion"]
                        st.session_state.piezas[idx]["caption"]    = res["caption"]
                        st.session_state.piezas[idx]["cta"]        = res["cta"]
                        if res["angulo"]:
                            angulos_por_subtema.setdefault(key, []).append(res["angulo"])
                        done += 1
                        prog.progress(done/len(sin_contenido), text=f"Generando {done}/{len(sin_contenido)}...")
                prog.empty()
                st.success("✅ Listo.")
                st.rerun()
        elif not groq_key and sin_contenido:
            st.warning("Ingresa tu Groq API Key en el panel izquierdo para generar contenido.")

        st.markdown("---")

        for idx, p in enumerate(piezas):
            tiene = bool(p.get("angulo"))
            icono = "🟢" if tiene else "⚪"
            titulo = p.get("angulo") or p["subtema"]
            with st.expander(f"{icono} #{idx+1} · {p['pilar']} · {p['formato']} · {p['red']} · {titulo[:55]}"):

                col_info, col_st = st.columns([4, 1])
                col_info.markdown(f"📅 **{p['fecha'].strftime('%d %B %Y')}** · 📱 {p['red']} · 🎤 {p['vocero']}")
                status_idx = STATUS_OPTS.index(p["status"]) if p["status"] in STATUS_OPTS else 0
                nuevo_st = col_st.selectbox("Status", STATUS_OPTS, index=status_idx, key=f"gst_{idx}")
                st.session_state.piezas[idx]["status"] = nuevo_st

                st.markdown(f"**Subtema amplio:** {p['subtema']}")

                if tiene:
                    st.markdown(f"**📌 Ángulo / Título:** {p['angulo']}")

                    st.markdown("**🎬 Guía de Producción**")
                    prod = st.text_area("", value=p["produccion"], height=280,
                                       key=f"prod_{idx}", label_visibility="collapsed")
                    st.session_state.piezas[idx]["produccion"] = prod

                    st.markdown("**📝 Caption**")
                    cap = st.text_area("", value=p["caption"], height=130,
                                      key=f"cap_{idx}", label_visibility="collapsed")
                    st.session_state.piezas[idx]["caption"] = cap

                    st.markdown("**🎯 CTA**")
                    cta = st.text_input("", value=p["cta"], key=f"cta_{idx}", label_visibility="collapsed")
                    st.session_state.piezas[idx]["cta"] = cta

                    ht = p.get("hashtags","") + " #TuSaludNoDaEspera #Previplan #Previsalud"
                    st.code(ht.strip(), language=None)

                else:
                    st.info("Sin contenido IA aún.")
                    if groq_key and st.button("🤖 Generar esta pieza", key=f"gen1_{idx}"):
                        ctx    = st.session_state.get("ctx_guardado", "")
                        usados = [pp["angulo"] for pp in piezas
                                  if pp.get("angulo") and pp["subtema"] == p["subtema"] and pp["pilar"] == p["pilar"]]
                        res    = generar_pieza_ia(p["pilar"], p["subtema"], p["formato"], p["vocero"], ctx, usados, groq_key)
                        st.session_state.piezas[idx]["angulo"]     = res["angulo"]
                        st.session_state.piezas[idx]["produccion"] = res["produccion"]
                        st.session_state.piezas[idx]["caption"]    = res["caption"]
                        st.session_state.piezas[idx]["cta"]        = res["cta"]
                        st.rerun()
