import { InputHTMLAttributes, TextareaHTMLAttributes, forwardRef } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  variant?: 'default' | 'underline'
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className = '', variant = 'default', ...props }, ref) => {
    const variantClass = variant === 'underline' ? 'input-underline' : ''

    return (
      <input
        ref={ref}
        className={`input ${variantClass} ${className}`}
        {...props}
      />
    )
  }
)

Input.displayName = 'Input'

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  variant?: 'default' | 'underline'
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className = '', variant = 'default', ...props }, ref) => {
    const variantClass = variant === 'underline' ? 'input-underline' : ''

    return (
      <textarea
        ref={ref}
        className={`input ${variantClass} ${className}`}
        {...props}
      />
    )
  }
)

Textarea.displayName = 'Textarea'
