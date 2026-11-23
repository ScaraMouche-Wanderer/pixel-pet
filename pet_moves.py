"""Pet-specific poses and the small pixel props that move with them."""
import math
import random
from typing import NamedTuple


MOVE_DURATION = 2.2


class Move(NamedTuple):
    name: str
    pose: str
    prop: str
    path: str
    color: str
    count: int = 3


MOVES = {
    'cat': (Move('Constellation stretch', 'stretch', 'spark', 'orbit', '#c6adff', 5),
            Move('Meteor pounce', 'jumping', 'comet', 'shower', '#9cddff'),
            Move('Nebula knead', 'groom', 'nebula', 'spiral', '#ed9cff', 5),
            Move('Lunar leap', 'jumping', 'saturn', 'arc', '#b4b7ff', 1)),
    'cat-classic': (Move('Bat the yarn', 'waving', 'yarn', 'bounce', '#ec87a1', 1),
                    Move('Butterfly watch', 'crouch-right', 'butterfly', 'flutter', '#ffc170', 2),
                    Move('Chase the mouse', 'running', 'mouse', 'scurry', '#bba69e', 1),
                    Move('Ribbon swat', 'waving', 'bow', 'ribbon', '#ff96ad', 3)),
    'monkey': (Move('Banana juggle', 'trick-right', 'banana', 'juggle', '#ffd457'),
               Move('Vine shake', 'tail-hang', 'frond', 'flutter', '#89ce69', 4),
               Move('Coconut toss', 'jumping', 'nut', 'arc', '#c18d5a', 2),
               Move('Blossom swing', 'swing-right', 'bloom', 'spiral', '#ffa4ad', 4)),
    'eagle': (Move('Thermal spiral', 'trick-glide-right', 'gust', 'orbit', '#a6dfef'),
              Move('River strike', 'trick-land-right', 'fish', 'splash', '#77d6ed', 2),
              Move('Cliff dive', 'trick-land-right', 'talon', 'swoop', '#fac973', 2),
              Move('Summit soar', 'trick-takeoff-right', 'cloud', 'ribbon', '#d3eafa', 3)),
    'owl': (Move('Moonlit glide', 'trick-glide-right', 'moon', 'rise', '#ffe3a2', 2),
            Move('Moth patrol', 'preen', 'moth', 'flutter', '#ddc8ec'),
            Move('Twilight blink', 'waiting', 'twinkle', 'pulse', '#b5b3ff', 4),
            Move('Silent wingbeat', 'trick-flap-right', 'plume', 'swoop', '#ccc1ff', 3)),
    'hoots': (Move('Hoot echoes', 'trick-flap-right', 'echo', 'pulse', '#f7c681'),
              Move('Downy drift', 'preen', 'down', 'flutter', '#ecd6aa', 4),
              Move('Acorn patrol', 'trick-glide-right', 'acorn', 'arc', '#d6aa67', 2),
              Move('Lantern flight', 'trick-takeoff-right', 'lantern', 'spiral', '#ffcb62', 4)),
    'codex': (Move('Type a command', 'review', 'prompt', 'type', '#8df1b5', 4),
              Move('Compile sparks', 'running', 'braces', 'rise', '#aabaff'),
              Move('Trace a circuit', 'running', 'chip', 'scan', '#9fe3bc', 3),
              Move('Patch parade', 'review', 'patch', 'ribbon', '#cab8ff', 4)),
    'dewey': (Move('Puddle splash', 'jumping', 'drop', 'splash', '#71dfff', 6),
              Move('Bubble float', 'waving', 'bubble', 'rise', '#abedff', 4),
              Move('Rain dance', 'jumping', 'rain', 'shower', '#8ad9ff', 6),
              Move('Ripple rings', 'waiting', 'ring', 'ripple', '#9ceefe', 4)),
    'fireball': (Move('Ember sneeze', 'failed', 'ember', 'shower', '#ff9348', 5),
                 Move('Flame halo', 'jumping', 'flame', 'orbit', '#ffd55e', 4),
                 Move('Cinder cyclone', 'jumping', 'cinder', 'spiral', '#ffac50', 6),
                 Move('Lava leap', 'jumping', 'lava', 'arc', '#ff694f', 4)),
    'rocky': (Move('Pebble tumble', 'jumping', 'pebble', 'bounce', '#c7a783', 4),
              Move('Crystal glint', 'review', 'crystal', 'pulse', '#c9b0fb'),
              Move('Fossil dig', 'waving', 'fossil', 'rise', '#e6c49e', 2),
              Move('Fault tremor', 'failed', 'crack', 'ripple', '#d5a87b', 4)),
    'seedy': (Move('Leaf fall', 'waving', 'leaf', 'flutter', '#83c85a', 4),
              Move('Fruit drop', 'jumping', 'apple', 'drop', '#ef7764', 2),
              Move('Dandelion breeze', 'waving', 'tuft', 'ribbon', '#fff2cc', 5),
              Move('Petal swirl', 'review', 'petal', 'spiral', '#f29daa', 5)),
    'stacky': (Move('Restack blocks', 'review', 'block', 'stack', '#b8a1fa'),
               Move('Topple tower', 'failed', 'brick', 'bounce', '#8498c9'),
               Move('Domino run', 'running', 'domino', 'scurry', '#99c8e8', 5),
               Move('Tile fan', 'waving', 'tile', 'arc', '#e8addd', 4)),
    'bsod': (Move('Error cascade', 'failed', 'error', 'shower', '#80baff', 4),
             Move('Reboot sequence', 'review', 'power', 'type', '#a4ebff'),
             Move('Memory scan', 'waiting', 'ram', 'scan', '#88c6ff', 3),
             Move('Dump bytes', 'failed', 'byte', 'drop', '#a7dcff', 4)),
    'null-signal': (Move('Signal sweep', 'waiting', 'signal', 'pulse', '#f47b97', 4),
                    Move('Static leak', 'failed', 'static', 'flutter', '#ca9fc1', 5),
                    Move('Antenna search', 'waiting', 'dish', 'scan', '#ea9cb6', 3),
                    Move('Lost packets', 'running', 'packet', 'swoop', '#cc98c4', 4)),
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
    'nebula': ('011001', '112110', '001211', '010110'),
    'saturn': ('001100', '012211', '111110', '001100'),
    'mouse': ('010100', '121110', '011111', '000001'),
    'bow': ('11011', '12121', '01310', '01010'),
    'nut': ('00300', '01110', '12111', '11111', '01110'),
    'bloom': ('01010', '11211', '02220', '11211', '01010'),
    'talon': ('10010', '10010', '11011', '02102'),
    'cloud': ('002200', '021120', '111111', '011110'),
    'twinkle': ('01001', '12100', '01000', '00010'),
    'plume': ('00011', '00121', '01210', '11000'),
    'acorn': ('00300', '22222', '11111', '01110', '00100'),
    'lantern': ('02220', '01010', '12221', '01110'),
    'chip': ('01010', '12221', '01110', '12221', '01010'),
    'patch': ('11111', '10201', '12221', '10201', '11111'),
    'rain': ('00001', '00010', '00100', '01000'),
    'ring': ('01110', '10001', '01110'),
    'cinder': ('00110', '01210', '11000'),
    'lava': ('00100', '01210', '12121', '11111', '01110'),
    'fossil': ('01110', '12001', '10111', '01100'),
    'crack': ('00010', '00100', '01110', '01000', '10000'),
    'tuft': ('20102', '02120', '00200', '00300', '03000'),
    'petal': ('01110', '12210', '01100', '01000'),
    'domino': ('111', '121', '111', '121', '111'),
    'tile': ('00200', '02110', '21111', '01110', '00100'),
    'ram': ('222222', '121211', '111111', '030303'),
    'byte': ('01110', '12001', '11111'),
    'dish': ('10001', '01110', '00100', '01110'),
    'packet': ('22221', '12111', '11211', '11111'),
}


