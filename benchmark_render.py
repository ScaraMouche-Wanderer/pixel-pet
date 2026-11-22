"""Repeatable offscreen animation workload; not a compositor/FPS benchmark."""
import json
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import statistics
import tempfile
import time
from pathlib import Path
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from pet import Pet, Settings


def run_case(app, kind):
    with tempfile.TemporaryDirectory() as directory:
        pet = Pet(Settings(Path(directory) / 'state.json'), preview=True)
        pet.ticker.stop()
        pet.settings.data['autonomous'] = False
        now = [time.monotonic()]
        pet.mode_started, pet.mode_until, pet.last_tick = now[0], now[0], now[0]
        if kind == 'walk':
            pet.mode, pet.mode_until = 'running-right', now[0] + 20
        elif kind == 'nap':
            pet.companion.data['sleeping'] = True
        elif kind == 'bubble':
            pet.effects.say('A speech bubble moving with the pet.', 20)
        origin = pet.pos()
        latencies = []
        with patch('time.monotonic', side_effect=lambda: now[0]), \
                patch.object(pet, 'setMask', wraps=pet.setMask) as masks, \
                patch.object(pet.effects, 'show', wraps=pet.effects.show) as shows, \
                patch.object(pet.effects, 'update', wraps=pet.effects.update) as redraws:
            for index in range(250):
                now[0] += .04
                start = time.perf_counter_ns()
                if kind == 'bubble':
                    pet.move(origin.x() - index % 100, origin.y())
                pet.tick()
                app.processEvents()
                latencies.append((time.perf_counter_ns() - start) / 1e6)
            result = {'ticks': 250, 'window_mask_changes': masks.call_count,
                      'effects_show_calls': shows.call_count, 'effects_redraw_requests': redraws.call_count,
                      'mean_tick_ms': round(statistics.mean(latencies), 3),
                      'max_tick_ms': round(max(latencies), 3),
                      'p95_tick_ms': round(sorted(latencies)[237], 3),
                      'timer_interval_ms': pet.ticker.interval()}
        pet.tray.hide()
        pet.close()
        pet.effects.close()
        pet.ball.close()
        pet.firefly.close()
        pet.card.close()
        pet.deleteLater()
        app.processEvents()
        return result


if __name__ == '__main__':
    app = QApplication.instance() or QApplication([])
    print(json.dumps({kind: run_case(app, kind) for kind in ('idle', 'walk', 'nap', 'bubble')}, indent=2))
