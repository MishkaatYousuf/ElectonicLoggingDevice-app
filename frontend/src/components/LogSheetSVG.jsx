import './LogSheetSVG.css'

const ROW_ORDER = ['OFF', 'SB', 'D', 'ON']
const ROW_LABELS = {
  OFF: '1. Off Duty',
  SB: '2. Sleeper Berth',
  D: '3. Driving',
  ON: '4. On Duty (not driving)',
}

const GRID_LEFT = 150
const GRID_TOP = 30
const HOUR_WIDTH = 34
const ROW_HEIGHT = 34
const GRID_WIDTH = HOUR_WIDTH * 24
const GRID_HEIGHT = ROW_HEIGHT * 4
const SVG_WIDTH = GRID_LEFT + GRID_WIDTH + 30
const SVG_HEIGHT = GRID_TOP + GRID_HEIGHT + 40

function xForHour(h) {
  return GRID_LEFT + h * HOUR_WIDTH
}

function yForRow(status) {
  return GRID_TOP + ROW_ORDER.indexOf(status) * ROW_HEIGHT
}

export default function LogSheetSVG({ day }) {
  const segments = [...day.segments].sort((a, b) => a.start_hour - b.start_hour)

  // Build a continuous path: horizontal run per segment, vertical jump between them
  let pathD = ''
  segments.forEach((seg, i) => {
    const y = yForRow(seg.status)
    const x1 = xForHour(seg.start_hour)
    const x2 = xForHour(seg.end_hour)
    if (i === 0) {
      pathD += `M ${x1} ${y} L ${x2} ${y} `
    } else {
      pathD += `L ${x1} ${y} L ${x2} ${y} `
    }
  })

  return (
    <div className="log-sheet">
      <div className="log-sheet__header">
        <div>
          <div className="log-sheet__title">Driver's Daily Log</div>
          <div className="log-sheet__subtitle">{day.date_label} · 24 hours</div>
        </div>
        <div className="log-sheet__totals">
          <TotalPill label="Driving" value={day.total_driving_hours} color="var(--amber)" />
          <TotalPill label="On duty" value={day.total_on_duty_hours} color="var(--blue)" />
          <TotalPill label="Off duty" value={day.total_off_duty_hours} color="var(--text-dim)" />
          <TotalPill label="Sleeper" value={day.total_sleeper_hours} color="#a78bfa" />
        </div>
      </div>

      <svg
        viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
        className="log-sheet__svg"
        role="img"
        aria-label={`Daily log grid for ${day.date_label}`}
      >
        {/* Hour labels top */}
        {Array.from({ length: 25 }).map((_, h) => (
          <text
            key={`label-${h}`}
            x={xForHour(h)}
            y={GRID_TOP - 10}
            textAnchor="middle"
            className="log-sheet__hourlabel"
          >
            {h === 0 || h === 24 ? 'Mid' : h === 12 ? 'Noon' : h % 12}
          </text>
        ))}

        {/* Row labels */}
        {ROW_ORDER.map((status) => (
          <text
            key={status}
            x={GRID_LEFT - 10}
            y={yForRow(status) + ROW_HEIGHT / 2 + 4}
            textAnchor="end"
            className="log-sheet__rowlabel"
          >
            {ROW_LABELS[status]}
          </text>
        ))}

        {/* Grid background rows */}
        {ROW_ORDER.map((status, i) => (
          <rect
            key={status}
            x={GRID_LEFT}
            y={GRID_TOP + i * ROW_HEIGHT}
            width={GRID_WIDTH}
            height={ROW_HEIGHT}
            className="log-sheet__row"
          />
        ))}

        {/* Vertical hour gridlines (bold every hour, faint every 15 min) */}
        {Array.from({ length: 24 * 4 + 1 }).map((_, q) => {
          const hour = q / 4
          const isHourLine = q % 4 === 0
          return (
            <line
              key={`grid-${q}`}
              x1={xForHour(hour)}
              y1={GRID_TOP}
              x2={xForHour(hour)}
              y2={GRID_TOP + GRID_HEIGHT}
              className={isHourLine ? 'log-sheet__gridline-major' : 'log-sheet__gridline-minor'}
            />
          )
        })}

        {/* Horizontal row separators */}
        {Array.from({ length: 5 }).map((_, i) => (
          <line
            key={`hrow-${i}`}
            x1={GRID_LEFT}
            y1={GRID_TOP + i * ROW_HEIGHT}
            x2={GRID_LEFT + GRID_WIDTH}
            y2={GRID_TOP + i * ROW_HEIGHT}
            className="log-sheet__gridline-major"
          />
        ))}

        {/* The duty status line itself - the signature element */}
        <path d={pathD} className="log-sheet__dutyline" fill="none" />

        {/* Vertical connector ticks at status changes, small dots */}
        {segments.map((seg, i) => (
          <circle
            key={`dot-${i}`}
            cx={xForHour(seg.start_hour)}
            cy={yForRow(seg.status)}
            r={2.5}
            className="log-sheet__dutydot"
          />
        ))}
      </svg>

      <div className="log-sheet__remarks">
        {segments.map((seg, i) => (
          <span key={i} className="log-sheet__remark-chip">
            {formatHour(seg.start_hour)}–{formatHour(seg.end_hour)} · {seg.label || ROW_LABELS[seg.status]}
          </span>
        ))}
      </div>
    </div>
  )
}

function TotalPill({ label, value, color }) {
  return (
    <div className="total-pill">
      <span className="total-pill__dot" style={{ background: color }} />
      <span className="total-pill__label">{label}</span>
      <span className="total-pill__value">{value.toFixed(1)}h</span>
    </div>
  )
}

function formatHour(h) {
  const hours = Math.floor(h) % 24
  const minutes = Math.round((h - Math.floor(h)) * 60)
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`
}