def move_particles(move, art):
    """Use desktop coordinates so falling objects stay where they were released."""
    size = max(12, art.height())
    return [dict(kind=move.prop, color=move.color, path=move.path, index=i, count=move.count,
                 x=art.center().x(), y=art.top(), origin_x=art.center().x(), origin_y=art.top(),
                 size=size, phase=random.uniform(-.3, .3), life=MOVE_DURATION, duration=MOVE_DURATION)
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
    elif path == 'spiral':
        radius = .12 + .66 * t
        x, y = radius * math.cos(2 * angle), .52 - t * .62 + radius * .45 * math.sin(2 * angle)
    elif path == 'arc':
        x, y = (t - .5) * 1.6 + spread * .3, .74 - (1 - (2 * t - 1) ** 2) * (.65 + i * .09)
    elif path == 'scurry':
        x, y = (t - .5) * 1.8 + spread * .25, .88 - .12 * abs(math.sin(3 * angle))
    elif path == 'ribbon':
        x, y = (t - .5) * 1.4 + spread * .4, .14 + .20 * math.sin(2 * angle)
    elif path == 'swoop':
        x, y = (t - .5) * 1.5 + spread * .3, -.12 + .92 * math.sin(math.pi * t)
    elif path == 'scan':
        x, y = .65 * math.sin(2 * math.pi * t), .04 + i * .21
    elif path == 'ripple':
        x, y = spread * (.1 + 1.1 * t), .87 + .08 * math.cos(angle + t * 8)
    else:  # stack
        x, y = .48, min(.9 - i * .15, -.45 + 3 * max(0, t - i * .12) ** 2)
    item['x'] = item['origin_x'] + x * size
    item['y'] = item['origin_y'] + y * size
