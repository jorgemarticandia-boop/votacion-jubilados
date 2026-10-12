import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Votación Digital - Asociación de Jubilados",
    page_icon="🗳️",
    layout="centered",
)

# Archivos de datos
CANDIDATOS_FILE = "candidatos.csv"
PADRON_FILE = "padron_nacional.csv"
VOTOS_FILE = "votos_registrados.csv"

# Inicialización de archivos si no existen
if not os.path.exists(CANDIDATOS_FILE):
    pd.DataFrame(columns=["Nombre_Lista_o_Candidato"]).to_csv(
        CANDIDATOS_FILE, index=False
    )

if not os.path.exists(PADRON_FILE):
    pd.DataFrame(
        columns=["Documento", "Nombre", "Zona_Local", "Codigo_Socio"]
    ).to_csv(PADRON_FILE, index=False)

if not os.path.exists(VOTOS_FILE):
    pd.DataFrame(
        columns=["Documento", "Candidato", "Zona_Local", "Fecha_Hora"]
    ).to_csv(VOTOS_FILE, index=False)

st.title("🗳️ Votación Digital Asamblearia")
st.caption("Asociación de Jubilados - Elecciones Nacionales")
st.markdown("---")

menu = st.sidebar.radio(
    "Navegación", ["Votar (Socio)", "Administración y Reportes"]
)

# ==============================================================================
# MÓDULO DE VOTACIÓN PÚBLICA (Para los socios)
# ==============================================================================
if menu == "Votar (Socio)":
    st.subheader("Formulario de Emisión de Voto")
    st.info("Ingrese sus datos de afiliado para acceder a la papeleta digital.")

    df_padron = pd.read_csv(PADRON_FILE, dtype=str)
    df_candidatos = pd.read_csv(CANDIDATOS_FILE)

    if df_padron.empty or df_candidatos.empty:
        st.warning(
            "El proceso de votación no está activo en este momento. Intente más tarde."
        )
    else:
        # Paso 1: Identificación
        with st.form("form_identificacion"):
            doc_input = st.text_input(
                "Número de Documento de Identidad (sin puntos)"
            ).strip()
            cod_input = st.text_input(
                "Código de Socio / Contraseña personal (si aplica)"
            ).strip()

            btn_validar = st.form_submit_button("Ingresar a Votar")

        if btn_validar:
            if not doc_input:
                st.warning("Por favor, ingrese su número de documento.")
            else:
                df_votos = pd.read_csv(VOTOS_FILE, dtype=str)

                # Buscar en el padrón
                socio = df_padron[df_padron["Documento"] == doc_input]

                if socio.empty:
                    st.error(
                        "❌ El número de documento no figura en el Padrón de Habilitados."
                    )
                elif doc_input in df_votos["Documento"].values:
                    st.warning(
                        "⚠️ Ya consta un voto emitido para este número de documento."
                    )
                else:
                    # Validar segundo factor opcional si existe en el padrón
                    codigo_correcto = True
                    if "Codigo_Socio" in socio.columns and pd.notna(
                        socio.iloc[0]["Codigo_Socio"]
                    ):
                        if socio.iloc[0]["Codigo_Socio"] != cod_input:
                            codigo_correcto = False
                            st.error(
                                "❌ El Código de Socio / Verificación ingresado es incorrecto."
                            )

                    if codigo_correcto:
                        st.session_state["socio_actual"] = {
                            "documento": doc_input,
                            "nombre": socio.iloc[0]["Nombre"],
                            "zona": socio.iloc[0]["Zona_Local"],
                        }
                        st.rerun()

        # Paso 2: Papeleta Digital
        if "socio_actual" in st.session_state:
            socio = st.session_state["socio_actual"]
            st.success(
                f"Bienvenido/a, **{socio['nombre']}** (Zona: {socio['zona']})"
            )

            opciones = list(df_candidatos["Nombre_Lista_o_Candidato"]) + [
                "Voto en Blanco"
            ]

            with st.form("form_voto_remoto"):
                st.write("### Seleccione la Lista o Fórmula de su preferencia:")
                eleccion = st.radio("Opciones disponibles:", opciones)

                confirmar_voto = st.form_submit_button(
                    "📩 Emitir y Registrar Voto"
                )

                if confirmar_voto:
                    df_votos = pd.read_csv(VOTOS_FILE, dtype=str)

                    # Doble verificación antes de guardar
                    if socio["documento"] in df_votos["Documento"].values:
                        st.error("Usted ya ha registrado su voto previamente.")
                    else:
                        nuevo_voto = pd.DataFrame({
                            "Documento": [socio["documento"]],
                            "Candidato": [eleccion],
                            "Zona_Local": [socio["zona"]],
                            "Fecha_Hora": [
                                pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                            ],
                        })
                        nuevo_voto.to_csv(
                            VOTOS_FILE, mode="a", header=False, index=False
                        )

                        st.balloons()
                        st.success(
                            "✅ ¡Su voto ha sido emitido y guardado exitosamente!"
                        )
                        del st.session_state["socio_actual"]

