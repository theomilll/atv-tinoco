'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { Barcode } from '@/components'

export default function LoginPage() {
  const router = useRouter()
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [currentTime, setCurrentTime] = useState('')
  const [currentDate, setCurrentDate] = useState('')

  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      setCurrentTime(now.toLocaleTimeString('en-US', { hour12: false }))
      setCurrentDate(now.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: '2-digit'
      }).toUpperCase())
    }
    updateTime()
    const interval = setInterval(updateTime, 1000)
    return () => clearInterval(interval)
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      await login(username, password)
      router.push('/chat')
    } catch {
      setError('ACCESS DENIED')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg-dark flex items-center justify-center p-8">
      <div className="w-full max-w-md">
        {/* Boarding Pass Card */}
        <div className="bg-bg-surface border border-border">
          {/* Header */}
          <div className="flex items-start justify-between p-6 border-b border-dotted border-border">
            <div>
              <div className="text-2xl tracking-wider text-white mb-1">CHATGEPETO</div>
              <div className="text-xs tracking-widest text-text-muted">SYSTEM ACCESS</div>
            </div>
            <Barcode width={80} height={40} />
          </div>

          {/* Form Section */}
          <div className="p-6">
            {error && (
              <div className="mb-6 p-4 border border-red-500 bg-red-500/10">
                <div className="text-xs tracking-wide text-red-400">{error}</div>
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="mb-6">
                <label className="field-label mb-2 block">PASSENGER</label>
                <input
                  type="text"
                  className="input"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="ENTER USERNAME"
                  required
                  disabled={isLoading}
                  autoComplete="username"
                />
              </div>

              <div className="mb-6">
                <label className="field-label mb-2 block">CLEARANCE</label>
                <input
                  type="password"
                  className="input"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="ENTER PASSWORD"
                  required
                  disabled={isLoading}
                  autoComplete="current-password"
                />
              </div>

              <div className="border-t border-dotted border-border pt-6">
                <button
                  type="submit"
                  className="btn btn-primary w-full"
                  disabled={isLoading}
                >
                  {isLoading ? 'AUTHENTICATING...' : 'AUTHENTICATE'}
                </button>
              </div>
            </form>
          </div>

          {/* Footer */}
          <div className="border-t border-dashed border-border p-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="status-dot" />
              <span className="text-xs tracking-wide text-text-muted">
                {isLoading ? 'CONNECTING' : 'AWAITING CREDENTIALS'}
              </span>
            </div>
            <div className="text-right">
              <div className="text-xs text-text-muted">{currentDate}</div>
              <div className="text-sm text-white tracking-wide">{currentTime}</div>
            </div>
          </div>
        </div>

        {/* Stub */}
        <div className="mt-4 flex items-center justify-between text-xs text-text-muted tracking-wide">
          <span>XX-{Math.floor(Math.random() * 9000000 + 1000000)}</span>
          <Barcode width={60} height={24} />
        </div>
      </div>
    </div>
  )
}
