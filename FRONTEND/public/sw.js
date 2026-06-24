self.addEventListener('push', (event) => {
  if (!event.data) return

  let data = {}
  try {
    data = event.data.json()
  } catch {
    data = { title: 'Acelera Transportes', body: event.data.text() }
  }

  const titulo = data.title || 'Acelera Transportes'
  const opcoes = {
    body: data.body || '',
    icon: '/favicon.png',
    badge: '/favicon.png',
    data: { url: data.url || '/fretes' },
    requireInteraction: true,
    tag: `frete-${data.frete_id || 'aviso'}`,
    renotify: true,
  }

  event.waitUntil(self.registration.showNotification(titulo, opcoes))
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const url = event.notification.data?.url || '/fretes'

  event.waitUntil(
    clients
      .matchAll({ type: 'window', includeUncontrolled: true })
      .then((lista) => {
        for (const client of lista) {
          if ('focus' in client) {
            client.navigate(url)
            return client.focus()
          }
        }
        if (clients.openWindow) {
          return clients.openWindow(url)
        }
      }),
  )
})
