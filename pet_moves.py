"""Pet-specific poses and the small pixel props that move with them."""
import math
import random
from typing import NamedTuple


class Move(NamedTuple):
    name: str
    pose: str
    prop: str
    path: str
    color: str
    count: int = 3


MOVES = {
    'cat': (Move('Constellation stretch', 'stretch', 'spark', 'orbit', '#c6adff', 5),
            Move('Meteor pounce', 'jumping', 'comet', 'shower', '#9cddff')),
    'cat-classic': (Move('Bat the yarn', 'waving', 'yarn', 'bounce', '#ec87a1', 1),
                    Move('Butterfly watch', 'crouch-right', 'butterfly', 'flutter', '#ffc170', 2)),
    'monkey': (Move('Banana juggle', 'trick-right', 'banana', 'juggle', '#ffd457'),
               Move('Vine shake', 'tail-hang', 'frond', 'flutter', '#89ce69', 4)),
    'eagle': (Move('Thermal spiral', 'trick-glide-right', 'gust', 'orbit', '#a6dfef'),
              Move('River strike', 'trick-land-right', 'fish', 'splash', '#77d6ed', 2)),
    'owl': (Move('Moonlit glide', 'trick-glide-right', 'moon', 'rise', '#ffe3a2', 2),
            Move('Moth patrol', 'preen', 'moth', 'flutter', '#ddc8ec')),
    'hoots': (Move('Hoot echoes', 'trick-flap-right', 'echo', 'pulse', '#f7c681'),
              Move('Downy drift', 'preen', 'down', 'flutter', '#ecd6aa', 4)),
    'codex': (Move('Type a command', 'review', 'prompt', 'type', '#8df1b5', 4),
              Move('Compile sparks', 'running', 'braces', 'rise', '#aabaff')),
    'dewey': (Move('Puddle splash', 'jumping', 'drop', 'splash', '#71dfff', 6),
              Move('Bubble float', 'waving', 'bubble', 'rise', '#abedff', 4)),
    'fireball': (Move('Ember sneeze', 'failed', 'ember', 'shower', '#ff9348', 5),
                 Move('Flame halo', 'jumping', 'flame', 'orbit', '#ffd55e', 4)),
    'rocky': (Move('Pebble tumble', 'jumping', 'pebble', 'bounce', '#c7a783', 4),
              Move('Crystal glint', 'review', 'crystal', 'pulse', '#c9b0fb')),
    'seedy': (Move('Leaf fall', 'waving', 'leaf', 'flutter', '#83c85a', 4),
              Move('Fruit drop', 'jumping', 'apple', 'drop', '#ef7764', 2)),
    'stacky': (Move('Restack blocks', 'review', 'block', 'stack', '#b8a1fa'),
               Move('Topple tower', 'failed', 'brick', 'bounce', '#8498c9')),
    'bsod': (Move('Error cascade', 'failed', 'error', 'shower', '#80baff', 4),
             Move('Reboot sequence', 'review', 'power', 'type', '#a4ebff')),
    'null-signal': (Move('Signal sweep', 'waiting', 'signal', 'pulse', '#f47b97', 4),
                    Move('Static leak', 'failed', 'static', 'flutter', '#ca9fc1', 5)),
}

# 1 is the prop colour, 2 a highlight, and 3 the stem or contrasting detail.
GLYPHS = {
    'spark': ('00100','00100','11211','00100','00100'),
    'comet': ('00001','00011','02210','21100','11000'),
    'yarn': ('01110','12111','11221','12111','0111011'),
    'butterfly': ('11011','12321','01310','11011'),
    'banana': ('00003','00011','20110','11100'),
    'frond': ('00101','01110','10100','01000'),
    'gust': ('001110','000021','111110','000000','011100'),
    'fish': ('0111001','1211111','0111001'),
    'moon': ('00110','01100','12100','01101','00110'),
    'moth': ('10001','21012','12321','01010'),
    'echo': ('10010','01001','01001','10010'),
    'down': ('00110','01211','01110','01000'),
    'prompt': ('10000','01000','00100','01000','10022'),
    'braces': ('0110110','0100010','1000001','0100010','0110110'),
    'drop': ('00100','01110','12110','01110'),
    'bubble': ('01110','12001','10001','10001','01110'),
    'ember': ('0010','0110','1211','0110'),
    'flame': ('01000','01101','11211','12211','01110'),
    'pebble': ('01100','12210','11111','01110'),
    'crystal': ('00100','01210','11211','01110','00100'),
    'leaf': ('00011','00121','01210','11100','30000'),
    'apple': ('000330','003000','011110','121111','111111','011110'),
    'block': ('22221','21111','21111','11111'),
    'brick': ('222221','211111','111111'),
    'error': ('11111','12021','11211','12021','11111'),
    'power': ('00200','10201','10001','10001','01110'),
    'signal': ('00001','00101','10101'),
    'static': ('011001','100100','001011'),
}


def move_particles(move, art):
    """Use desktop coordinates so falling objects stay where they were released."""
    size = max(12, art.height())
    return [dict(kind=move.prop, color=move.color, path=move.path, index=i, count=move.count,
                 x=art.center().x(), y=art.top(), origin_x=art.center().x(), origin_y=art.top(),
                 size=size, phase=random.uniform(-.3, .3), life=2.2, duration=2.2)
            for i in range(move.count)]


def advance_prop(item):
    i, count = item['index'], item['count']
    t = 1 - item['life'] / item['duration']
    spread = (i + .5) / count * 2 - 1
    angle = math.tau * (t + i / count)
    phase = item['phase']
    size = item['size']
    path = item['path']
    if path == 'flutter':
        x, y = spread * .55 + .18 * math.sin(angle * 2 + phase), -.14 + t * 1.15
    elif path == 'drop':
        x = spread * (.45 + .65 * t) + phase * .12
        y = min(.98, .07 + 2.7 * max(0, t - .18 * i) ** 2)
    elif path == 'bounce':
        x, y = spread * .4 + t * (.75 + phase), .94 - abs(math.sin(t * math.pi * 3)) * (1 - t)
    elif path == 'orbit':
        x, y = .68 * math.cos(angle), .28 + .45 * math.sin(angle)
    elif path == 'juggle':
        x, y = .55 * math.cos(angle), .48 - abs(math.sin(angle)) * .95
    elif path == 'splash':
        x, y = spread * t * 1.5, .8 - 3.7 * t * (1 - t)
    elif path == 'shower':
        x, y = spread * .65 + .75 * t, -.35 + 1.25 * t * t + phase
    elif path == 'rise':
        x, y = spread * .6 + .12 * math.sin(angle), .58 - t + phase
    elif path == 'pulse':
        x, y = .22 + t * .8 + spread * .2, .25 + spread * (.15 + t * .5)
    elif path == 'type':
        x, y = -.4 + i * .25, -.18 - .12 * math.sin(min(1, max(0, 4 * t - i * .45)) * math.pi)
    else:  # stack
        x, y = .48, min(.9 - i * .15, -.45 + 3 * max(0, t - i * .12) ** 2)
    item['x'] = item['origin_x'] + x * size
    item['y'] = item['origin_y'] + y * size
