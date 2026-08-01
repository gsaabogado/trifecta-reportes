"""
Guía paso a paso para el timbrado manual de facturas (CFDI 4.0) en el
portal gratuito del SAT ("Genera tu factura").

Los valores fijos (régimen, clave de producto, unidad, IVA) provienen de
los CFDI reales emitidos por SNCG, y las capturas de pantalla son del
recorrido real validado el 2026-08-01 (emisión + cancelación de una
factura de prueba de $1.00). La guía es solo en español porque el portal
del SAT es en español.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from branding import section_label

# --- Datos fijos del emisor (tomados de CFDIs reales de SNCG) ---------------
EMISOR = {
    "RFC emisor": "SCO240921EA6",
    "Nombre emisor (SIN 'SAS DE CV')": "SNCG CONSULTING",
    "Régimen fiscal": "626 - Régimen Simplificado de Confianza (RESICO)",
    "Lugar de expedición (C.P.)": "36250",
    "Tipo de comprobante": "I - Ingreso",
    "Moneda": "MXN - Peso Mexicano",
    "Exportación": "01 - No aplica",
}

CONCEPTO = {
    "Clave de producto/servicio": "78141600",
    "Descripción": "Servicio de inspección",
    "Clave de unidad": "E48 - Unidad de servicio",
    "Cantidad": "1",
    "Objeto de impuesto": "02 - Sí objeto de impuesto",
    "IVA trasladado": "Tasa 16% (0.160000)",
}

PORTAL_URL = "https://portalcfdi.facturaelectronica.sat.gob.mx"
VERIFICA_URL = "https://verificacfdi.facturaelectronica.sat.gob.mx"

ASSETS = Path(__file__).resolve().parent.parent / "assets" / "guia_sat"


def _kv_table(data: dict) -> None:
    """Render a copy-friendly key/value block."""
    rows = "\n".join(f"| {k} | `{v}` |" for k, v in data.items())
    st.markdown(f"| Campo | Valor |\n|---|---|\n{rows}")


def _img(name: str, caption: str) -> None:
    """Render a guide screenshot if the asset exists."""
    path = ASSETS / name
    if path.exists():
        st.image(str(path), caption=caption, use_container_width=True)


def render_sat_guide(lang: str = "es") -> None:
    """Render the full manual-timbrado guide."""
    if lang == "en":
        st.caption(
            "This guide is in Spanish only, because the SAT portal itself "
            "is in Spanish."
        )

    st.markdown(
        "Guía para emitir una factura (CFDI 4.0) en el **portal gratuito del "
        "SAT**, con los valores exactos que usa SNCG Consulting y capturas de "
        "pantalla del proceso real. Siga los pasos en orden; al final está la "
        "sección de **problemas frecuentes**."
    )

    # -----------------------------------------------------------------
    section_label("Paso 0 — Qué necesita y dónde está")
    st.markdown(
        """
Antes de abrir el portal, junte estas **3 cosas**. Si falta una, no podrá
terminar:

**A. e.firma (FIEL) de SNCG** — sirve para **INICIAR SESIÓN** en el portal.
Son dos archivos (un `.cer` y un `.key`) más su contraseña. Están en el
Shared Drive, carpeta `02_fiscal/firma_electronica/`.

**B. CSD (Certificado de Sello Digital) de SNCG** — sirve para **SELLAR
(firmar) la factura** al final. También son un `.cer` + un `.key` con su
propia contraseña, PERO **no son los mismos archivos que la e.firma**.
Están en `02_fiscal/sello_digital/`.

⚠️ **REGLA DE ORO: copie los 4 archivos a su Escritorio ANTES de empezar.**
Nunca los suba al portal directo desde la carpeta de Google Drive o Dropbox:
el navegador puede subir un archivo incompleto y el portal dirá que el
certificado o la contraseña son inválidos **aunque todo esté correcto**.
(Nos pasó: el mismo archivo falló desde Drive y funcionó desde el Escritorio.)
Al terminar, borre las copias del Escritorio.

