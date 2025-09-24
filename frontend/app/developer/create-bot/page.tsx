'use client'

import { useRouter } from 'next/navigation'
import BotForm from '@/components/bots/BotForm'

export default function CreateBotPage() {
  const router = useRouter()

  const handleSuccess = () => {
    router.push('/developer/bots')
  }

  const handleCancel = () => {
    router.back()
  }

  return (
    <BotForm 
      onSuccess={handleSuccess}
      onCancel={handleCancel}
    />
  )
}

