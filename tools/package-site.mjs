import path from 'node:path'
import { cp, readFile, readdir, unlink } from 'node:fs/promises'
import crypto from 'node:crypto'
const root = path.resolve(import.meta.dirname, '..')
const output = path.join(root, 'web/dist')
for (const name of await readdir(output)) {
  // Remove only generated Godot sidecars copied by Vite's publicDir.
  if (name.endsWith('.import')) await unlink(path.join(output, name))
}
for (const name of ['LICENSE', 'THIRD_PARTY_NOTICES.md', 'licenses']) await cp(path.join(root, name), path.join(output, name), { recursive: true })
for (const name of ['future_courtyard_environment.glb', 'future_courtyard_character.glb']) {
  const original = await readFile(path.join(root, 'assets/runtime', name))
  const published = await readFile(path.join(output, name))
  if (!original.equals(published)) throw new Error(`Web copy differs: ${name}`)
  console.log(`${name} SHA256 ${crypto.createHash('sha256').update(published).digest('hex')}`)
}
