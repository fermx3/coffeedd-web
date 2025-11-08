# app.py — CoffeeCare (Streamlit)
import os
import io
import time
import base64
import requests
from requests.exceptions import HTTPError
from PIL import Image
import streamlit as st

# =========================
# Configuración general
# =========================
st.set_page_config(
    page_title="CoffeeCare - Diagnóstico",
    page_icon="☕️",
    layout="centered"
)

# Parámetros de negocio / UX
CONF_THRESH = 0.60             # Umbral de confianza (ej. 0.60 = 60%)
MAX_FILE_MB = 5                # Máximo tamaño aceptado (MB)
SUPPORT_EMAIL = "soporte@coffeecare.example"  # Cambia por tu correo real

# =========================
# Configuración de la API
# =========================
API_BASE    = os.getenv("API_URL", "https://coffeedd-api-696723121967.europe-southwest1.run.app").rstrip("/")
PREDICT_URL = f"{API_BASE}/predict"
HEALTH_URL  = f"{API_BASE}/health"

def check_health(timeout=1000):
    """
    Consulta /health.
    - Si responde 200 y status='healthy' & model_loaded=True -> (True, data, 'health')
    - Si /health NO existe (404) -> (True, {'status': 'demo'}, 'demo')  [tolerante]
    - Cualquier otro error -> (False, <texto_error>, 'error')
    """
    try:
        r = requests.get(HEALTH_URL, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        ok = (data.get("status") == "healthy") and bool(data.get("model_loaded", False))
        return ok, data, "health"
    except HTTPError as e:
        try:
            status_code = e.response.status_code  # type: ignore[attr-defined]
        except Exception:
            status_code = None
        if status_code == 404:
            # API sin /health -> seguir en modo demo
            return True, {"status": "demo", "reason": "API sin /health (404)"}, "demo"
        return False, f"{status_code} {e}", "error"
    except Exception as e:
        return False, str(e), "error"

# ---- Encabezado
st.title("☕️🍃 CoffeeCare")
st.subheader("Detección de enfermedades en hojas de café con IA")
st.markdown(
    "Sube una **foto nítida de la hoja** (primer plano, buena luz). "
    "La imagen se enviará al modelo para evaluar si está **sana** o presenta **enfermedad**."
)

# =======================================
# Estado del modelo
# =======================================
st.markdown("#### Estado del modelo")
ok, health_payload, source = check_health()

col_h1, col_h2 = st.columns([1, 3])
with col_h1:
    if ok:
        st.success("Listo ✅" if source == "health" else "Listo (demo) ✅")
    else:
        st.error("No disponible ❌")
with col_h2:
    if isinstance(health_payload, dict):
        if source == "health":
            st.caption(
                f"status: `{health_payload.get('status')}` · "
                f"model_loaded: `{health_payload.get('model_loaded')}`"
            )
        else:
            st.caption("Funcionando sin `/health` (maqueta).")
    else:
        st.code(health_payload, language="text")

# Botón para reintentar chequeo
# if st.button("Reintentar chequeo"):
#    st.rerun()

# ---- Carga de imagen con validación de tamaño
uploaded = st.file_uploader("Imagen de hoja (JPG/PNG)", type=["jpg", "jpeg", "png"])
if uploaded is not None:
    size_mb = uploaded.size / (1024 * 1024)
    if size_mb > MAX_FILE_MB:
        st.error(
            f"La imagen pesa **{size_mb:.2f} MB** y supera el límite de **{MAX_FILE_MB} MB**. "
            "Por favor sube una imagen más liviana."
        )
        uploaded = None  # invalida la imagen para el flujo

# ---- Recomendaciones por clase (demo)
RECO_MAP = {
    "healthy": [
        "Mantén riego regular y buen drenaje.",
        "Monitorea periódicamente para detección temprana."
    ],
    "leaf_rust": [
        "Retira hojas muy afectadas para evitar propagación.",
        "Mejora aireación del cultivo y evita exceso de humedad.",
        "Consulta manejo integrado (fungicidas si corresponde)."
    ],
    "american_leaf_spot": [
        "Revisa humedad y estrés hídrico.",
        "Sanea partes muy dañadas y optimiza fertilización."
    ],
    "miner": [
        "Monitoreo frecuente; retirar hojas muy minadas.",
        "Manejo integrado de plagas según recomendaciones locales."
    ],
    "phoma": [
        "Evitar exceso de riego, mejorar drenaje.",
        "Aplicar manejo fitosanitario recomendado por técnico."
    ],
    "other": [
        "Sigue observando; si empeora, consulta a un técnico local.",
        "Toma más fotos de diferentes hojas para precisar diagnóstico."
    ],
}

# Etiquetas y clases enfermas para color
LABELS_ES = {
    "healthy": "Sana",
    "leaf_rust": "Roya",
    "american_leaf_spot": "Mancha foliar americana",
    "miner": "Minador",
    "phoma": "Phoma"
}
DISEASE_CLASSES = {"leaf_rust", "american_leaf_spot", "miner", "phoma"}

# ---- UI principal
col1, col2 = st.columns([1, 1])
with col1:
    if uploaded:
        img_pil = Image.open(uploaded).convert("RGB")
        st.image(img_pil, caption="Imagen cargada", width="stretch")
    else:
        st.info("Sube una imagen para habilitar el botón de diagnóstico.")

with col2:
    st.markdown("### Diagnóstico")
    run = st.button("Analizar imagen", width="stretch", type="primary")

    if run:
        # Validaciones previas
        if not uploaded:
            st.warning("Primero sube una imagen.")
            st.stop()

        if not ok and source != "demo":
            st.error("El modelo no está disponible en este momento. Intenta cuando el estado sea 'Listo ✅'.")
            st.stop()

        # Llamada al backend con barra de progreso (visual)
        files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
        progress = st.progress(0)
        try:
            # Paso 1: preparando
            progress.progress(20)
            # time.sleep(0.05)

            # Paso 2: enviando / esperando respuesta
            progress.progress(55)
            with st.spinner("Procesando imagen..."):
                resp = requests.post(PREDICT_URL, files=files, timeout=60)
                resp.raise_for_status()
                data = resp.json()

            # Paso 3: parseando / mostrando
            progress.progress(85)
            # time.sleep(0.05)

        except Exception as e:
            progress.empty()
            st.error(f"Error llamando a la API: {e}")
            st.stop()
        finally:
            progress.progress(100)
            # time.sleep(0.05)
            progress.empty()

        # Esperado: {"class_name": "...", "probability": float, "raw": [...], "image_base64": "opcional"}
        class_name = data.get("class_name", "unknown")
        prob = data.get("probability", None)

        if class_name == "unknown" or prob is None:
            st.warning("La respuesta no contiene los campos esperados. Respuesta completa:")
            st.json(data)
        else:
            conf_pct = f"{prob*100:.1f}%"
            label = LABELS_ES.get(class_name, class_name)

            # Colorear según clase
            if class_name == "healthy":
                st.success(f"**Resultado:** `{label}` · **Confianza:** {conf_pct}")
            elif class_name in DISEASE_CLASSES:
                st.error(f"**Resultado:** `{label}` · **Confianza:** {conf_pct}", icon="🚩")
            else:
                st.info(f"**Resultado:** `{label}` · **Confianza:** {conf_pct}")

            # Aviso por baja confianza
            if isinstance(prob, (int, float)) and prob < CONF_THRESH:
                st.warning(
                    f"**Confianza baja ({conf_pct})**. Te sugerimos subir más fotos de distintas hojas o "
                    f"contactar a soporte: [{SUPPORT_EMAIL}](mailto:{SUPPORT_EMAIL})."
                )

            # Recomendaciones
            recos = RECO_MAP.get(class_name, RECO_MAP["other"])
            st.markdown("**Recomendaciones sugeridas:**")
            for r in recos:
                st.markdown(f"- {r}")

            # Imagen devuelta (por ejemplo, overlay/Grad-CAM)
            if "image_base64" in data:
                try:
                    out_bytes = base64.b64decode(data["image_base64"])
                    out_img = Image.open(io.BytesIO(out_bytes))
                    st.image(out_img, caption="Imagen procesada (API)", width="stretch")
                except Exception:
                    st.caption("No se pudo decodificar la imagen devuelta por la API.")

            # Probabilidades completas
            with st.expander("Ver probabilidades por clase"):
                st.json(data.get("raw", []))

# ---- Footer
st.divider()
st.caption("CoffeeCare · Demo académica · Streamlit Frontend + FastAPI Backend")
