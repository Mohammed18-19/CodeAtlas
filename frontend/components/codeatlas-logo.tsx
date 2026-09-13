import * as React from 'react'

export function CodeAtlasLogo({
  className = 'h-9 w-9',
}: {
  className?: string
}) {
  return (
    <svg
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="CodeAtlas"
    >
      <defs>
        <linearGradient id="ca-logo-gradient" x1="8" y1="8" x2="40" y2="40">
          <stop offset="0%" stopColor="#A78BFA" />
          <stop offset="48%" stopColor="#7C3AED" />
          <stop offset="100%" stopColor="#C084FC" />
        </linearGradient>
      </defs>

      <rect
        x="2"
        y="2"
        width="44"
        height="44"
        rx="13"
        fill="#0D0B19"
        stroke="rgba(167,139,250,0.25)"
        strokeWidth="1.5"
      />

      <path
        d="M18 12.5C13.8 15.5 11.5 19.5 11.5 24C11.5 28.5 13.8 32.5 18 35.5"
        stroke="url(#ca-logo-gradient)"
        strokeWidth="2.6"
        strokeLinecap="round"
      />

      <path
        d="M30 12.5C34.2 15.5 36.5 19.5 36.5 24C36.5 28.5 34.2 32.5 30 35.5"
        stroke="url(#ca-logo-gradient)"
        strokeWidth="2.6"
        strokeLinecap="round"
      />

      <path
        d="M24 9.5C19.4 13.2 17 18 17 24C17 30 19.4 34.8 24 38.5C28.6 34.8 31 30 31 24C31 18 28.6 13.2 24 9.5Z"
        fill="#7C3AED"
        fillOpacity="0.08"
        stroke="url(#ca-logo-gradient)"
        strokeWidth="1.5"
      />

      <path
        d="M10.5 24H37.5"
        stroke="#A78BFA"
        strokeOpacity="0.55"
        strokeWidth="1.2"
      />

      <circle cx="24" cy="24" r="3.4" fill="#A78BFA" />
      <circle cx="24" cy="24" r="6.5" stroke="#A78BFA" strokeOpacity="0.18" />

      <circle cx="14" cy="17" r="1.4" fill="#C084FC" />
      <circle cx="34" cy="17" r="1.4" fill="#C084FC" />
      <circle cx="14" cy="31" r="1.4" fill="#8B5CF6" />
      <circle cx="34" cy="31" r="1.4" fill="#8B5CF6" />
    </svg>
  )
}
