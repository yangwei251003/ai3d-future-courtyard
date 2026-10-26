import http from 'node:http'
import path from 'node:path'
import { readFile } from 'node:fs/promises'

const root = path.resolve(import.meta.dirname, '../web/dist')
const port = Number(process.env.AI3D_TEST_PORT || 4188)
const prefix = process.env.AI3D_TEST_BASE_PATH || '/'
if (!prefix.startsWith('/') || !prefix.endsWith('/') || prefix.includes('..')) throw new Error('Invalid preview prefix')
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.glb': 'model/gltf-binary', '.png': 'image/png', '.wasm': 'application/wasm', '.md': 'text/markdown; charset=utf-8' }
const server = http.createServer(async (req, res) => {
  if (!['GET', 'HEAD'].includes(req.method)) { res.writeHead(405).end(); return }
  try {
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname)
    if (!pathname.startsWith(prefix)) { res.writeHead(404).end(); return }
    const name = pathname.slice(prefix.length) || 'index.html'
    const target = path.resolve(root, name)
    if (!target.startsWith(root + path.sep) || name.includes('\\') || target.endsWith('.import')) { res.writeHead(403).end(); return }
    const bytes = await readFile(target)
    res.writeHead(200, { 'Content-Type': types[path.extname(target)] || 'application/octet-stream', 'Cache-Control': 'no-store' })
    res.end(req.method === 'HEAD' ? undefined : bytes)
  } catch { res.writeHead(404).end() }
})
server.listen(port, '127.0.0.1', () => console.log(`Public asset preview: http://127.0.0.1:${port}${prefix}`))