Para no confundir los pares: los archivos cuyo nombre empieza con `FIEL` o
`Claveprivada_FIEL` son la **e.firma** (entrar); los que empiezan con `CSD`
o con puros números son el **sello** (firmar). El CSD vigente de SNCG expira
el **30-ene-2029**.

📄 La ubicación exacta de cada archivo y quién resguarda cada contraseña
están en la guía interna **«Accesos facturación SAT»** dentro de
`02_fiscal/` en el Drive (documento interno; no se publica aquí). Si no
tiene acceso, pídalo a administración (Laura).

**C. Constancia de Situación Fiscal (CSF) del CLIENTE**, reciente (menos de
~3 meses). De ahí se copian su RFC, nombre, código postal y régimen fiscal.
**Pídala al cliente antes de empezar** — es la causa #1 de rechazos. Para
clientes ya facturados antes no hace falta: el portal los recuerda (paso 3).
"""
    )

    # -----------------------------------------------------------------
    section_label("Datos fijos de SNCG (copiar tal cual)")
    _kv_table(EMISOR)
    st.markdown("**Concepto (servicio de inspección):**")
    _kv_table(CONCEPTO)
    st.info(
        "El nombre del emisor se escribe **SNCG CONSULTING**, en mayúsculas y "
        "**sin** «SAS DE CV». En CFDI 4.0 el régimen societario NUNCA se "
        "incluye en el nombre — ni en el emisor ni en el receptor. Es el "
        "error más común de todo el proceso."
    )

    # -----------------------------------------------------------------
    section_label("Paso 1 — Entrar al portal")
    st.markdown("Copie esta dirección en **Chrome o Edge** (no Safari):")
    st.code(PORTAL_URL, language="text")
    st.markdown(
        """
(Si la dirección cambia: en Google busque **«SAT genera tu factura»** y entre
al resultado que termine en `sat.gob.mx`. Nunca entre a un timbrador de
anuncios/publicidad: el portal oficial es gratuito.)

La página muestra dos formas de iniciar sesión. **Use la pestaña «e.firma»**
(botón abajo a la derecha): la de «Contraseña» pide la Contraseña del SAT
(antes CIEC), que NO es la contraseña de la e.firma. Si mete la contraseña
de la e.firma ahí, verá «El RFC o contraseña son incorrectos»:
"""
    )
    _img(
        "01_login_contrasena_error.jpg",
        "Pantalla equivocada: «Acceso por contraseña» pide la CIEC, no la "
        "contraseña de la e.firma. Si ve este error, cambie al botón «e.firma».",
    )
    st.markdown(
        """
En la pantalla **«Acceso con e.firma»**:

1. En «Certificado (.cer)» cargue el `.cer` de la **e.firma** (¡no el del CSD!).
2. En «Clave privada (.key)» cargue el `.key` de la e.firma.
3. Escriba la contraseña de la e.firma (mejor: cópiela y péguela) y el
   captcha, y entre. El RFC se llena solo al cargar el certificado.
"""
    )
    _img(
        "02_login_efirma.jpg",
        "Pantalla correcta: «Acceso con e.firma» con los archivos de la "
        "e.firma cargados. Si aun así marca error, casi siempre es porque los "
        "archivos se subieron desde Drive/Dropbox: cópielos al Escritorio.",
    )

    # -----------------------------------------------------------------
    section_label("Paso 2 — Abrir el formulario de factura")
    st.markdown(
        """
Ya dentro, en el menú superior derecho elija **«Generación de CFDI»**.
Se abre el formulario «Factura» (una sola página). La cabecera
**Comprobante** ya viene pre-llenada con los datos de SNCG — solo
**verifique** que diga: Régimen Simplificado de Confianza, C.P. `36250`,
Tipo `Ingreso`, Forma de pago `Transferencia electrónica de fondos`,
Método `Pago en una sola exhibición` (PUE) y Moneda `Peso Mexicano`.
"""
    )
    _img(
        "03_formulario.jpg",
        "El formulario de factura. La cabecera «Comprobante» ya trae los "
        "datos fijos de SNCG; usted solo llena cliente y concepto.",
    )
    st.markdown(
        """
