// Inspect the checked-in canonical pair. Never builds, rewrites or promotes assets.
import { createRequire } from 'node:module'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import crypto from 'node:crypto'
const require = createRequire(import.meta.url)
const validator = require('gltf-validator')
const root = path.resolve(import.meta.dirname, '..')
const manifest = JSON.parse(await readFile(path.join(root, 'assets/manifests/future_courtyard.manifest.json'), 'utf8'))
const files = []
for (const kind of ['environment', 'character']) {
  const entry = manifest.runtime.assets[kind]
  const filename = path.resolve(root, entry.path)
  if (!filename.startsWith(path.join(root, 'assets/runtime') + path.sep)) throw new Error('Asset path escaped canonical directory')
  const bytes = await readFile(filename)
  const sha256 = crypto.createHash('sha256').update(bytes).digest('hex')
  if (sha256 !== entry.sha256) throw new Error(`Canonical hash mismatch: ${kind}`)
  const report = await validator.validateBytes(new Uint8Array(bytes), { uri: path.basename(filename) })
  files.push({ kind, path: entry.path, bytes: bytes.length, sha256, validator: report.validatorVersion, errors: report.issues.numErrors, warnings: report.issues.numWarnings, infos: report.issues.numInfos, hints: report.issues.numHints })
}
console.log(JSON.stringify({ scope: 'canonical GLB byte identity and Khronos validation only; no G0-G7 production claim', files, passed: files.every(x => x.errors === 0 && x.warnings === 0) }, null, 2))
if (files.some(x => x.errors || x.warnings)) process.exitCode = 1
