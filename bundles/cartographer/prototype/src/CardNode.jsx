import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import { GLYPHS } from './transform.js';

const SIDES = [
  ['t', Position.Top],
  ['r', Position.Right],
  ['b', Position.Bottom],
  ['l', Position.Left],
];

// One station on the map. Everything it shows comes from node.data.
const CardNode = memo(function CardNode({ data, selected }) {
  const cls = ['card'];
  if (data.standing === 'expired') cls.push('expired');
  if (data.isFrontier) cls.push('frontier');
  if (selected) cls.push('selected');

  return (
    <div className={cls.join(' ')} style={{ '--line': data.lineColor }}>
      {SIDES.map(([s, p]) => (
        <Handle key={`${s}-in`} id={`${s}-in`} type="target" position={p} />
      ))}
      {SIDES.map(([s, p]) => (
        <Handle key={`${s}-out`} id={`${s}-out`} type="source" position={p} />
      ))}

      <div className="card-row">
        <span className={`glyph glyph-${data.moment}`} aria-hidden="true">
          {GLYPHS[data.moment]}
        </span>
        <span className="card-title">{data.title}</span>
      </div>

      {(data.status === 'open' || data.isFrontier) && (
        <div className="card-tags">
          {data.status === 'open' && <span className="tag-open">open</span>}
          {data.isFrontier && (
            <span className="tag-frontier">
              <span className="pulse-dot" />
              in progress now
            </span>
          )}
        </div>
      )}

      {data.excursions && (
        <div className="card-excursions">
          {data.excursions.map((ex) => (
            <button
              key={ex.key}
              className="excursion-chip"
              style={{ '--ex': ex.color }}
              title={ex.collapsed ? 'expand' : 'collapse'}
              onClick={(e) => {
                e.stopPropagation();
                data.onToggleExcursion?.(ex.key);
              }}
            >
              <span className="line-dot" style={{ background: ex.color }} />
              {ex.label} · {ex.stops} stops
              <span className="chev" aria-hidden="true">
                {ex.collapsed ? '▸' : '▾'}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
});

export default CardNode;
