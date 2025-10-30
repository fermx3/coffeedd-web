import os
import io
import base64
import requests
from PIL import Image
import streamlit as st

st.set_page_config(page_title="CoffeeCare - Diagnóstico", page_icon="☕️", layout="centered")

# ---- Encabezado
st.title("☕️🍃 CoffeeCare")
st.subheader("Detección de enfermedades en hojas de café con IA")

st.markdown(
    "Sube una **foto nítida de la hoja** (primer plano, buena luz). "
    "La imagen se enviará al modelo para evaluar si está **sana** o presenta **enfermedad**."
)

# ---- Config API
API_URL_DEFAULT = "http://localhost:8000/predict"  # cámbiala si tu API vive en otro host
api_url = st.text_input("Endpoint de la API", value=API_URL_DEFAULT, help="Ej: http://localhost:8000/predict")

# ---- Uploader
uploaded = st.file_uploader("Imagen de hoja (JPG/PNG)", type=["jpg", "jpeg", "png"])

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

# ---- UI principal
col1, col2 = st.columns([1, 1])
with col1:
    if uploaded:
        img_pil = Image.open(uploaded).convert("RGB")
        st.image(img_pil, caption="Imagen cargada", use_column_width=True)
    else:
        st.info("Sube una imagen para habilitar el botón de diagnóstico.")

with col2:
    st.markdown("### Diagnóstico")
    run = st.button("Analizar imagen", use_container_width=True, type="primary")

    if run:
        if not uploaded:
            st.warning("Primero sube una imagen.")
            st.stop()

        # Llamada al backend
        files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)}
        try:
            with st.spinner("Procesando imagen..."):
                resp = requests.post(api_url, files=files, timeout=60)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            st.error(f"Error llamando a la API: {e}")
            st.stop()

        # Esperado: {"class_name": "...", "probability": float, "raw": [...], "image_base64": "opcional"}
        class_name = data.get("class_name", "unknown")
        prob = data.get("probability", None)

        if class_name == "unknown" or prob is None:
            st.warning("La respuesta no contiene los campos esperados. Respuesta completa:")
            st.json(data)
        else:
            conf_pct = f"{prob*100:.1f}%"
            st.success(f"**Resultado**: `{class_name}` · **Confianza**: {conf_pct}")

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
                    st.image(out_img, caption="Imagen procesada (API)", use_column_width=True)
                except Exception:
                    st.caption("No se pudo decodificar la imagen devuelta por la API.")

            # Probabilidades completas
            with st.expander("Ver probabilidades por clase"):
                st.json(data.get("raw", []))

# ---- Footer
st.divider()
st.caption("CoffeeCare · Demo académica · Streamlit Frontend + FastAPI Backend")
