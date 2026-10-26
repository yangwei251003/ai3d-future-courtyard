extends CharacterBody3D

const WALK_SPEED := 3.0
const RUN_SPEED := 6.0
const JUMP_VELOCITY := 5.0
const CROSS_FADE := 0.15

var gravity: float = float(ProjectSettings.get_setting("physics/3d/default_gravity", 9.8))
var visual: Node3D
var camera_arm: SpringArm3D
var animation_tree: AnimationTree
var playback: AnimationNodeStateMachinePlayback
var current_state := "Idle"
var mouse_sensitivity := 0.0025


func _ready() -> void:
    visual = get_node("Visual")
    camera_arm = get_node("CameraArm")
    set_meta("animation_state", current_state)
    _setup_animation_tree()
    if not DisplayServer.get_name().contains("headless"):
        Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


func _physics_process(delta: float) -> void:
    if not is_on_floor():
        velocity.y -= gravity * delta
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = JUMP_VELOCITY

    var input_vector := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
    var direction := Vector3(input_vector.x, 0.0, input_vector.y).normalized()
    var running := Input.is_action_pressed("run")
    var speed := RUN_SPEED if running else WALK_SPEED
    if direction != Vector3.ZERO:
        velocity.x = direction.x * speed
        velocity.z = direction.z * speed
        visual.rotation.y = lerp_angle(visual.rotation.y, atan2(direction.x, direction.z), min(1.0, delta * 10.0))
    else:
        velocity.x = move_toward(velocity.x, 0.0, speed * 5.0 * delta)
        velocity.z = move_toward(velocity.z, 0.0, speed * 5.0 * delta)
    move_and_slide()
    _update_animation(direction, running)


func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
        camera_arm.rotation.y -= event.relative.x * mouse_sensitivity
        camera_arm.rotation.x = clamp(camera_arm.rotation.x - event.relative.y * mouse_sensitivity, deg_to_rad(-55), deg_to_rad(10))
    elif event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
        Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
    elif event is InputEventMouseButton and event.pressed:
        Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


func _update_animation(direction: Vector3, running: bool) -> void:
    var desired := "Idle"
    if not is_on_floor():
        desired = "Jump"
    elif direction != Vector3.ZERO:
        desired = "Run" if running else "Walk"
    if desired == current_state:
        return
    current_state = desired
    set_meta("animation_state", current_state)
    if playback:
        playback.travel(current_state)


func _setup_animation_tree() -> void:
    var animation_player := _find_animation_player(visual)
    if animation_player == null:
        push_warning("Character GLB has no AnimationPlayer")
        return
    var clip_names := {}
    for animation_name in animation_player.get_animation_list():
        for desired_value in PackedStringArray(["Idle_loop", "Walk_loop", "Run_loop", "Jump"]):
            var desired: String = desired_value
            var imported_alias: String = desired.replace("_loop", "")
            if String(animation_name) == desired or String(animation_name) == imported_alias or String(animation_name).ends_with(desired):
                clip_names[desired] = animation_name
    if clip_names.size() != 4:
        push_warning("Expected four clips, found: %s" % [animation_player.get_animation_list()])

    animation_tree = AnimationTree.new()
    animation_tree.name = "AnimationTree"
    add_child(animation_tree)
    animation_tree.anim_player = animation_tree.get_path_to(animation_player)
    var machine := AnimationNodeStateMachine.new()
    var mapping := {"Idle": "Idle_loop", "Walk": "Walk_loop", "Run": "Run_loop", "Jump": "Jump"}
    for state_name in mapping:
        var node := AnimationNodeAnimation.new()
        node.animation = clip_names.get(mapping[state_name], mapping[state_name])
        machine.add_node(state_name, node)
    for from_state in mapping:
        for to_state in mapping:
            if from_state == to_state:
                continue
            var transition := AnimationNodeStateMachineTransition.new()
            transition.xfade_time = CROSS_FADE
            machine.add_transition(from_state, to_state, transition)
    animation_tree.tree_root = machine
    animation_tree.active = true
    playback = animation_tree.get("parameters/playback")
    playback.start("Idle")


func _find_animation_player(node: Node) -> AnimationPlayer:
    if node is AnimationPlayer:
        return node
    for child in node.get_children():
        var found := _find_animation_player(child)
        if found:
            return found
    return null
