interface DividerProps {
  variant?: 'solid' | 'dotted' | 'dashed'
  className?: string
}

export function Divider({ variant = 'solid', className = '' }: DividerProps) {
  const variantClass = variant === 'dotted'
    ? 'divider-dotted'
    : variant === 'dashed'
      ? 'divider-dashed'
      : 'divider'

  return <div className={`${variantClass} ${className}`} />
}
