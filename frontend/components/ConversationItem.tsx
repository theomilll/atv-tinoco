interface ConversationItemProps {
  title: string
  messageCount: number
  isActive: boolean
  onClick: () => void
  onDelete: () => void
}

export function ConversationItem({
  title,
  messageCount,
  isActive,
  onClick,
  onDelete
}: ConversationItemProps) {
  return (
    <div
      className={`p-3 border cursor-pointer transition-colors ${
        isActive
          ? 'bg-accent/20 border-accent'
          : 'border-transparent hover:bg-bg-elevated hover:border-border'
      }`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className={`text-sm truncate ${isActive ? 'text-accent-light' : 'text-white'}`}>
            {isActive && '> '}{title || 'UNTITLED'}
          </div>
          <div className="text-xs text-text-muted mt-1">
            {messageCount} MSG{messageCount !== 1 ? 'S' : ''}
          </div>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation()
            onDelete()
          }}
          className="text-text-muted hover:text-red-400 text-lg leading-none px-1 opacity-0 group-hover:opacity-100 hover:opacity-100"
          style={{ opacity: isActive ? 1 : undefined }}
          title="Delete"
        >
          x
        </button>
      </div>
    </div>
  )
}
