import { Client } from '@modelcontextprotocol/sdk/client/index.js'
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js'
import { spawn } from 'node:child_process'
import { copyFile, mkdir, writeFile } from 'node:fs/promises'
import path from 'node:path'

const root = path.resolve(import.meta.dirname, '..')
const godot = path.join(process.env.LOCALAPPDATA, 'Programs', 'Godot', '4.7.2', 'Godot_v4.7.2-stable_win64.exe')
const evidence = path.join(root, 'evidence', 'screenshots')
const logPath = path.join(root, 'evidence', 'mcp', 'godot-mcp-e2e.json')
await mkdir(evidence, { recursive: true })
await mkdir(path.dirname(logPath), { recursive: true })

const transport = new StdioClientTransport({
  command: 'C:\\Program Files\\nodejs\\npx.cmd',
  args: ['-y', 'godot-mcp-runtime@3.2.2'],
  env: { ...process.env, GODOT_PATH: godot, GODOT_MCP_STRICT: 'true' },
})
const client = new Client({ name: 'ai3d-godot-gate', version: '1.0.0' })
const calls = []
let game = null

function textOf(result) {
  return (result.content ?? []).filter((item) => item.type === 'text').map((item) => item.text).join('\n')
}

async function call(name, args = {}) {
  const started = Date.now()
  const result = await client.callTool({ name, arguments: args })
  calls.push({ name, args, elapsedMs: Date.now() - started, isError: Boolean(result.isError), text: textOf(result), structuredContent: result.structuredContent ?? null })
  if (result.isError) throw new Error(`${name}: ${textOf(result)}`)
  return result
}

async function preserveScreenshot(result, filename) {
  const text = textOf(result)
  const source = result.structuredContent?.path ?? (() => { try { return JSON.parse(text).path } catch { return null } })()
  if (!source) throw new Error(`Screenshot path missing: ${text}`)
  const destination = path.join(evidence, filename)
  await copyFile(source, destination)
  return destination
}

try {
  await client.connect(transport)
  await call('get_project_info', { projectPath: root })
  await call('create_scene', { projectPath: root, scenePath: 'evidence/tmp/godot_mcp_write_test.tscn', rootNodeType: 'Node3D', rootNodeName: 'MCP_Write_Test' })
  await call('validate', { projectPath: root, scenePath: 'game/scenes/main.tscn' })
  await call('validate', { projectPath: root, scriptPath: 'game/scripts/main.gd' })
  await call('validate', { projectPath: root, scriptPath: 'game/scripts/player_controller.gd' })

  const attachPromise = call('attach_project', { projectPath: root, bridgePort: 27654 })
  await new Promise((resolve) => setTimeout(resolve, 900))
  game = spawn(godot, ['--path', root], { stdio: 'ignore', windowsHide: false })
  await attachPromise

  const day = await call('take_screenshot', { responseMode: 'path_only', timeout: 10000 })
  const dayPath = await preserveScreenshot(day, 'godot-day.png')
  await call('simulate_input', { actions: [
    { type: 'key', key: 'W', pressed: true }, { type: 'wait', ms: 1000 }, { type: 'key', key: 'W', pressed: false },
    { type: 'key', key: 'Space', pressed: true }, { type: 'wait', ms: 100 }, { type: 'key', key: 'Space', pressed: false },
  ] })
  const ui = await call('get_ui_elements', { visibleOnly: true })
  const state = await call('run_script', { script: `extends RefCounted\nfunc execute(scene_tree: SceneTree) -> Variant:\n\tvar root = scene_tree.current_scene\n\tvar player = root.get_node_or_null("Player")\n\treturn {"scene": root.name, "player_position": player.global_position if player else Vector3.ZERO}\n` })
  await call('simulate_input', { actions: [
    { type: 'key', key: 'L', pressed: true }, { type: 'wait', ms: 100 }, { type: 'key', key: 'L', pressed: false }, { type: 'wait', ms: 500 },
  ] })
  const night = await call('take_screenshot', { responseMode: 'path_only', timeout: 10000 })
  const nightPath = await preserveScreenshot(night, 'godot-night.png')
  await call('simulate_input', { actions: [{ type: 'wait', ms: 30000 }] })
  const finalShot = await call('take_screenshot', { responseMode: 'path_only', timeout: 10000 })
  await call('detach_project', {})
  const report = { status: 'pass', dayPath, nightPath, ui: ui.structuredContent ?? textOf(ui), state: state.structuredContent ?? textOf(state), finalScreenshot: textOf(finalShot), calls }
  await writeFile(logPath, JSON.stringify(report, null, 2), 'utf8')
  console.log(JSON.stringify({ status: 'pass', dayPath, nightPath, calls: calls.map(({ name, isError, elapsedMs }) => ({ name, isError, elapsedMs })) }))
} catch (error) {
  const report = { status: 'fail', error: String(error), calls }
  await writeFile(logPath, JSON.stringify(report, null, 2), 'utf8')
  console.error(JSON.stringify(report))
  process.exitCode = 1
} finally {
  if (game && !game.killed) game.kill()
  await client.close().catch(() => {})
}