Sobre la forma y método de pago:
- Si el cliente pagará por transferencia (lo normal): deje `Transferencia` + `PUE`.
- Si aún no se sabe cómo pagará: Forma `99 - Por definir`.
- `PPD` solo si pagará después o en partes — y obliga a emitir luego un
  **complemento de pago**. En SNCG lo normal es **PUE**.
"""
    )

    # -----------------------------------------------------------------
    section_label("Paso 3 — Datos del cliente")
    st.markdown(
        """
Haga clic en el campo **«Cliente Frecuente»**: se despliega la lista de
clientes a los que SNCG ya ha facturado. **Si el cliente está en la lista,
selecciónelo y el portal llena todo solo** — no hay que volver a capturar
nada.
"""
    )
    _img(
        "04_cliente_frecuente.jpg",
        "La lista de clientes frecuentes. Para un cliente ya facturado, "
        "selecciónelo y salte al Paso 4.",
    )
    st.markdown(
        """
Para un cliente **nuevo**, elija **«Otro»** (última opción). Aparecen los
campos en rojo para capturar, todo copiado **tal cual de la CSF del cliente**:

- **RFC** del cliente.
- **Nombre o Razón Social:** exactamente como en la CSF, en MAYÚSCULAS y
  **sin** régimen societario (sin «SA DE CV», «SAS», etc.). Una letra mal y
  el portal lo rechaza contra el RFC.
- **Código postal** del domicilio fiscal (el de la CSF, no el de la oficina).
- **Régimen fiscal** del cliente (viene en la CSF).
- **Uso de la Factura:** normalmente `G03 - Gastos en general`. ⚠️ La lista
  tiene muchas opciones parecidas (S01, CP01, CN01...) — lea con calma y
  elija la correcta; si el cliente pidió un uso específico, use ese.
"""
    )
    _img(
        "05_cliente_otro.jpg",
        "Cliente nuevo: con «Otro» aparecen los campos RFC y Nombre "
        "(en rojo = obligatorios).",
    )

    # -----------------------------------------------------------------
    section_label("Paso 4 — Producto y servicio")
    st.markdown(
        """
En **Producto y Servicio** haga clic en **«Agregar»** y llene:

- **Descripción Detallada:** texto libre, p. ej. `Servicio de inspección`
  (agregue contenedor o PO si aplica).
- **Producto o Servicio:** clic en la **lupa azul** 🔍 y busque `78141600`
  — debe quedar seleccionado del catálogo, no escrito a mano.
- **Unidad de Medida:** con su lupa, `E48 - Unidad de servicio`.
- **Cantidad** y **Valor Unitario SIN IVA** (el Importe se calcula solo).
- **Objeto de Impuesto:** `Sí objeto de impuesto`.
- **Número de Identificación** y **Cuenta Predial:** se dejan **vacíos**.
"""
    )
    _img(
        "06_producto_servicio.jpg",
        "El concepto llenado. «Número de Identificación» se queda vacío; el "
        "Importe lo calcula el portal.",
    )
    st.markdown(
        """
Más abajo, deje marcada la casilla **«Acepto Sugerencia de Impuestos»**:
el portal pone solo el **IVA cobrado, Tasa 16%**. Las retenciones (IVA/ISR)
se quedan vacías — SNCG no retiene. «Número de pedimento» también se salta
(es solo para venta de mercancía importada).
"""
    )
    _img(
        "07_impuestos.jpg",
        "La sugerencia de impuestos ya trae IVA 16%. Retenciones vacías. "
        "Al final, clic en «Guardar» para agregar el concepto.",
    )
    st.markdown(
        """
