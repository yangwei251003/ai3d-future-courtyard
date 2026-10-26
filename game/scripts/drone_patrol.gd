extends CharacterBody3D

var points := [
    Vector3(6, 0.65, 6),
    Vector3(6, 0.65, -4),
    Vector3(-5, 0.65, -4),
    Vector3(-5, 0.65, 6),
]
var index := 1
var speed := 1.8
var agent: NavigationAgent3D


func _ready() -> void:
    agent = get_node("NavigationAgent3D")
    call_deferred("_set_target")


func _physics_process(_delta: float) -> void:
    if agent == null or NavigationServer3D.map_get_iteration_id(get_world_3d().navigation_map) == 0:
        return
    if agent.is_navigation_finished():
        index = (index + 1) % points.size()
        _set_target()
    var next := agent.get_next_path_position()
    var direction := global_position.direction_to(next)
    velocity = Vector3(direction.x, 0, direction.z) * speed
    if velocity.length_squared() > 0.01:
        rotation.y = atan2(velocity.x, velocity.z)
    move_and_slide()


func _set_target() -> void:
    if agent:
        agent.target_position = points[index]

