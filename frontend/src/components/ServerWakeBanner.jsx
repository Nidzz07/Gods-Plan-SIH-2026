import { useEffect, useState, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { API_BASE } from '../api.js'

export default function ServerWakeBanner() {
  const { t } = useTranslation()
  const [wakeState, setWakeState] = useState('idle') // 'idle' | 'waking' | 'error' | 'ready'
  const [secondsElapsed, setSecondsElapsed] = useState(0)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    let isCancelled = false
    let retryTimeoutId = null
    const startTime = Date.now()

    // Show banner after 3 seconds if not already resolved
    const wakeNoticeTimer = setTimeout(() => {
      if (!isCancelled) {
        setWakeState((current) => (current === 'ready' ? 'ready' : 'waking'))
      }
    }, 3000)

    // Elapsed seconds counter
    const intervalId = setInterval(() => {
      if (!isCancelled) {
        setSecondsElapsed(Math.floor((Date.now() - startTime) / 1000))
      }
    }, 1000)

    async function checkHealth(delay = 0) {
      if (isCancelled) return

      if (delay > 0) {
        await new Promise((resolve) => {
          retryTimeoutId = setTimeout(resolve, delay)
        })
      }

      if (isCancelled) return

      const elapsed = (Date.now() - startTime) / 1000
      if (elapsed > 90) {
        if (!isCancelled) setWakeState('error')
        return
      }

      try {
        const controller = new AbortController()
        const signalTimer = setTimeout(() => controller.abort(), 6000)
        const response = await fetch(`${API_BASE}/health`, {
          signal: controller.signal,
          headers: { Accept: 'application/json' },
        })
        clearTimeout(signalTimer)

        if (response.ok) {
          if (!isCancelled) {
            clearTimeout(wakeNoticeTimer)
            setWakeState('ready')
          }
          return
        }
      } catch {
        // Ignored: server still spinning up or sleeping
      }

      if (isCancelled) return

      // Backoff retry: 3s to 5s intervals
      const nextDelay = Math.min(3000 + Math.floor(elapsed) * 100, 5000)
      checkHealth(nextDelay)
    }

    checkHealth(0)

    return () => {
      isCancelled = true
      clearTimeout(wakeNoticeTimer)
      clearTimeout(retryTimeoutId)
      clearInterval(intervalId)
    }
  }, [])

  if (wakeState === 'idle' || wakeState === 'ready') {
    return null
  }

  if (wakeState === 'error') {
    return (
      <aside
        id="server-wake-banner"
        role="alert"
        aria-live="assertive"
        className="w-full bg-[#FDF2F0] border-b border-[#D4573D] text-[#D4573D] px-4 py-2 text-[13px] font-sans"
      >
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <span>
            {t('common.serverWakeTimeout', 'Could not reach the server after 90 seconds. Please check back shortly.')}
          </span>
        </div>
      </aside>
    )
  }

  return (
    <aside
      id="server-wake-banner"
      role="status"
      aria-live="polite"
      className="w-full bg-[#F3F0EA] border-b border-[#DDD9D0] text-[#14171A] px-4 py-2 text-[13px] font-sans"
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <span>
          {t('common.serverWaking', 'Waking the server. Free hosting sleeps when idle; this takes up to a minute.')}
        </span>
        <span className="text-[#5B6169] tabular-nums font-mono text-[12px]">
          {secondsElapsed}s / 90s
        </span>
      </div>
    </aside>
  )
}
