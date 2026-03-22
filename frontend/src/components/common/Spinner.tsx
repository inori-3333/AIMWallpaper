export function Spinner({ className = '' }: { className?: string }) {
  return (
    <div className={`inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent ${className}`} />
  )
}
