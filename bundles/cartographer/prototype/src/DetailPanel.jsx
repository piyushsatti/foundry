import { GLYPHS } from './transform.js';

// The single disclosure surface: opens on node click, closes on canvas click.
export default function DetailPanel({ d }) {
  return (
    <aside className="panel">
      <div className="panel-line">
        <span className="line-dot" style={{ background: d.lineColor }} />
        {d.lineLabel}
      </div>

      <h2 className={d.standing === 'expired' ? 'struck' : ''}>{d.title}</h2>

      <div className="panel-moment">
        <span aria-hidden="true">{GLYPHS[d.moment]}</span> {d.moment}
        {d.status === 'open' && <span className="tag-open">open</span>}
        {d.isFrontier && (
          <span className="tag-frontier">
            <span className="pulse-dot" />
            in progress now
          </span>
        )}
      </div>

      {d.standing === 'expired' && (
        <p className="expired-note">
          No longer in force — superseded by “{d.supersededBy}”.
        </p>
      )}

      <p className="panel-summary">{d.summary}</p>

      {d.settled && (
        <p className="panel-settled">
          <strong>Settled</strong> {d.settled}
        </p>
      )}

      {d.quote && <blockquote className="panel-quote">{d.quote}</blockquote>}

      {d.artifacts.length > 0 && (
        <div className="panel-artifacts">
          <h3>Produced</h3>
          <ul>
            {d.artifacts.map((a) => (
              <li key={a.name}>
                {a.path ? (
                  <a
                    className="artifact-link"
                    href={`/artifact/${encodeURI(a.path)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {a.name}
                  </a>
                ) : (
                  <>
                    {a.name} <span className="no-file">no file</span>
                  </>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </aside>
  );
}
