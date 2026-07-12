Design probe for the cartographer session map: every session in `src/data/*.json` (masthead select appears when there's more than one) rendered as a draggable React Flow canvas — colored lines, fan-out/merge, a loop-back excursion that collapses into its anchor card, frontier pulse, click-a-node disclosure with artifact links served raw from the repo at `/artifact/<path>`.

    npm install && npm run dev

Judge the paradigm by feel: does dragging stations while edges follow make the session legible, and does the one-quiet-view rule (masthead + thesis + canvas, nothing else at rest) hold up? Law check: `node scripts/check-ids.mjs`.