# ==============================================================================
# MÓDULO DE ADMINISTRACIÓN, CARGA Y RESULTADOS
# ==============================================================================
elif menu == "Administración y Reportes":
    st.header("⚙️ Panel de Control y Resultados")
    clave = st.text_input("Contraseña de Administrador", type="password")

    if clave == "admin123":
        tab1, tab2, tab3 = st.tabs(
            ["Listas / Candidatos", "Cargar Padrón", "Resultados y Resumen"]
        )

        with tab1:
            st.subheader("Gestión de Fórmulas o Listas")
            candidatos_df = pd.read_csv(CANDIDATOS_FILE)
            st.dataframe(candidatos_df, use_container_width=True)

            nueva_lista = st.text_input("Añadir Lista/Fórmula:")
            if st.button("Guardar Lista"):
                if nueva_lista.strip():
                    df_nueva = pd.DataFrame(
                        {"Nombre_Lista_o_Candidato": [nueva_lista.strip()]}
                    )
                    df_nueva.to_csv(
                        CANDIDATOS_FILE,
                        mode="a",
                        header=candidatos_df.empty,
                        index=False,
                    )
                    st.success("Lista agregada correctamente.")
                    st.rerun()

        with tab2:
            st.subheader("Cargar Padrón Nacional")
            st.caption(
                "Formato requerido (CSV o Excel): Documento, Nombre, Zona_Local, Codigo_Socio (Opcional)"
            )
            archivo = st.file_uploader("Subir Padrón", type=["csv", "xlsx"])

            if archivo:
                df_subido = (
                    pd.read_csv(archivo, dtype=str)
                    if archivo.name.endswith(".csv")
                    else pd.read_excel(archivo, dtype=str)
                )
                if {"Documento", "Nombre", "Zona_Local"}.issubset(
                    df_subido.columns
                ):
                    if st.button("Reemplazar Padrón Actual"):
                        df_subido.to_csv(PADRON_FILE, index=False)
                        st.success(
                            f"Padrón actualizado con {len(df_subido)} afiliados."
                        )
                else:
                    st.error(
                        "El archivo no tiene las columnas requeridas (Documento, Nombre, Zona_Local)."
                    )

        with tab3:
            st.subheader("📊 Resumen General de Resultados")
            df_padron = pd.read_csv(PADRON_FILE, dtype=str)
            df_votos = pd.read_csv(VOTOS_FILE, dtype=str)

            tot_padron = len(df_padron)
            tot_votos = len(df_votos)
            porcentaje = (
                (tot_votos / tot_padron * 100) if tot_padron > 0 else 0
            )

            c1, c2, c3 = st.columns(3)
            c1.metric("Padrón Total", tot_padron)
            c2.metric("Votos Emitidos", tot_votos)
            c3.metric("Participación Nacional", f"{porcentaje:.2f}%")

            st.markdown("---")

            if tot_votos > 0:
                conteo_nacional = (
                    df_votos["Candidato"].value_counts().reset_index()
                )
                conteo_nacional.columns = ["Candidato / Lista", "Total Votos"]

                st.subheader(
                    f"🏆 Lista Ganadora: **{conteo_nacional.iloc[0]['Candidato / Lista']}**"
                )
                st.dataframe(conteo_nacional, use_container_width=True)
                st.bar_chart(conteo_nacional.set_index("Candidato / Lista"))

                st.markdown("---")
                st.subheader("📍 Desglose por Zona / Sede Nacional")

                # Agrupar por Zona
                resumen_zonas = []
                for zona in df_padron["Zona_Local"].unique():
                    if pd.isna(zona):
                        continue
                    hab = len(df_padron[df_padron["Zona_Local"] == zona])
                    vot = len(df_votos[df_votos["Zona_Local"] == zona])
                    part = (vot / hab * 100) if hab > 0 else 0

                    resumen_zonas.append({
                        "Zona": zona,
                        "Habilitados": hab,
                        "Votos": vot,
                        "% Participación": f"{part:.1f}%",
                    })

                st.dataframe(
                    pd.DataFrame(resumen_zonas), use_container_width=True
                )

                st.download_button(
                    label="📥 Descargar Planilla Final en CSV",
                    data=df_votos.to_csv(index=False).encode("utf-8"),
                    file_name="resumen_votacion_nacional.csv",
                    mime="text/csv",
                )
