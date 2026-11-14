// Logo of the (fictional) customer Aerion Windkraft AG: a three-blade rotor and a wordmark. Same mark as the deck.
export function AerionLogo({ size = 32 }: { size?: number }) {
  return (
    <span className="aerion" aria-label="Aerion Windkraft AG" role="img">
      <svg viewBox="-36 -36 72 72" width={size} height={size} aria-hidden="true">
        <g fill="currentColor">
          <path id="aerion-blade" d="M0,-5 C6,-12 6,-27 0,-35 C-3.5,-27 -4,-12 0,-5Z" />
          <use href="#aerion-blade" transform="rotate(120)" />
          <use href="#aerion-blade" transform="rotate(240)" />
        </g>
        <circle r="5" fill="#FF3621" />
      </svg>
      <span className="aerion-text" aria-hidden="true">
        <b>AERION</b>
        <small>Windkraft AG</small>
      </span>
    </span>
  );
}
