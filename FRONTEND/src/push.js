import axios from 'axios'

function urlBase64ParaUint8Array(base64) {
  const padding = '='.repeat((4 - (base64.length % 4)) % 4)
  const b64 = (base64 + padding).replace(/-/g, '+').replace(/_/g, '/')
  const raw = window.atob(b64)
  return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)))
}

let _inscricaoAtiva = false

export async function iniciarNotificacoesPush() {
  if (_inscricaoAtiva) return
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) return

  try {
    const registro = await navigator.serviceWorker.register('/sw.js')
    await navigator.serviceWorker.ready

    const permissao = await Notification.requestPermission()
    if (permissao !== 'granted') return

    const { data } = await axios.get('/push/vapid-public-key')
    if (!data?.public_key) return

    const chavePublica = urlBase64ParaUint8Array(data.public_key)

    const inscricaoExistente = await registro.pushManager.getSubscription()
    if (inscricaoExistente) {
      _inscricaoAtiva = true
      return
    }

    const inscricao = await registro.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: chavePublica,
    })

    const json = inscricao.toJSON()
    await axios.post('/push/subscribe', {
      endpoint: json.endpoint,
      p256dh: json.keys.p256dh,
      auth: json.keys.auth,
    })

    _inscricaoAtiva = true
  } catch (err) {
    // Falha silenciosa — push nao e obrigatorio
    console.warn('[push] Setup falhou:', err?.message || err)
  }
}

export async function cancelarNotificacoesPush() {
  if (!('serviceWorker' in navigator)) return
  try {
    const registro = await navigator.serviceWorker.getRegistration('/sw.js')
    if (!registro) return
    const inscricao = await registro.pushManager.getSubscription()
    if (!inscricao) return
    await axios.delete('/push/subscribe', {
      data: {
        endpoint: inscricao.endpoint,
        p256dh: inscricao.toJSON().keys.p256dh,
        auth: inscricao.toJSON().keys.auth,
      },
    })
    await inscricao.unsubscribe()
    _inscricaoAtiva = false
  } catch (err) {
    console.warn('[push] Cancelamento falhou:', err?.message || err)
  }
}
