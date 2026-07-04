# Pendientes de NEGOCIO para vender en serio (2026-07-03)

> Salieron de la auditoría "producto premium USD 70/mes". Todo lo arreglable
> por código ya se arregló y está en main. Estos 3 puntos NO son de código:
> son decisiones/operación de Mati + Agus.

## 1) Precios de materiales: el catálogo está congelado en 2026-04-15
La sección Materiales (feature estrella) sirve un CSV curado
(`backend/data/materiales-precios.csv`, 74 materiales) cuya última
actualización fue el 15/04. Hoy un cliente ve precios de hace 2,5 meses.
El copy ya se bajó a "precios de referencia" (era "en vivo" — mentía), pero
para vender a $69.900/mes hace falta **rutina de actualización**:
- Mínimo: refrescar el CSV 1 vez al mes (commit + deploy automático).
- Ideal: ruta admin de carga (mismo patrón que admin-creditos) para
  actualizar sin deploy. Se construye en un día cuando lo prioricen.

## 2) Landing promete "sin tarjeta" pero el onboarding con MP es tarjeta-upfront
`index.html` dice "Probá 7 días gratis" sin tarjeta. El código de registro
(`auth_service.register_user`) está preparado así: SIN MP → trial directo
sin tarjeta (estado actual, coherente). CON MP activo → el usuario nuevo
arranca `inactive` y debe cargar tarjeta para el trial (tarjeta-upfront).
**El día que carguen las credenciales de MP, la landing pasa a mentir.**
Decidir ANTES de activar pagos:
- (a) mantener trial sin tarjeta (cambiar el registro para que siga dando
  trial aunque MP esté activo — 1 línea), o
- (b) tarjeta-upfront (cambiar el copy de landing/pricing: "7 días de
  prueba, cancelás cuando quieras").
La (b) filtra curiosos y suele convertir mejor a pago real; la (a) llena el
funnel. Es una decisión de negocio, no técnica.

## 3) Sandbox de MP antes de cobrar de verdad
Ya está en `ACTIVAR_PAGOS.md` §3 pero lo repito porque es la única parte del
camino del dinero que nunca se ejecutó end-to-end: cuando Agus tenga las
credenciales de TEST, correr el flujo completo (suscripción + carrito de
cursos, con tarjetas de prueba) antes de pasar a producción. El código del
preapproval está escrito contra la doc de MP; el sandbox puede revelar
ajustes finos (lo dice el propio docstring del servicio).

---
También quedó documentado en la auditoría (no bloqueante): los `confirm()`
nativos del navegador en acciones destructivas — funcionales pero no
premium; migrarlos a un modal propio cuando haya un rato.
