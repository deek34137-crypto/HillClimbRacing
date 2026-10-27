#!/usr/bin/env python3
"""
Injects the CrazyGames SDK v2 into a Godot 4 Web export HTML file.
Also hooks into the Godot engine lifecycle for:
  - sdkGameLoadingStop() — when game finishes loading
  - gameplayStart() / gameplayStop() — when gameplay begins/pauses
"""

import sys
import re

def inject_sdk(html_path: str) -> None:
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Inject SDK script tag in <head>
    sdk_script = (
        '\n    <!-- CrazyGames SDK v2 -->\n'
        '    <script src="https://sdk.crazygames.com/crazygames-sdk-v2.js"></script>\n'
    )
    if "crazygames-sdk" in content:
        print("✅ CrazyGames SDK already present, skipping injection.")
        return

    content = content.replace("</head>", sdk_script + "</head>", 1)

    # 2. Inject lifecycle hooks — inserted just before engine.startGame()
    lifecycle_js = """
    <!-- CrazyGames SDK Lifecycle Hooks -->
    <script>
    (function() {
        var _sdk = function() { return window.CrazyGames && window.CrazyGames.SDK; };

        // Called once Godot's engine has fully loaded
        function onGameLoaded() {
            var sdk = _sdk();
            if (sdk && sdk.game) {
                sdk.game.sdkGameLoadingStop();
                console.log('[CrazyGames] sdkGameLoadingStop called');
            }
            // Signal gameplay start after loading
            onGameplayStart();
        }

        // Called when gameplay begins (level starts, resumed from pause)
        function onGameplayStart() {
            var sdk = _sdk();
            if (sdk && sdk.game) {
                sdk.game.gameplayStart();
                console.log('[CrazyGames] gameplayStart called');
            }
        }

        // Called when gameplay pauses (menu open, ad showing)
        function onGameplayStop() {
            var sdk = _sdk();
            if (sdk && sdk.game) {
                sdk.game.gameplayStop();
                console.log('[CrazyGames] gameplayStop called');
            }
        }

        // Pause/resume when tab visibility changes
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                onGameplayStop();
            } else {
                onGameplayStart();
            }
        });

        // Expose globally so GDScript can call via JavaScriptBridge
        window.CrazyGamesHooks = {
            gameLoaded: onGameLoaded,
            gameplayStart: onGameplayStart,
            gameplayStop: onGameplayStop,
            requestMidrollAd: function(onComplete) {
                var sdk = _sdk();
                if (!sdk || !sdk.ad) {
                    if (onComplete) onComplete();
                    return;
                }
                sdk.ad.requestAd('midgame', {
                    adStarted:  function() { onGameplayStop(); },
                    adFinished: function() { onGameplayStart(); if (onComplete) onComplete(); },
                    adError:    function() { onGameplayStart(); if (onComplete) onComplete(); }
                });
            }
        };

        // Hook into Godot engine start
        document.addEventListener('DOMContentLoaded', function() {
            var origStartGame = null;
            // Wait for Godot's engine object to be available
            var interval = setInterval(function() {
                if (typeof Engine !== 'undefined') {
                    clearInterval(interval);
                    var origInit = Engine.prototype.startGame;
                    Engine.prototype.startGame = function() {
                        var result = origInit.apply(this, arguments);
                        if (result && typeof result.then === 'function') {
                            result.then(onGameLoaded);
                        } else {
                            onGameLoaded();
                        }
                        return result;
                    };
                }
            }, 100);
        });
    })();
    </script>
"""

    # Insert before </body>
    content = content.replace("</body>", lifecycle_js + "\n</body>", 1)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ CrazyGames SDK injected into: {html_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: inject_crazygames_sdk.py <path/to/index.html>")
        sys.exit(1)
    inject_sdk(sys.argv[1])
