interface BarcodeProps {
  width?: number
  height?: number
  className?: string
  dark?: boolean
}

export function Barcode({ width = 100, height = 50, className = '', dark = false }: BarcodeProps) {
  // Generate a pseudo-random pattern based on width
  const bars: { width: number; gap: number }[] = []
  let currentX = 0
  const seed = width * 7 + height * 3

  while (currentX < width) {
    const barWidth = ((seed + currentX * 13) % 3) + 3 // 3-5px bars
    const gapWidth = ((seed + currentX * 7) % 2) + 2 // 2-3px gaps
    bars.push({ width: barWidth, gap: gapWidth })
    currentX += barWidth + gapWidth
  }

  const barColor = dark ? '#1a1a1a' : '#ffffff'

  return (
    <div
      className={`flex items-stretch ${className}`}
      style={{ height, width }}
      aria-hidden="true"
    >
      {bars.map((bar, i) => (
        <div
          key={i}
          style={{
            width: bar.width,
            marginRight: bar.gap,
            backgroundColor: barColor,
          }}
        />
      ))}
    </div>
  )
}

export function BarcodePattern({
  width = 100,
  height = 50,
  className = '',
  dark = false
}: BarcodeProps) {
  return (
    <div
      className={`${dark ? 'barcode-pattern-dark' : 'barcode-pattern'} ${className}`}
      style={{ width, height }}
      aria-hidden="true"
    />
  )
}
