import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Create singleton formatters to avoid recreation on every call
const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
})

const numberFormatter = new Intl.NumberFormat('en-US')

const dateFormatter = new Intl.DateTimeFormat('en-US', {
  year: 'numeric',
  month: 'short',
  day: 'numeric',
})

export function formatCurrency(amount: number): string {
  return currencyFormatter.format(amount)
}

export function formatNumber(num: number): string {
  return numberFormatter.format(num)
}

export function formatDate(date: Date | string): string {
  return dateFormatter.format(new Date(date))
}

export function generateApiKey(): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let result = 'sk_'
  for (let i = 0; i < 32; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}
