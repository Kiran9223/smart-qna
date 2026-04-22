import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

// ─── Animated similarity bar + count-up number ───────────────────────────────
function SimilarityBar({ similarity, delay = 0 }) {
  const [barWidth, setBarWidth] = useState(0);
  const [count, setCount] = useState(0);
  const pct = Math.round(similarity * 100);

  useEffect(() => {
    const t = setTimeout(() => {
      setBarWidth(pct);

      const startTime = performance.now();
      const duration = 750;
      const tick = (now) => {
        const elapsed = now - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // cubic ease-out
        setCount(Math.round(eased * pct));
        if (progress < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    }, delay);

    return () => clearTimeout(t);
  }, [pct, delay]);

  const barColor =
    pct >= 85 ? "bg-emerald-500" : pct >= 70 ? "bg-amber-500" : "bg-rose-400";
  const countColor =
    pct >= 85 ? "text-emerald-700" : pct >= 70 ? "text-amber-700" : "text-rose-600";

  return (
    <div className="flex items-center gap-2 mt-1.5">
      <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${barColor}`}
          style={{
            width: `${barWidth}%`,
            transition: "width 0.75s cubic-bezier(0.22, 1, 0.36, 1)",
          }}
        />
      </div>
      <span
        className={`text-xs font-bold w-9 text-right tabular-nums shrink-0 ${countColor}`}
      >
        {count}%
      </span>
    </div>
  );
}

// ─── Gear path generator ──────────────────────────────────────────────────────
function buildGearPath(cx, cy, outerR, innerR, teeth) {
  const step = (Math.PI * 2) / teeth;
  const pts = [];
  for (let i = 0; i < teeth; i++) {
    const base = i * step - Math.PI / 2;
    pts.push([cx + innerR * Math.cos(base),              cy + innerR * Math.sin(base)]);
    pts.push([cx + outerR * Math.cos(base + step * 0.2), cy + outerR * Math.sin(base + step * 0.2)]);
    pts.push([cx + outerR * Math.cos(base + step * 0.5), cy + outerR * Math.sin(base + step * 0.5)]);
    pts.push([cx + innerR * Math.cos(base + step * 0.7), cy + innerR * Math.sin(base + step * 0.7)]);
  }
  return "M " + pts.map(([x, y]) => `${x.toFixed(2)} ${y.toFixed(2)}`).join(" L ") + " Z";
}

// ─── Mechanical gears loading state ──────────────────────────────────────────
function GearScanner() {
  return (
    <div className="card overflow-hidden border border-slate-200">
      {/* Dark machine header */}
      <div className="bg-gradient-to-br from-slate-800 to-slate-900 px-5 py-4 flex items-center gap-5">

        {/* Gear SVG — 3 interlocking gears, brain at center */}
        <div className="relative shrink-0" style={{ width: 130, height: 90 }}>
          <svg viewBox="0 0 130 90" width="130" height="90" overflow="visible">
            {/* Large center gear — spins clockwise */}
            <g className="gear-cw">
              <path d={buildGearPath(62, 44, 18, 13, 10)} fill="#6366f1" />
              <circle cx={62} cy={44} r={8} fill="#0f172a" />
              <circle cx={62} cy={44} r={3} fill="#4f46e5" />
            </g>

            {/* Upper-right gear — spins counter-clockwise (interlocked) */}
            <g className="gear-ccw">
              <path d={buildGearPath(89, 27, 12, 9, 8)} fill="#818cf8" />
              <circle cx={89} cy={27} r={4.5} fill="#0f172a" />
              <circle cx={89} cy={27} r={2} fill="#6366f1" />
            </g>

            {/* Lower-left gear — spins counter-clockwise (interlocked) */}
            <g className="gear-ccw">
              <path d={buildGearPath(35, 61, 12, 9, 8)} fill="#818cf8" />
              <circle cx={35} cy={61} r={4.5} fill="#0f172a" />
              <circle cx={35} cy={61} r={2} fill="#6366f1" />
            </g>

            {/* Faint connector lines between gear centers */}
            <line x1={62} y1={44} x2={89} y2={27} stroke="#334155" strokeWidth="1" strokeDasharray="3 3" />
            <line x1={62} y1={44} x2={35} y2={61} stroke="#334155" strokeWidth="1" strokeDasharray="3 3" />
          </svg>

          {/* Brain emoji pinned to center of large gear */}
          <div
            className="absolute pointer-events-none select-none text-sm leading-none"
            style={{ top: "44px", left: "62px", transform: "translate(-50%, -50%)" }}
          >
            🧠
          </div>
        </div>

        {/* Right side text */}
        <div className="flex-1">
          <p className="text-white font-bold tracking-widest text-sm">
            AI PROCESSING
          </p>
          <p className="text-slate-400 text-xs mt-0.5">
            Scanning for similar questions…
          </p>
          <div className="flex gap-1.5 mt-3">
            {[0, 0.22, 0.44].map((delay, i) => (
              <div
                key={i}
                className="w-1.5 h-1.5 rounded-full bg-indigo-400"
                style={{ animation: `pulse 1.2s ease-in-out ${delay}s infinite` }}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Scanning skeleton lines */}
      <div className="px-4 py-3 bg-slate-50 space-y-2.5">
        {[72, 52, 38].map((_, i) => (
          <div key={i} className="h-2 rounded-full bg-slate-100 overflow-hidden">
            <div
              className="h-full w-1/3 rounded-full bg-gradient-to-r from-transparent via-indigo-200 to-transparent"
              style={{ animation: `scan-slide 1.7s ease-in-out ${i * 0.2}s infinite` }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Results panel ────────────────────────────────────────────────────────────
function MatchResults({ results }) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setVisible(false);
    const t = setTimeout(() => setVisible(true), 40);
    return () => clearTimeout(t);
  }, [results]);

  return (
    <div
      className="card overflow-hidden border border-amber-300"
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(-6px)",
        transition: "opacity 0.3s ease, transform 0.3s ease",
      }}
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-amber-500 to-orange-500 px-4 py-3 flex items-center gap-2.5">
        <div
          className="relative w-9 h-9 shrink-0"
          style={{ animation: "brain-ping 2.5s ease-in-out infinite" }}
        >
          <div className="absolute inset-0 rounded-full bg-amber-600/50" />
          <div className="absolute inset-1 rounded-full bg-amber-700 flex items-center justify-center">
            <span className="text-sm select-none">🧠</span>
          </div>
        </div>

        <div>
          <p className="text-white text-sm font-bold tracking-widest">
            MATCH FOUND
          </p>
          <p className="text-amber-100 text-xs">
            Similar questions already exist
          </p>
        </div>

        <span className="ml-auto bg-white/25 text-white text-xs font-bold px-2.5 py-0.5 rounded-full shrink-0">
          {results.length} result{results.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Result rows */}
      <div className="divide-y divide-amber-100">
        {results.map((post, i) => (
          <div
            key={post.post_id}
            className="px-4 py-3 hover:bg-amber-50 transition-colors"
            style={{
              animation: `result-in 0.3s ease both`,
              animationDelay: `${i * 80}ms`,
            }}
          >
            <div className="flex items-start justify-between gap-2">
              <Link
                to={`/posts/${post.post_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-700 hover:text-blue-900 hover:underline font-medium leading-snug"
              >
                {post.title}
              </Link>
              <span className="shrink-0 text-gray-400 text-xs mt-0.5">↗</span>
            </div>
            <SimilarityBar similarity={post.similarity} delay={i * 100 + 100} />
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="px-4 py-2.5 bg-amber-50 border-t border-amber-100">
        <p className="text-xs text-amber-700">
          Your answer might already be above. You can still post if none of
          these help.
        </p>
      </div>
    </div>
  );
}

// ─── Public export ────────────────────────────────────────────────────────────
export default function SimilarQuestionsPanel({ isLoading, results }) {
  if (isLoading) return <GearScanner />;
  if (results.length > 0) return <MatchResults results={results} />;
  return null;
}
