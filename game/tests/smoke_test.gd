extends SceneTree

var failures: Array[String] = []


func _initialize() -> void:
    call_deferred("_run")


func assert_true(value: bool, message: String) -> void:
    if not value:
        failures.append(message)
        push_error(message)


func _run() -> void:
    var packed := load("res://game/scenes/main.tscn") as PackedScene
    assert_true(packed != null, "main scene loads")
    if packed == null:
        quit(1)
        return
    var scene := packed.instantiate()
    root.add_child(scene)
    for _frame in range(20):
        await physics_frame
    var player := scene.get_node_or_null("Player") as CharacterBody3D
    assert_true(player != null, "player exists")
    assert_true(scene.get_node_or_null("CanonicalEnvironment") != null, "canonical environment exists")
    assert_true(scene.get_node_or_null("RuntimeNavigationRegion") != null, "navigation region exists")
    assert_true(scene.get_node_or_null("NavigationDrone") != null, "navigation drone exists")
    if player:
        var start := player.global_position
        Input.action_press("move_forward")
        for _frame in range(60):
            await physics_frame
        Input.action_release("move_forward")
        var distance := Vector2(player.global_position.x - start.x, player.global_position.z - start.z).length()
        assert_true(distance > 2.2 and distance < 3.8, "walk distance is %.3f m" % distance)
        Input.action_press("jump")
        await physics_frame
        Input.action_release("jump")
        var peak := player.global_position.y
        for _frame in range(120):
            await physics_frame
            peak = max(peak, player.global_position.y)
        assert_true(peak - 0.95 > 0.8, "jump height is %.3f m" % (peak - 0.95))
        assert_true(player.is_on_floor(), "player lands after jump")
        assert_true(player.has_meta("animation_state"), "animation state is exposed")
    scene.set_night_mode(true)
    assert_true(scene.night_mode, "night mode toggles")
    var result := {
        "status": "pass" if failures.is_empty() else "fail",
        "failures": failures,
        "playerPosition": player.global_position if player else Vector3.ZERO,
    }
    print("AI3D_GODOT_SMOKE ", JSON.stringify(result))
    quit(0 if failures.is_empty() else 1)

