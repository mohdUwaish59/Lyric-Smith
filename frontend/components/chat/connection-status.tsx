"use client"

import { useEffect, useState } from "react"
import { Wifi, WifiOff } from "lucide-react"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function ConnectionStatus() {
  const [isConnected, setIsConnected] = useState<boolean | null>(null)
  const [isChecking, setIsChecking] = useState(false)

  useEffect(() => {
    let mounted = true
    
    const checkConnection = async () => {
      if (isChecking) return
      setIsChecking(true)
      
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 3000)
        
        const response = await fetch(`${API_BASE}/`, {
          signal: controller.signal,
        })
        
        clearTimeout(timeoutId)
        
        if (mounted) {
          setIsConnected(response.ok)
        }
      } catch (error) {
        if (mounted) {
          setIsConnected(false)
        }
      } finally {
        if (mounted) {
          setIsChecking(false)
        }
      }
    }

    // Check immediately
    checkConnection()
    
    // Check every 10 seconds
    const interval = setInterval(checkConnection, 10000)
    
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [isChecking])

  if (isConnected === null) {
    return null // Don't show anything while initially checking
  }

  if (!isConnected) {
    return (
      <div className="fixed bottom-20 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded-full shadow-lg text-sm animate-in slide-in-from-bottom-2">
        <WifiOff className="w-4 h-4" />
        <span>API server not connected</span>
      </div>
    )
  }

  return null
}
