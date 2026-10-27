## CrazyGames SDK Bridge for Godot 4
## Provides a GDScript API to interact with the CrazyGames SDK via JavaScriptBridge.
## Works only on Web export; all calls are no-ops on other platforms.
##
## Usage:
##   CrazyGamesSDK.request_midroll_ad()
##   CrazyGamesSDK.gameplay_start()
##   CrazyGamesSDK.gameplay_stop()
##
## Add this as an Autoload in Project Settings (optional).

extends Node

## Emitted when a mid-roll ad has finished (or failed) — resume gameplay.
signal ad_finished

## True when running inside a browser (Web export)
var is_web: bool = OS.get_name() == "Web"


func _ready() -> void:
	if is_web:
		print("[CrazyGames] SDK Bridge initialized (Web platform)")
	else:
		print("[CrazyGames] SDK Bridge: non-web platform, all calls are no-ops")


## Call this when gameplay starts (level loaded, game resumed)
func gameplay_start() -> void:
	if not is_web:
		return
	JavaScriptBridge.eval("window.CrazyGamesHooks && window.CrazyGamesHooks.gameplayStart();")


## Call this when gameplay pauses (pause menu, shop, etc.)
func gameplay_stop() -> void:
	if not is_web:
		return
	JavaScriptBridge.eval("window.CrazyGamesHooks && window.CrazyGamesHooks.gameplayStop();")


## Call this when the game has fully loaded (auto-called by HTML hooks,
## but you can call it manually too)
func game_loaded() -> void:
	if not is_web:
		return
	JavaScriptBridge.eval("window.CrazyGamesHooks && window.CrazyGamesHooks.gameLoaded();")


## Request a mid-roll ad. Pauses gameplay, shows ad, emits ad_finished when done.
## Connect to the ad_finished signal to resume gameplay logic.
func request_midroll_ad() -> void:
	if not is_web:
		emit_signal("ad_finished")
		return

	gameplay_stop()

	# Use a JS callback that calls back into Godot via a global flag
	JavaScriptBridge.eval("""
		window._godotAdDone = false;
		window.CrazyGamesHooks && window.CrazyGamesHooks.requestMidrollAd(function() {
			window._godotAdDone = true;
		});
	""")

	# Poll until ad is done (runs in _process via a timer)
	_poll_ad_completion()


func _poll_ad_completion() -> void:
	# Wait up to 60 seconds for ad to complete
	var timeout := 60.0
	var elapsed := 0.0
	var timer := get_tree().create_timer(0.25)

	while elapsed < timeout:
		await timer.timeout
		elapsed += 0.25

		var done: bool = bool(JavaScriptBridge.eval("!!window._godotAdDone"))
		if done:
			JavaScriptBridge.eval("window._godotAdDone = false;")
			gameplay_start()
			emit_signal("ad_finished")
			return

		timer = get_tree().create_timer(0.25)

	# Timed out — resume anyway
	gameplay_start()
	emit_signal("ad_finished")
