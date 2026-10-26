extends Node3D

const ENVIRONMENT_SCENE := preload("res://assets/runtime/future_courtyard_environment.glb")
const CHARACTER_SCENE := preload("res://assets/runtime/future_courtyard_character.glb")
const PLAYER_SCRIPT := preload("res://game/scripts/player_controller.gd")
const DRONE_SCRIPT := preload("res://game/scripts/drone_patrol.gd")

var player: CharacterBody3D
var world_environment: WorldEnvironment
var sun: DirectionalLight3D
var accent_light: OmniLight3D
var debug_label: Label
var help_panel: PanelContainer
var night_mode := false


func _ready() -> void:
    _build_lighting()
    _build_environment()
    _build_navigation()
    _build_player()
    _build_drone()
    _build_ui()


func _process(_delta: float) -> void:
    if is_instance_valid(debug_label) and is_instance_valid(player):
        var state := str(player.get_meta("animation_state", "Idle"))
        debug_label.text = "状态: %s\n位置: (%.2f, %.2f, %.2f)\n模式: %s" % [
            state,
            player.global_position.x,
            player.global_position.y,
            player.global_position.z,
            "夜景" if night_mode else "白昼",
        ]


func _unhandled_input(event: InputEvent) -> void:
    if event.is_action_pressed("toggle_day_night"):
        set_night_mode(not night_mode)
    elif event.is_action_pressed("toggle_debug") and is_instance_valid(debug_label):
        debug_label.visible = not debug_label.visible


func _build_environment() -> void:
    var environment_instance := ENVIRONMENT_SCENE.instantiate()
    environment_instance.name = "CanonicalEnvironment"
    add_child(environment_instance)

    # Runtime collision is deliberately simple and deterministic. Imported
    # -colonly proxies remain part of the asset contract and are also inspected.
    _add_static_box("RuntimeGround", Vector3(0, -0.15, 0), Vector3(24, 0.3, 24))
    _add_static_box("RuntimeWallNorth", Vector3(0, 1.5, -10), Vector3(20, 3, 0.25))
    _add_static_box("RuntimeWallEast", Vector3(10, 1.5, 0), Vector3(0.25, 3, 20))
    _add_static_box("RuntimeWallWest", Vector3(-10, 1.5, 0), Vector3(0.25, 3, 20))
    _add_static_box("RuntimeWallSouthLeft", Vector3(-6, 1.5, 10), Vector3(8, 3, 0.25))
    _add_static_box("RuntimeWallSouthRight", Vector3(6, 1.5, 10), Vector3(8, 3, 0.25))
    _add_static_box("RuntimeFountain", Vector3(0, 0.6, 0), Vector3(4, 1.2, 4))


func _add_static_box(node_name: String, position: Vector3, size: Vector3) -> void:
    var body := StaticBody3D.new()
    body.name = node_name
    body.position = position
    var shape := CollisionShape3D.new()
    var box := BoxShape3D.new()
    box.size = size
    shape.shape = box
    body.add_child(shape)
    add_child(body)


func _build_navigation() -> void:
    var region := NavigationRegion3D.new()
    region.name = "RuntimeNavigationRegion"
    var navigation_mesh := NavigationMesh.new()
    navigation_mesh.vertices = PackedVector3Array([
        Vector3(-9.2, 0.05, -9.2),
        Vector3(9.2, 0.05, -9.2),
        Vector3(9.2, 0.05, 9.2),
        Vector3(-9.2, 0.05, 9.2),
    ])
    navigation_mesh.add_polygon(PackedInt32Array([0, 1, 2, 3]))
    region.navigation_mesh = navigation_mesh
    add_child(region)


