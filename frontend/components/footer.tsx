interface FooterTextProps {
  className?: string
}

export function FooterText({
  className
}: FooterTextProps) {
  return (
    <div className={className}>
      <p className="text-center text-xs text-zinc-500">
        CodeAtlas · AI-powered codebase intelligence
      </p>
    </div>
  )
}