Clic en **«Guardar»**. El concepto aparece en la tabla y en **Totales**
verifique: `Total = Subtotal × 1.16`. Si no cuadra, vea problemas frecuentes.
"""
    )

    # -----------------------------------------------------------------
    section_label("Paso 5 — Sellar (firmar) la factura")
    st.markdown(
        """
Arriba del formulario están los botones `Guardar · Vista Previa · Sellar ·
Mi Factura`. Puede usar **Vista Previa** para revisar. Cuando todo esté
bien, clic en **«Sellar»**.

En la pantalla **«Firmar comprobante»** cargue los archivos del **CSD**
(¡no los de la e.firma!) desde su Escritorio:

1. **Clave privada (.key):** el `.key` que empieza con `CSD`.
2. **Certificado (.cer):** el `.cer` de puros números.
3. **Contraseña de clave privada:** la contraseña **del CSD** (es distinta
   a la de la e.firma y a la del portal; la resguarda administración).
4. **Confirmar** → **Firmar**.

Si carga los archivos de la e.firma por error, el portal responde
**«El Certificado utilizado no es de tipo Sello»** — es su forma de decir
"me diste la e.firma, dame el CSD":
"""
    )
    _img(
        "08_error_no_es_sello.jpg",
        "Error clásico al sellar: se cargaron los archivos de la e.firma en "
        "lugar de los del CSD. Cambie a los archivos que empiezan con «CSD».",
    )

    # -----------------------------------------------------------------
    section_label("Paso 6 — Descargar, verificar y archivar")
    st.markdown(
        """
Al firmar, aparece **«Resultado de comprobante»** con el **folio fiscal
(UUID)** — la factura ya está timbrada ante el SAT.
"""
    )
    _img(
        "09_timbrada.jpg",
        "Factura timbrada. Los dos iconos de «Acciones» descargan el XML y "
        "el PDF. Descárguelos ANTES de salir de esta pantalla.",
    )
    st.markdown(
        f"""
1. **Descargue el XML y el PDF** con los dos iconos de la columna Acciones
   (llegan en un `.zip` con ambos). El XML es la factura legal; el PDF es
   solo la vista. (Si salió sin descargar: «Consultar Facturas Emitidas».)
2. Verifique el CFDI en {VERIFICA_URL} (estado: **Vigente**).
3. Envíe **XML + PDF** al cliente.
4. Guarde ambos en el Drive: `02_fiscal/facturas_ingresos/<Mes Año>/`,
   nombrados con el UUID (convención de SNCG).
"""
    )

    # -----------------------------------------------------------------
    section_label("Cómo cancelar una factura")
    _img(
        "10_consulta.jpg",
        "El menú de consulta: «Consultar Facturas Emitidas» es donde se "
        "busca y cancela una factura.",
    )
    st.markdown(
        f"""
1. En el portal: **«Consultar Facturas Emitidas»** → busque por fecha de
   emisión o por folio fiscal (UUID) → marque la factura →
   **«Cancelar seleccionados»**.
2. El SAT pide un **motivo de cancelación**:
   - `02 - Comprobantes emitidos con errores SIN relación` → el caso normal
     (factura duplicada, datos mal, prueba). **Use este por defecto.**
   - `01 - Con errores CON relación` → solo si ya emitió la factura corregida;
     el portal pedirá el UUID de la factura que la sustituye.
   - `03 - No se llevó a cabo la operación` → el servicio nunca ocurrió.
3. Se firma la cancelación con el **CSD** (mismos archivos y contraseña que
   al sellar).
4. **¿Necesita aceptación del cliente?**
   - Facturas de **$1,000 MXN o menos** (o canceladas el mismo día): se
     cancelan **directo, sin aceptación**.
   - Facturas mayores: el cliente recibe la solicitud en su **Buzón
     Tributario** y tiene **3 días hábiles** para aceptar o rechazar. Si no
     responde, se cancela automáticamente (positiva ficta).
