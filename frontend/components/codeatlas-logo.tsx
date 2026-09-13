import * as React from 'react'

interface CodeAtlasLogoProps {
  className?: string
}

export function CodeAtlasLogo({
  className = 'h-10 w-10'
}: CodeAtlasLogoProps) {
  return (
    <svg
      viewBox="0 0 64 64"
      className={className}
      aria-label="CodeAtlas"
      role="img"
    >
      <defs>
        <linearGradient
          id="codeatlas-logo-gradient"
          x1="8"
          y1="8"
          x2="56"
          y2="56"
          gradientUnits="userSpaceOnUse"
        >
          <stop offset="0" stopColor="#6d28d9" />
          <stop offset="0.45" stopColor="#8b5cf6" />
          <stop offset="1" stopColor="#c084fc" />
        </linearGradient>
      </defs>

      <path
        fill="url(#codeatlas-logo-gradient)"
        d="M12 10h25c10 0 17 6 17 15 0 7-4 12-10 14l11 15H41L31 41h-7v13H12V10Zm12 10v11h11c4 0 7-2 7-5.5S39 20 35 20H24Z"
      />

      <path
        fill="#7c3aed"
        d="M31 41h9l11 13H38L31 45.5V41Z"
      />
    </svg>
  )
}
