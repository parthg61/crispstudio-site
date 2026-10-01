import { AbsoluteFill, Img, random, staticFile, useCurrentFrame } from 'remotion';

// Seamless 5s loop: croissant idles, stretches, crunches, and sprays crumbs that fall out of frame.
const BG = '#FFF4E8';
const COLOURS = ['#021F53', '#021F53', '#CD4604', '#FD9F0F', '#021F53', '#CD4604'];
const SHARDS = [
  'M2 9 8 1l10 4-3 9-11 1z',
  'M1 6 9 0l9 7-6 9-10-3z',
  'M3 2h12l3 9-9 5-8-6z',
  'M0 8 6 1l12 2 1 10-11 3z',
];
const CRUNCH_AT = 34;
const GRAVITY = 1.15;

const crumbs = new Array(18).fill(0).map((_, i) => {
  const angle = (-165 + random(`a${i}`) * 150) * (Math.PI / 180);
  const speed = 13 + random(`s${i}`) * 15;
  return {
    x0: 330 + random(`x${i}`) * 340,
    y0: 300 + random(`y${i}`) * 50,
    vx: Math.cos(angle) * speed,
    vy: Math.sin(angle) * speed - 6,
    size: 18 + random(`z${i}`) * 26,
    spin: (random(`r${i}`) - 0.5) * 30,
    rot0: random(`o${i}`) * 360,
    colour: COLOURS[i % COLOURS.length],
    path: SHARDS[i % SHARDS.length],
    delay: Math.floor(random(`d${i}`) * 3),
  };
});

export const Crunch: React.FC = () => {
  const f = useCurrentFrame();

  // Idle bob — one full sine period per loop so frame 0 === frame 150
  const bob = Math.sin((f / 150) * Math.PI * 2) * 8;

  // Anticipation stretch, then a damped squash after the crunch
  let sx = 1;
  let sy = 1;
  if (f >= CRUNCH_AT - 10 && f < CRUNCH_AT) {
    const p = (f - (CRUNCH_AT - 10)) / 10;
    sy = 1 + 0.05 * Math.sin(p * Math.PI * 0.5);
    sx = 1 - 0.025 * Math.sin(p * Math.PI * 0.5);
  } else if (f >= CRUNCH_AT) {
    const t = f - CRUNCH_AT;
    const amp = Math.exp(-t / 7) * Math.cos(t / 2.1);
    sy = 1 - 0.1 * amp;
    sx = 1 + 0.06 * amp;
  }
  const tilt = f >= CRUNCH_AT ? Math.exp(-(f - CRUNCH_AT) / 9) * Math.sin((f - CRUNCH_AT) / 2.6) * 3 : 0;

  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      <div
        style={{
          position: 'absolute',
          left: 140,
          top: 258 + bob,
          width: 720,
          transformOrigin: '50% 90%',
          transform: `rotate(${tilt}deg) scale(${sx}, ${sy})`,
        }}
      >
        <Img src={staticFile('Crisp_Logo_FullColour.svg')} style={{ width: '100%' }} />
      </div>

      <svg width={1000} height={1000} style={{ position: 'absolute', inset: 0 }}>
        {/* Impact burst at the moment of the crunch */}
        {f >= CRUNCH_AT && f < CRUNCH_AT + 14 && (
          <g transform={`translate(560 ${250 + bob})`} opacity={1 - (f - CRUNCH_AT) / 14}>
            {[-70, -35, 0, 35, 70].map((a) => {
              const p = (f - CRUNCH_AT) / 14;
              return (
                <line
                  key={a}
                  x1={0}
                  y1={-20 - 40 * p}
                  x2={0}
                  y2={-50 - 70 * p}
                  stroke="#021F53"
                  strokeWidth={9}
                  strokeLinecap="round"
                  transform={`rotate(${a})`}
                />
              );
            })}
          </g>
        )}
        {crumbs.map((c, i) => {
          const t = f - CRUNCH_AT - c.delay;
          if (t < 0) return null;
          const x = c.x0 + c.vx * t;
          const y = c.y0 + bob + c.vy * t + 0.5 * GRAVITY * t * t;
          if (y > 1100) return null;
          const pop = Math.min(1, t / 4);
          return (
            <g key={i} transform={`translate(${x} ${y}) rotate(${c.rot0 + c.spin * t}) scale(${(c.size / 20) * pop})`}>
              <path d={c.path} fill={c.colour} transform="translate(-10 -8)" />
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