5. Descargue el **acuse de cancelación** y verifique en {VERIFICA_URL} que el
   estado diga **Cancelado**. Archive el acuse junto con la factura.

⏰ **Plazo legal:** una factura solo puede cancelarse hasta el último día del
mes en que se presenta la declaración anual del ejercicio en que se emitió.
No deje cancelaciones pendientes de un año a otro.
"""
    )

    # -----------------------------------------------------------------
    section_label("Problemas frecuentes y cómo resolverlos")

    problems = [
        (
            "«El RFC o contraseña son incorrectos» al entrar al portal",
            """
**Causa:** está en la pestaña «Acceso por contraseña», que pide la
**Contraseña del SAT (antes CIEC)** — y usted está tecleando la contraseña
de la e.firma. Son credenciales distintas.

**Solución:** cambie al botón **«e.firma»** y entre con los archivos
`.cer` + `.key` de la e.firma más SU contraseña. No insista en la pestaña
de contraseña: varios intentos fallidos bloquean la cuenta.
""",
        ),
        (
            "La e.firma marca «certificado, clave o contraseña inválidos» aunque todo está bien",
            """
**Causa (comprobada aquí):** los archivos `.cer`/`.key` se están subiendo al
portal **directo desde la carpeta de Google Drive o Dropbox**. Esas carpetas
son "streaming": el navegador a veces sube un archivo incompleto y el portal
rechaza el trío completo con un mensaje que no dice cuál falló.

**Solución:** copie los archivos al **Escritorio** y cárguelos desde ahí.
También: pegue la contraseña en lugar de teclearla (cuidado con mayúsculas
y con seleccionar espacios de más al copiar).
""",
        ),
        (
            "«El Certificado utilizado no es de tipo Sello» al firmar",
            """
**Causa:** cargó los archivos de la **e.firma** en la pantalla de firmar,
pero ahí van los del **CSD** (sello digital). Ambos son un `.cer` + `.key`,
pero NO son intercambiables.

**Solución:** use los archivos que empiezan con `CSD` (el `.key`) y el
`.cer` de puros números, con la contraseña **del CSD**. Vea el Paso 0 para
saber dónde están.
""",
        ),
        (
            "«El nombre del receptor no coincide con el RFC» (error CFDI40-…)",
            """
**Causa:** el nombre no está EXACTAMENTE como en la Constancia de Situación
Fiscal del cliente: sobra el «SA DE CV / SAS DE CV», hay minúsculas, un
espacio doble, o la razón social cambió.

**Solución:**
1. Pida la **CSF más reciente** del cliente (la de hace un año puede estar vieja).
2. Copie el nombre tal cual, en MAYÚSCULAS, **sin régimen societario**.
3. Revise que no haya espacios al inicio o final (al pegar es muy común).
""",
        ),
        (
            "«El código postal no corresponde al domicilio fiscal del receptor»",
            """
**Causa:** se capturó el C.P. de la oficina o bodega del cliente, no el de su
**domicilio fiscal**.

**Solución:** use el C.P. que aparece en la CSF del cliente. Si el cliente se
mudó y no ha actualizado su domicilio ante el SAT, la factura debe llevar el
C.P. viejo (el que el SAT tiene registrado) hasta que él lo actualice.
""",
        ),
        (
            "«El régimen fiscal no es compatible con el Uso CFDI» — o eligió un uso equivocado",
            """
**Causa:** cada régimen del receptor solo admite ciertos usos, y la lista
del portal tiene opciones muy parecidas (S01, CP01, CN01, G03...). Es fácil
seleccionar la equivocada sin darse cuenta.

**Solución:** confirme el régimen en la CSF y elija con calma.
`G03 - Gastos en general` funciona para casi todas las empresas. Si el
portal rechaza la combinación, `S01 - Sin efectos fiscales` es aceptado por
todos los regímenes. Si ya timbró con un uso equivocado: el uso CFDI **no**
obliga a cancelar (el receptor puede deducir con el uso que le aplique),
pero si el cliente lo pide, cancele con motivo 01 y reemita.
""",
        ),
        (
            "No puedo entrar: Contraseña bloqueada u olvidada",
            """
