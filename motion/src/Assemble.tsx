import { AbsoluteFill, Easing, Img, interpolate, random, spring, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';

// 1.5s intro: crumbs fly in and the croissant assembles. The last frame matches Crunch frame 0
// exactly (logo at rest, no crumbs), so the site can swap straight into the loop.
const BG = '#FFF4E8';
const COLOURS = ['#021F53', '#CD4604', '#021F53', '#FD9F0F', '#021F53', '#CD4604'];
const SHARDS = ['M2 9 8 1l10 4-3 9-11 1z', 'M1 6 9 0l9 7-6 9-10-3z', 'M3 2h12l3 9-9 5-8-6z', 'M0 8 6 1l12 2 1 10-11 3z'];
const LAND = 22; // crumbs arrive
const POP = 12; // croissant starts forming

const crumbs = new Array(24).fill(0).map((_, i) => {
  const a = random(`ia${i}`) * Math.PI * 2;
  const r = 620 + random(`ir${i}`) * 200;
  return {
    sx: 500 + Math.cos(a) * r,
    sy: 500 + Math.sin(a) * r,
    ex: 260 + random(`ex${i}`) * 480,
    ey: 320 + random(`ey${i}`) * 300,
    size: 16 + random(`iz${i}`) * 24,
    spin: (random(`is${i}`) - 0.5) * 720,
    colour: COLOURS[i % COLOURS.length],
    path: SHARDS[i % SHARDS.length],
    delay: Math.floor(random(`id${i}`) * 8),
  };
});

export const Assemble: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();

  const s = spring({ frame: f - POP, fps, config: { damping: 9, mass: 0.7, stiffness: 140 } });
  const settle = interpolate(f, [38, 44], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const scale = (0.55 + 0.45 * s) * (1 - settle) + settle;
  const squashY = f > LAND && f < LAND + 10 ? 1 - 0.06 * Math.sin(((f - LAND) / 10) * Math.PI) * (1 - settle) : 1;
  const reveal = interpolate(f, [POP, POP + 14], [0, 80], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });
  const opacity = interpolate(f, [POP, POP + 4], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      <div
        style={{
          position: 'absolute',
          left: 140,
          top: 258,
          width: 720,
          opacity,
          transformOrigin: '50% 90%',
          transform: `scale(${scale}, ${scale * squashY})`,
          clipPath: f >= 40 ? 'none' : `circle(${reveal}% at 50% 60%)`,
        }}
      >
        <Img src={staticFile('Crisp_Logo_FullColour.svg')} style={{ width: '100%' }} />
      </div>

      <svg width={1000} height={1000} style={{ position: 'absolute', inset: 0 }}>
        {crumbs.map((c, i) => {
          const t = interpolate(f - c.delay, [0, LAND - 4], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.in(Easing.quad) });
          if (t >= 1) return null;
          const x = c.sx + (c.ex - c.sx) * t;
          const y = c.sy + (c.ey - c.sy) * t;
          const k = t > 0.8 ? (1 - t) / 0.2 : 1;
          return (
            <g key={i} transform={`translate(${x} ${y}) rotate(${c.spin * t}) scale(${(c.size / 20) * k})`}>
              <path d={c.path} fill={c.colour} transform="translate(-10 -8)" />
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};
