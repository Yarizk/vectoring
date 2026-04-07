interface KseiLogoProps {
  size?: number;
  className?: string;
}

/**
 * KSEI Intelligence logo mark.
 * Three ascending bars (financial data) + trend line + peak circle.
 * Gradient blue background, white/sky elements.
 */
export function KseiLogo({ size = 20, className }: KseiLogoProps) {
  const id = 'ksei-grad';
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="KSEI Intelligence"
    >
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="24" y2="24" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#1d4ed8" />
          <stop offset="100%" stopColor="#0369a1" />
        </linearGradient>
      </defs>

      {/* Background */}
      <rect width="24" height="24" rx="5.5" fill={`url(#${id})`} />

      {/* Bar 1 — shortest */}
      <rect x="3.5" y="15" width="3.5" height="6" rx="1" fill="white" opacity="0.5" />
      {/* Bar 2 — medium */}
      <rect x="8.5" y="11" width="3.5" height="10" rx="1" fill="white" opacity="0.75" />
      {/* Bar 3 — tallest */}
      <rect x="13.5" y="7" width="3.5" height="14" rx="1" fill="white" />

      {/* Trend line connecting bar tops */}
      <polyline
        points="5.25,15 10.25,11 15.25,7"
        stroke="#7dd3fc"
        strokeWidth="1.25"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />

      {/* Peak accent dot */}
      <circle cx="20" cy="5" r="2" fill="#38bdf8" />
      <circle cx="20" cy="5" r="1" fill="white" />
    </svg>
  );
}