**Solución:** en el portal del SAT elija «¿Olvidaste tu contraseña?» y
renuévela con la **e.firma** de SNCG (es inmediato). Sin e.firma a la mano,
se puede generar con SAT ID, pero tarda días — mejor usar la e.firma.
""",
        ),
        (
            "El portal se congela, se queda en blanco o da error al sellar",
            """
El portal del SAT es viejo y se satura, sobre todo los **últimos días del mes
por la tarde** (cuando todo México factura).

**Soluciones, en orden:**
1. Use **Chrome o Edge**; evite Safari.
2. Pruebe en **ventana de incógnito** (elimina problemas de caché y sesión).
3. Desactive el bloqueador de pop-ups para `*.sat.gob.mx`.
4. Si sigue fallando, **espere y reintente en la mañana** (antes de las 10 am
   hora del centro casi siempre funciona).
5. Antes de recapturar todo, revise en «Consultar facturas emitidas» si la
   factura SÍ se timbró — a veces el error es solo de pantalla y la factura
   ya existe. **Emitirla dos veces crea un duplicado que luego hay que cancelar.**
""",
        ),
        (
            "El total no cuadra por centavos («el importe no coincide»)",
            """
**Causa:** redondeos al capturar el precio unitario con muchos decimales.

**Solución:** capture el valor unitario con **máximo 2 decimales** y deje que
el portal calcule IVA y total. Si necesita llegar a un total exacto con IVA
incluido, divida el total entre 1.16 y redondee a 2 decimales
(ej.: $6,100.44 ÷ 1.16 = $5,259.00 de subtotal).
""",
        ),
        (
            "Emití con PPD y el cliente ya pagó — ¿ahora qué?",
            """
Con método `PPD`, cada pago recibido obliga a emitir un **complemento de
pago** (mismo portal, sección «Complemento de recepción de pagos») a más
tardar el **día 5 del mes siguiente** al pago. Si el pago fue inmediato y se
olvidó cambiar a PUE, lo más limpio es: cancelar la factura PPD (motivo 01),
emitir una nueva con PUE y relacionarla como sustitución.
""",
        ),
        (
            "La factura salió con un error y ya se envió al cliente",
            """
No se puede «editar» un CFDI timbrado; solo cancelar y reemitir:
1. Emita primero la factura **correcta**.
2. Cancele la equivocada con motivo `01`, relacionando el UUID de la nueva.
3. Envíe al cliente la nueva factura y el acuse de cancelación de la vieja.
(Si aún no la enviaba y es ≤ $1,000 o del mismo día, basta motivo 02 directo.)
""",
        ),
        (
            "El cliente dice que «no le llega» o que «no es deducible»",
            """
1. Verifique el estado en el verificador del SAT: debe decir **Vigente**.
2. Mande siempre **el XML**, no solo el PDF — para el SAT el PDF no es nada.
3. Si el cliente cambió de régimen o de C.P. y no avisó, el CFDI sale con
   datos viejos y su contador lo rechaza: pida la CSF actualizada y reemita.
""",
        ),
    ]

    for title, body in problems:
        with st.expander(f"⚠️ {title}"):
            st.markdown(body)

    # -----------------------------------------------------------------
    section_label("Práctica recomendada")
    st.markdown(
        """
Antes de facturar «en serio» por primera vez, haga **una factura de prueba de
$1.00 MXN** a un RFC conocido con uso `S01 - Sin efectos fiscales`,
verifíquela y luego **cancélela con motivo 02**. Por ser menor a $1,000 MXN
la cancelación es directa, sin aceptación del receptor. Así se recorre el
proceso completo (emitir → verificar → cancelar) sin ningún efecto fiscal.
Este recorrido se validó el **2026-08-01** — las capturas de esta guía son
de esa prueba real.
"""
    )
