import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// foundry repo root (prototype lives at plugins/cartographer/prototype)
const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');

// Serves repo files as plain text at /artifact/<repo-relative-path> so
// artifact chips in the detail panel are real links. Chosen over /@fs/
// because it works identically in dev AND preview, and pins content-type
// to text/plain (markdown renders as raw text — this is a probe).
function artifactServer() {
  const handler = async (req, res, next) => {
    if (!req.url || !req.url.startsWith('/artifact/')) return next();
    const rel = decodeURIComponent(req.url.slice('/artifact/'.length).split('?')[0]);
    const abs = path.resolve(REPO_ROOT, rel);
    if (!abs.startsWith(REPO_ROOT + path.sep)) {
      res.statusCode = 403;
      return res.end('forbidden');
    }
    try {
      const body = await readFile(abs);
      res.setHeader('Content-Type', 'text/plain; charset=utf-8');
      res.end(body);
    } catch {
      res.statusCode = 404;
      res.end('no file');
    }
  };
  return {
    name: 'artifact-server',
    configureServer(server) {
      server.middlewares.use(handler);
    },
    configurePreviewServer(server) {
      server.middlewares.use(handler);
    },
  };
}

export default defineConfig({
  plugins: [react(), artifactServer()],
});
