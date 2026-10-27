#!/usr/bin/env python3
"""
Injects into a Godot 4 Web export HTML file:
1. coi-serviceworker (enables Cross-Origin Isolation & SharedArrayBuffer on GitHub Pages / static hosts)
2. CrazyGames SDK v2 + lifecycle hooks
"""

import sys
import os
import shutil
from pathlib import Path

def inject_sdk(html_path: str) -> None:
    html_file = Path(html_path)
    if not html_file.exists():
        print(f"❌ HTML file not found: {html_path}")
        sys.exit(1)

    export_dir = html_file.parent

    # 1. Copy coi-serviceworker.min.js if available
    script_dir = Path(__file__).resolve().parent
    coi_source = script_dir / "coi-serviceworker.min.js"
    if coi_source.exists():
        shutil.copy(coi_source, export_dir / "coi-serviceworker.min.js")
        print(f"✅ Copied coi-serviceworker.min.js to {export_dir}")

    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 2. Inject coi-serviceworker at the very top of <head>
    if "coi-serviceworker.min.js" not in content and (export_dir / "coi-serviceworker.min.js").exists():
        coi_tag = '<script src="coi-serviceworker.min.js"></script>\n'
        content = content.replace("<head>", f"<head>\n    {coi_tag}", 1)
        print("✅ Injected coi-serviceworker tag into <head>")

    # 3. Inject CrazyGames SDK script tag in <head>
    if "crazygames-sdk" not in content:
        sdk_script = (
            '\n    <!-- CrazyGames SDK v2 -->\n'
            '    <script src="https://sdk.crazygames.com/crazygames-sdk-v2.js"></script>\n'
        )
        content = content.replace("</head>", sdk_script + "</head>", 1)
        print("✅ Injected CrazyGames SDK into <head>")

    # 4. Inject lifecycle hooks before </body>
    if "CrazyGamesHooks" not in content:
        lifecycle_js = """
    <!-- CrazyGames SDK Lifecycle Hooks -->
    <script>
    (function() {
        var _sdk = function() { return window.CrazyGames && window.CrazyGames.SDK; };

        function onGameLoaded() {
            var sdk = _sdk();
            if (sdk && sdk.game) {
                sdk.game.sdkGameLoadingStop();
                console.log('[CrazyGames] sdkGameLoadingStop called');
            }
            onGameplayStart();
        }

        function onGameplayStart() {
            var sdk = _sdk();
            if (sdk && sdk.game) {
                sdk.game.gameplayStart();
                console.log('[CrazyGames] gameplayStart called');
            }
        }

        function onGameplayStop() {
            var sdk = _sdk();
            if (sdk && sdk.game) {
                sdk.game.gameplayStop();
                console.log('[CrazyGames] gameplayStop called');
            }
        }

        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                onGameplayStop();
            } else {
                onGameplayStart();
            }
        });

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

        document.addEventListener('DOMContentLoaded', function() {
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
        content = content.replace("</body>", lifecycle_js + "\n</body>", 1)
        print("✅ Injected CrazyGames lifecycle hooks before </body>")

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"🎉 Fully prepared HTML build: {html_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: inject_crazygames_sdk.py <path/to/index.html>")
        sys.exit(1)
    inject_sdk(sys.argv[1])
