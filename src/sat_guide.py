"""
Guía paso a paso para el timbrado manual de facturas (CFDI 4.0) en el
portal gratuito del SAT ("Genera tu factura").

Los valores fijos (régimen, clave de producto, unidad, IVA) provienen de
los CFDI reales emitidos por SNCG, de modo que el trabajador solo copia y
pega. La guía es solo en español porque el portal del SAT es en español.
"""

from __future__ import annotations

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


def _kv_table(data: dict) -> None:
    """Render a copy-friendly key/value block."""
    rows = "\n".join(f"| {k} | `{v}` |" for k, v in data.items())
    st.markdown(f"| Campo | Valor |\n|---|---|\n{rows}")


def render_sat_guide(lang: str = "es") -> None:
    """Render the full manual-timbrado guide."""
    if lang == "en":
        st.caption(
            "This guide is in Spanish only, because the SAT portal itself "
            "is in Spanish."
        )

    st.markdown(
        "Guía para emitir una factura (CFDI 4.0) en el **portal gratuito del "
        "SAT**, con los valores exactos que usa SNCG Consulting. Siga los "
        "pasos en orden; al final está la sección de **problemas frecuentes**."
    )

    # -----------------------------------------------------------------
    section_label("Antes de empezar — checklist")
    st.markdown(
        """
Necesita tener a la mano **estas 3 cosas**. Si falta una, no podrá terminar:

1. **Contraseña del SAT (antes CIEC)** o **e.firma** de SNCG para entrar al portal.
2. **Los archivos del CSD** (Certificado de Sello Digital): un `.cer`, un `.key`
   y su contraseña. ⚠️ El CSD **no es lo mismo** que la e.firma; son archivos
   distintos. Los de SNCG están en el Drive: `02_fiscal/sello_digital/`.
   El CSD vigente de SNCG (no. `00001000000712989129`) expira el **30-ene-2029**.
3. **La Constancia de Situación Fiscal (CSF) del cliente**, reciente (menos de
   ~3 meses). De ahí se copian: RFC, nombre, código postal y régimen fiscal.
   Pídala al cliente ANTES de empezar; es la causa #1 de rechazos.
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
    section_label("Paso a paso — emitir la factura")
    st.markdown(
        f"""
**1. Entrar al portal.**
Abra {PORTAL_URL} en **Chrome o Edge** (no Safari). Inicie sesión con el RFC
`SCO240921EA6` y la Contraseña, o con la e.firma.

**2. Ir a «Generación de CFDI» → «Generar nuevo CFDI»** (factura con CSD).

**3. Pestaña *Comprobante*.** Llene con los datos fijos de arriba:
- Tipo: **I - Ingreso** · Moneda: **MXN** · Exportación: **01 - No aplica**
- Lugar de expedición: **36250**
- **Forma de pago:** `03 - Transferencia electrónica` si el cliente ya pagó o
  pagará por transferencia. Si aún no se sabe cómo pagará, use `99 - Por definir`.
- **Método de pago:** `PUE - Pago en una sola exhibición` si el pago ya se
  recibió (o se recibe ese mismo mes). Si el cliente pagará después o en
  partes, use `PPD` — pero ojo: PPD obliga a emitir después un
  **complemento de pago** cuando el dinero llegue. En SNCG lo normal es **PUE**.

**4. Pestaña *Receptor*.** Todo sale de la CSF del cliente, copiado **tal cual**:
- **RFC** del cliente.
- **Nombre / razón social:** exactamente como aparece en la CSF, en
  MAYÚSCULAS y **sin** el régimen societario (sin «SA DE CV», «SAS», etc.).
- **Código postal** del domicilio fiscal (el de la CSF, no el de la oficina).
- **Régimen fiscal** del cliente (viene en la CSF, p. ej. `601 - General de
  Ley Personas Morales`).
- **Uso CFDI:** normalmente `G03 - Gastos en general`. Si el cliente pide otro,
  usar el que indique. Para pruebas internas: `S01 - Sin efectos fiscales`.

**5. Pestaña *Conceptos* → Agregar.** Use la tabla de concepto de arriba:
clave `78141600`, cantidad `1`, unidad `E48`, descripción
«Servicio de inspección» (puede agregar detalle, p. ej. el número de
contenedor o PO), y el **valor unitario SIN IVA**.
- En impuestos: **Traslado IVA, tasa 0.160000** (16%). El portal calcula el
  importe solo. No capture retenciones (SNCG no retiene en este esquema).
- Verifique que el **Total = Subtotal × 1.16**.

**6. Sellar.** Botón **«Sellar comprobante»**: el portal pide los archivos del
CSD (`.cer`, `.key`) y su contraseña. Al sellar, el SAT timbra el CFDI y
asigna el **folio fiscal (UUID)**.

**7. Descargar TODO antes de salir.** Descargue el **XML** y la
**representación impresa (PDF)**. El XML es la factura legal; el PDF es solo
una vista. Si sale del portal sin descargar, puede recuperarlos en
«Consultar facturas emitidas».

**8. Verificar y archivar.**
- Verifique el CFDI en {VERIFICA_URL} (estado: **Vigente**).
- Envíe XML + PDF al cliente.
- Guarde ambos en el Drive: `02_fiscal/facturas_ingresos/<Mes Año>/`,
  nombrados con el UUID (convención de SNCG).
"""
    )

    # -----------------------------------------------------------------
    section_label("Cómo cancelar una factura")
    st.markdown(
        f"""
1. En el portal: **«Consultar facturas emitidas»** → busque por fecha o por
   folio fiscal (UUID) → seleccione la factura → **«Cancelar seleccionados»**.
2. El SAT pide un **motivo de cancelación**:
   - `02 - Comprobantes emitidos con errores SIN relación` → el caso normal
     (factura duplicada, datos mal, prueba). **Use este por defecto.**
   - `01 - Con errores CON relación` → solo si ya emitió la factura corregida;
     el portal pedirá el UUID de la factura que la sustituye.
   - `03 - No se llevó a cabo la operación` → el servicio nunca ocurrió.
3. Se firma la cancelación con el CSD o la e.firma.
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
            "«El régimen fiscal no es compatible con el Uso CFDI»",
            """
**Causa:** cada régimen del receptor solo admite ciertos usos. Ejemplo: a una
persona física asalariada (régimen 605) no se le puede poner `G03`.

**Solución:** confirme el régimen en la CSF y elija un uso compatible.
`G03 - Gastos en general` funciona para casi todas las empresas (601, 626,
612). Si nada funciona, `S01 - Sin efectos fiscales` es aceptado por todos
los regímenes.
""",
        ),
        (
            "El portal no acepta el certificado / «Certificado no válido»",
            """
**Causa #1 (la más común):** están subiendo los archivos de la **e.firma** en
lugar de los del **CSD**. Ambos son un `.cer` + `.key`, pero NO son
intercambiables: para sellar facturas se usa el CSD.

**Causa #2:** contraseña equivocada (la del CSD no es la misma que la de la
e.firma ni la Contraseña del SAT).

**Causa #3:** certificado vencido o revocado.

**Solución:** use los archivos de `02_fiscal/sello_digital/` con SU contraseña.
El CSD vigente de SNCG expira el 30-ene-2029; verifique vigencia en el portal
CertiSAT si hay duda. Si está vencido, hay que generar un CSD nuevo con la
e.firma (CertiSAT Web) y esperar ~1 hora a que se active.
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
$1.00 MXN** a un RFC propio con uso `S01 - Sin efectos fiscales`, verifíquela
en el portal del SAT y luego **cancélela con motivo 02**. Por ser menor a
$1,000 MXN la cancelación es directa, sin aceptación del receptor. Así se
recorre el proceso completo (emitir → verificar → cancelar) sin ningún efecto
fiscal ni riesgo.
"""
    )
