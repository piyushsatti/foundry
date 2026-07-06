# manifold-web

Browser UI for manifold — HTML viewer + JSON API + CodeMirror editor.

Depends on `packages/manifold` for all data access. Started via:

```bash
# preferred — uses CLI shim with PYTHONPATH set
packages/manifold/scripts/manifold serve

# or directly (set PYTHONPATH first)
export PYTHONPATH="$PWD/packages/manifold:$PWD/apps/manifold-web"
python3 -m manifold_web serve --port 7779
```

Default URL: http://127.0.0.1:7779/

## Tests

```bash
cd apps/manifold-web && python3 -m unittest discover -v
```
