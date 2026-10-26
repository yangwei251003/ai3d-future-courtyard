import { Suspense, useEffect, useMemo, useRef, useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { Html, OrbitControls, useAnimations, useGLTF } from '@react-three/drei'
import { SkeletonUtils } from 'three/examples/jsm/Addons.js'
import * as THREE from 'three'

const clips = ['Idle_loop', 'Walk_loop', 'Run_loop', 'Jump'] as const
type ClipName = (typeof clips)[number]
type ThemeName = 'cyan' | 'orange'

function cloneAndTheme(source: THREE.Object3D, theme: ThemeName) {
  const clone = SkeletonUtils.clone(source)
  const accent = theme === 'cyan' ? new THREE.Color('#12d6c5') : new THREE.Color('#ff9a3d')
  const emission = theme === 'cyan' ? new THREE.Color('#ff3ea5') : new THREE.Color('#55ddff')
  clone.traverse((node) => {
    node.visible = !/-(colonly|navmesh)$/i.test(node.name)
    if (node instanceof THREE.Mesh) {
      const list = Array.isArray(node.material) ? node.material : [node.material]
      const cloned = list.map((material) => {
        const next = material.clone()
        if (next.name === 'MAT_Accent') next.color.copy(accent)
        if (next.name === 'MAT_Emission') {
          next.color.copy(emission)
          if ('emissive' in next) (next as THREE.MeshStandardMaterial).emissive.copy(emission)
        }
        return next
      })
      node.material = Array.isArray(node.material) ? cloned : cloned[0]
      node.castShadow = true
      node.receiveShadow = true
    }
  })
  return clone
}

function EnvironmentModel({ theme }: { theme: ThemeName }) {
  const gltf = useGLTF(`${import.meta.env.BASE_URL}future_courtyard_environment.glb`)
  const scene = useMemo(() => cloneAndTheme(gltf.scene, theme), [gltf.scene, theme])
  return <primitive object={scene} />
}

function CharacterModel({ clip, theme, reducedMotion }: { clip: ClipName; theme: ThemeName; reducedMotion: boolean }) {
  const group = useRef<THREE.Group>(null)
  const gltf = useGLTF(`${import.meta.env.BASE_URL}future_courtyard_character.glb`)
  const scene = useMemo(() => cloneAndTheme(gltf.scene, theme), [gltf.scene, theme])
  const { actions } = useAnimations(gltf.animations, group)

  useEffect(() => {
    Object.values(actions).forEach((action) => action?.stop())
    const active = actions[clip]
    if (!active || reducedMotion) return
    active.reset().fadeIn(0.15).play()
    active.setLoop(clip === 'Jump' ? THREE.LoopOnce : THREE.LoopRepeat, clip === 'Jump' ? 1 : Infinity)
    active.clampWhenFinished = clip === 'Jump'
    return () => { active.fadeOut(0.15) }
  }, [actions, clip, reducedMotion])

  return <group ref={group} position={[0, 0, 4]}><primitive object={scene} /></group>
}

function Loading() {
  return <Html center><div className="loading">载入规范 GLB…</div></Html>
}

function Scene({ clip, theme, night, reducedMotion, mobile }: { clip: ClipName; theme: ThemeName; night: boolean; reducedMotion: boolean; mobile: boolean }) {
  return (
    <>
      <color attach="background" args={[night ? '#050812' : '#18202a']} />
      <ambientLight intensity={night ? 0.25 : 0.75} />
      <directionalLight castShadow={!mobile} position={[7, 12, 8]} intensity={night ? 0.45 : 2.2} color={night ? '#7fa8ff' : '#fff2d4'} />
      <pointLight position={[0, 4, 0]} intensity={night ? 28 : 4} color={theme === 'cyan' ? '#ff3ea5' : '#55ddff'} distance={20} />
      <Suspense fallback={<Loading />}>
        <EnvironmentModel theme={theme} />
        <CharacterModel clip={clip} theme={theme} reducedMotion={reducedMotion} />
      </Suspense>
      <OrbitControls makeDefault target={[0, 1.2, 0]} minDistance={7} maxDistance={38} maxPolarAngle={Math.PI / 2.05} />
    </>
  )
}

export function App() {
  const forceFallback = new URLSearchParams(location.search).get('forceFallback') === '1'
  const [clip, setClip] = useState<ClipName>('Idle_loop')
  const [theme, setTheme] = useState<ThemeName>('cyan')
  const [night, setNight] = useState(false)
  const mobile = matchMedia('(max-width: 640px)').matches
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches

  return (
    <main>
      <header className="hero">
        <div>
          <p className="eyebrow">CODEX → BLENDER → GLB → GODOT / WEB</p>
          <h1>低多边形未来庭院</h1>
          <p className="subtitle">同一份规范资产，两个实时运行端。</p>
        </div>
        <div className="status"><span /> 运行资产已连接</div>
      </header>
      <section className="viewer" aria-label="三维庭院查看器">
        {forceFallback ? (
          <img className="fallback" src={`${import.meta.env.BASE_URL}future_courtyard_poster.png`} alt="未来庭院静态预览" />
        ) : (
          <Canvas shadows={!mobile} dpr={mobile ? 1 : [1, 1.5]} camera={{ position: [15, 12, 17], fov: 42 }} gl={{ antialias: !mobile, powerPreference: 'high-performance' }}>
            <Scene clip={clip} theme={theme} night={night} reducedMotion={reducedMotion} mobile={mobile} />
          </Canvas>
        )}
        <div className="controls" aria-label="查看器控制">
          <div className="control-group">
            <span>动画</span>
            <div className="button-row">
              {clips.map((name) => <button key={name} className={clip === name ? 'active' : ''} onClick={() => setClip(name)}>{name.replace('_loop', '')}</button>)}
            </div>
          </div>
          <div className="control-group compact">
            <button onClick={() => setTheme(theme === 'cyan' ? 'orange' : 'cyan')}>配色：{theme === 'cyan' ? '青色' : '橙色'}</button>
            <button onClick={() => setNight(!night)}>{night ? '切换白昼' : '切换夜景'}</button>
          </div>
        </div>
      </section>
      <footer>
        <span>鼠标拖动旋转 · 滚轮缩放</span>
        <span>资产预算：≤3 MiB · ≤25k 三角面</span>
      </footer>
    </main>
  )
}

useGLTF.preload(`${import.meta.env.BASE_URL}future_courtyard_environment.glb`)
useGLTF.preload(`${import.meta.env.BASE_URL}future_courtyard_character.glb`)