func _build_player() -> void:
    player = CharacterBody3D.new()
    player.name = "Player"
    player.set_script(PLAYER_SCRIPT)
    player.position = Vector3(4, 0.95, 3.5)

    var collider := CollisionShape3D.new()
    collider.name = "PlayerCollider"
    var capsule := CapsuleShape3D.new()
    capsule.height = 1.8
    capsule.radius = 0.35
    collider.shape = capsule
    player.add_child(collider)

    var visual := Node3D.new()
    visual.name = "Visual"
    visual.add_child(CHARACTER_SCENE.instantiate())
    player.add_child(visual)

    var spring_arm := SpringArm3D.new()
    spring_arm.name = "CameraArm"
    spring_arm.spring_length = 4.0
    spring_arm.position.y = 1.4
    spring_arm.rotation.x = deg_to_rad(-15)
    var camera := Camera3D.new()
    camera.name = "Camera"
    camera.current = true
    spring_arm.add_child(camera)
    player.add_child(spring_arm)
    add_child(player)


func _build_drone() -> void:
    var drone := CharacterBody3D.new()
    drone.name = "NavigationDrone"
    drone.position = Vector3(6, 0.65, 6)
    drone.set_script(DRONE_SCRIPT)
    var mesh_instance := MeshInstance3D.new()
    var mesh := CylinderMesh.new()
    mesh.top_radius = 0.18
    mesh.bottom_radius = 0.42
    mesh.height = 0.18
    mesh.radial_segments = 8
    mesh_instance.mesh = mesh
    var material := StandardMaterial3D.new()
    material.albedo_color = Color("ff3ea5")
    material.emission_enabled = true
    material.emission = Color("ff3ea5")
    material.emission_energy_multiplier = 3.0
    mesh_instance.material_override = material
    drone.add_child(mesh_instance)
    var agent := NavigationAgent3D.new()
    agent.name = "NavigationAgent3D"
    agent.path_height_offset = 0.65
    agent.path_desired_distance = 0.25
    agent.target_desired_distance = 0.35
    drone.add_child(agent)
    add_child(drone)


func _build_lighting() -> void:
    world_environment = WorldEnvironment.new()
    world_environment.name = "WorldEnvironment"
    var environment := Environment.new()
    environment.background_mode = Environment.BG_COLOR
    environment.background_color = Color("18202a")
    environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    environment.ambient_light_color = Color("d8e6ff")
    environment.ambient_light_energy = 0.72
    world_environment.environment = environment
    add_child(world_environment)

    sun = DirectionalLight3D.new()
    sun.name = "Sun"
    sun.rotation_degrees = Vector3(-52, -32, 0)
    sun.light_energy = 1.6
    sun.shadow_enabled = true
    add_child(sun)

    accent_light = OmniLight3D.new()
    accent_light.name = "AccentLight"
    accent_light.position = Vector3(0, 3.5, 0)
    accent_light.omni_range = 15.0
    accent_light.light_color = Color("ff3ea5")
    accent_light.light_energy = 4.0
    add_child(accent_light)


func set_night_mode(enabled: bool) -> void:
    night_mode = enabled
    var environment := world_environment.environment
    environment.background_color = Color("050812") if enabled else Color("18202a")
    environment.ambient_light_color = Color("7294d8") if enabled else Color("d8e6ff")
    environment.ambient_light_energy = 0.28 if enabled else 0.72
    sun.light_energy = 0.2 if enabled else 1.6
    accent_light.light_energy = 9.0 if enabled else 4.0


func _build_ui() -> void:
    var canvas := CanvasLayer.new()
    canvas.name = "HUD"
    add_child(canvas)
    var margin := MarginContainer.new()
    margin.add_theme_constant_override("margin_left", 20)
    margin.add_theme_constant_override("margin_top", 20)
    margin.add_theme_constant_override("margin_right", 20)
    margin.add_theme_constant_override("margin_bottom", 20)
    canvas.add_child(margin)
    var column := VBoxContainer.new()
    margin.add_child(column)
    var title := Label.new()
    title.text = "未来庭院 · Godot 运行端"
    title.add_theme_font_size_override("font_size", 24)
    column.add_child(title)
    var help := Label.new()
    help.text = "WASD 移动 · Shift 奔跑 · Space 跳跃 · 鼠标环视 · L 昼夜 · F3 调试"
    help.modulate = Color("aab6c8")
    column.add_child(help)
    debug_label = Label.new()
    debug_label.name = "DebugStatus"
    debug_label.text = "状态: 初始化"
    debug_label.add_theme_color_override("font_color", Color("5cefe0"))
    column.add_child(debug_label)
