import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  useReactFlow,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import CardNode from './CardNode.jsx';
import DetailPanel from './DetailPanel.jsx';
import { toFlow, GLYPHS } from './transform.js';
import './styles.css';

// All session datasets, eagerly loaded; the masthead select appears only
// when there is more than one.
const modules = import.meta.glob('./data/*.json', { eager: true });
const DATASETS = Object.keys(modules)
  .sort()
  .map((k) => modules[k].default ?? modules[k]);

const nodeTypes = { card: CardNode };

function Legend({ lines }) {
  return (
    <div className="legend">
      {lines.map((l) => (
        <div key={l.label} className="legend-row">
          <span className="line-dot" style={{ background: l.color }} />
          {l.label}
        </div>
      ))}
      <hr />
      <div className="legend-row">
        {GLYPHS.breakthrough} breakthrough · {GLYPHS.setback} setback · {GLYPHS.pivot} pivot ·{' '}
        {GLYPHS.grind} grind
      </div>
      <div className="legend-row">
        <span className="amber-dot" /> amber = open
      </div>
      <div className="legend-row">
        <span className="pulse-dot" /> pulse = in progress now
      </div>
      <div className="legend-row struck">struck = expired decision</div>
    </div>
  );
}

function SessionMap() {
  const [datasetIdx, setDatasetIdx] = useState(0);
  const [collapsed, setCollapsed] = useState(() => new Set()); // default: expanded
  const [selected, setSelected] = useState(null);
  const [legendOpen, setLegendOpen] = useState(false);
  const { fitView } = useReactFlow();

  const data = DATASETS[datasetIdx];

  const toggleExcursion = useCallback((key) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }, []);

  const flow = useMemo(() => toFlow(data, collapsed), [data, collapsed]);
  const flowNodes = useMemo(
    () =>
      flow.nodes.map((n) =>
        n.data.excursions
          ? { ...n, data: { ...n.data, onToggleExcursion: toggleExcursion } }
          : n,
      ),
    [flow, toggleExcursion],
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(flowNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(flow.edges);

  const firstRender = useRef(true);
  const prevData = useRef(data);
  useEffect(() => {
    if (firstRender.current) {
      firstRender.current = false;
      return;
    }
    const datasetChanged = prevData.current !== data;
    prevData.current = data;
    setNodes((prev) => {
      if (datasetChanged) return flowNodes;
      // collapse/expand toggle: keep dragged positions of surviving nodes
      const keep = new Map(prev.map((p) => [p.id, p.position]));
      return flowNodes.map((n) =>
        keep.has(n.id) ? { ...n, position: keep.get(n.id) } : n,
      );
    });
    setEdges(flow.edges);
    requestAnimationFrame(() => fitView({ padding: 0.1, duration: 450 }));
  }, [flowNodes, flow.edges, data, setNodes, setEdges, fitView]);

  const meta = flow.meta;

  return (
    <div className="app">
      <header className="masthead">
        <div className="mast-left">
          <h1>{meta.title}</h1>
          <span className="mast-date">{meta.date}</span>
        </div>
        <div className="mast-right">
          {DATASETS.length > 1 && (
            <select
              className="dataset-select"
              aria-label="session"
              value={datasetIdx}
              onChange={(e) => {
                setDatasetIdx(Number(e.target.value));
                setCollapsed(new Set());
                setSelected(null);
              }}
            >
              {DATASETS.map((d, i) => (
                <option key={d.session.title} value={i}>
                  {d.session.date} · {d.session.title}
                </option>
              ))}
            </select>
          )}
          <span className="open-chip">
            {meta.openCount} open
          </span>
          <button
            className="help-btn"
            aria-label="legend"
            onClick={() => setLegendOpen((v) => !v)}
          >
            ?
          </button>
          {legendOpen && <Legend lines={meta.lines} />}
        </div>
      </header>

      <p className="thesis">{meta.thesis}</p>

      <div className="canvas">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.1 }}
          minZoom={0.15}
          nodesConnectable={false}
          deleteKeyCode={null}
          onNodeClick={(_, node) => setSelected(node.data)}
          onPaneClick={() => setSelected(null)}
        >
          <Background variant={BackgroundVariant.Dots} gap={24} size={1.3} color="#d8d8d2" />
        </ReactFlow>
        {selected && <DetailPanel d={selected} />}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ReactFlowProvider>
      <SessionMap />
    </ReactFlowProvider>
  );
}
