import { mkdir, writeFile } from 'node:fs/promises'
import path from 'node:path'

const root = path.resolve(import.meta.dirname, '..')
const directory = path.join(root, 'node_modules')
await mkdir(directory, { recursive: true })
await writeFile(path.join(directory, '.gdignore'), '# Keep Godot from scanning JavaScript dependencies.\n', 'utf8')
console.log('Godot dependency scan guard ready.')
