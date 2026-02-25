import type { SSEEvent } from './types'
import { API_URL } from './api'

export type SSEEventHandler = (event: SSEEvent) => void

/**
 * Start an SSE connection to the research endpoint.
 * Returns an AbortController that can be used to cancel the stream.
 */
export function connectSSE(onEvent: SSEEventHandler): AbortController {
  const controller = new AbortController()

  const run = async () => {
    try {
      const response = await fetch(`${API_URL}/api/research`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
        signal: controller.signal,
      })

      if (!response.ok || !response.body) {
        onEvent({ type: 'error', message: `HTTP ${response.status}: ${response.statusText}` })
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (trimmed.startsWith('data: ')) {
            try {
              const event = JSON.parse(trimmed.slice(6)) as SSEEvent
              onEvent(event)
            } catch {
              // Skip unparseable events
            }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        onEvent({ type: 'error', message: `Connection failed: ${(err as Error).message}` })
      }
    }
  }

  run()
  return controller
}
