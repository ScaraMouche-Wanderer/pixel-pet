"""Small, local personality model; no background services or network calls."""
import math
import time

VOICES = {
    'cat': {
        'name': 'Mochi', 'treat_label': 'Fish treat', 'treat_art': 'fish',
        'moods': ('Focusing with you', 'Dreaming of tiny fish', 'A little sleepy',
                  'Thinking about snacks', 'Purring happily', 'Curious little companion'),
        'hello': 'Mrrp! This is my little corner.',
        'pet': 'Right behind the ears. Mrrp!',
        'treat': 'A fish! I accept this tribute.',
        'cuddle': 'Prrrrr. The good kind of stuck.',
        'jump': 'Four paws, zero gravity!',
        'nap': 'Time to curl up.', 'wake': 'Big stretch. Where is my yarn?',
        'idle': ('That yarn ball is plotting something.', 'This patch of sunlight is mine.'),
        'focus': '{minutes} minutes. I’ll keep your spot warm.',
        'follow': 'I’m right behind you. Quiet paws and all.',
        'rename': 'That name sounds good in a purr.',
        'finish': 'Stretch time. I’ll show you how.',
    },
    'monkey': {
        'name': 'Pip', 'treat_label': 'Banana slice', 'treat_art': 'banana',
        'moods': ('Keeping the grove quiet', 'Dozing on a branch', 'Taking a break from climbing',
                  'Looking for bananas', 'Grinning ear to ear', 'Scouting the next branch'),
        'hello': 'Hi! Want to see how high I can climb?',
        'pet': 'Ooh! A tiny head pat!',
        'treat': 'Banana! Best snack in the canopy.',
        'cuddle': 'I’ll hold on with my tail, too!',
        'jump': 'Branch hop!',
        'nap': 'This branch looks like a good bed.', 'wake': 'Tail stretched. Ready to climb!',
        'idle': ('Race you to the top branch!', 'I think I can climb a little higher.'),
        'focus': '{minutes} minutes. I can sit still. Probably.',
        'follow': 'Lead the way! I’ll scamper along.',
        'rename': 'I’m going to tell that name to every tree.',
        'finish': 'All done! Time for a branch hop.',
    },
    'eagle': {
        'name': 'Skye', 'treat_label': 'River fish', 'treat_art': 'fish',
        'moods': ('Keeping watch while you focus', 'Resting its wings', 'Ready for a perch break',
                  'Watching for a fish', 'Chirping softly', 'Watching for a breeze'),
        'hello': 'Hello from my perch. The wind feels good today.',
        'pet': 'A little chirp for you.',
        'treat': 'A river fish! Excellent catch.',
        'cuddle': 'Come under my wing.',
        'jump': 'Wings up!',
        'nap': 'Tucking my beak under a wing.', 'wake': 'Wings stretched. Ready for a glide.',
        'idle': ('I can see the whole field from this perch.', 'The breeze is picking up.'),
        'focus': '{minutes} minutes. I’ll keep watch.',
        'follow': 'I’ll keep you in sight.',
        'rename': 'That’s a fine name to call across the sky.',
        'finish': 'Wings out. You’ve earned a stretch.',
    },
    'mascot': {
        'name': 'Mochi', 'treat_label': 'Give a treat', 'treat_art': 'star',
        'moods': ('Focusing with you', 'Taking a nap', 'A little sleepy',
                  'Thinking about snacks', 'Happy to see you', 'Curious little companion'),
        'hello': 'Hi! Middle-click to open my card.',
        'pet': 'Hello, favorite human.',
        'treat': 'Snack acquired!',
        'cuddle': 'Thanks for the hug.',
        'jump': 'Boing!',
        'nap': 'Taking a little nap.', 'wake': 'Back from nap time.',
        'idle': ('I’m here if you need a little company.', 'Have you stretched lately?'),
        'focus': '{minutes} minutes. Let’s get some work done.',
        'follow': 'I’m right behind you.',
        'rename': 'I like my new name.',
        'finish': 'Time for a little break.',
    },
}

PET_DIALOGUE = {
    'owl': dict(
        name='Dusk', hello='A little owl, right on time for twilight.',
        pet='Soft feathers make good company.', treat='A tiny midnight snack. Thank you!',
        cuddle='Come sit under my wing.', jump='Up with the evening breeze!',
        nap='Tucking in for a quiet perch break.', wake='Feathers fluffed. Ready to fly.',
        idle=('I like how quiet the sky gets at dusk.', 'I can hear the breeze from here.'),
        focus='{minutes} minutes. I’ll keep a quiet watch.', follow='I’ll flutter along after you.',
        rename='I’ll remember that name at twilight.', finish='Time to rest those eyes.',
        moods=('Keeping a quiet watch', 'Sleeping on a perch', 'Ready to fold its wings',
               'Looking for a midnight snack', 'Softly hooting', 'Listening for the evening breeze')),
    'cat-classic': dict(
        hello='Mew! Is that a sunbeam over there?', pet='Yes, under the chin please.',
        treat='A little fish for a very good tabby.', cuddle='I fit right here. Purr.',
        jump='Up to the imaginary windowsill!', nap='Saving this sunbeam for my nap.',
        wake='Big stretch. Small meow.',
        idle=('I could watch that window all afternoon.', 'This looks like a good place to curl up.'),
        focus='{minutes} minutes. I’ll nap beside you.', follow='You walk, I’ll pad along.',
        rename='I’ll pretend I didn’t hear it the first time.', finish='You’re done! The windowsill is calling.'),
    'codex': dict(
        hello='Terminal open. Tiny helper ready.', pet='Pat received. Sending a happy beep.',
        treat='A byte-sized snack. Perfect.', cuddle='Pairing complete. Hug accepted.',
        jump='Jump command executed!', nap='Saving my place before sleep.', wake='Session restored!',
        idle=('Idle prompt. Plenty of time.', 'Need a tiny rubber duck?'),
        focus='{minutes} minutes. I’ll keep a quiet prompt.', follow='Following your cursor, step by step.',
        rename='New name saved locally.', finish='Done. Time for a quick reset.'),
    'dewey': dict(
        hello='Drip drop! Room for one more?', pet='That made my little ripples wiggle.',
        treat='A sip! Now I feel extra splashy.', cuddle='Soft hugs make the best puddles.',
        jump='Splish, splash, up I go!', nap='Going still as a pond.', wake='A little ripple woke me up.',
        idle=('I wonder where the next puddle is.', 'I’m practicing my quietest drip.'),
        focus='{minutes} minutes. Quiet as a puddle.', follow='I’ll splash along behind you.',
        rename='That name has a nice ripple to it.', finish='Take a sip of water with me.'),
    'fireball': dict(
        hello='A little spark just arrived!', pet='Careful, compliments make me glow.',
        treat='Fuel for one very small fire.', cuddle='Warm hug incoming!',
        jump='Pop! Like a spark from a campfire.', nap='Down to a little ember.',
        wake='Back to a bright little flame!',
        idle=('I’m warming this corner for you.', 'Small flame, very big ideas.'),
        focus='{minutes} minutes. I’ll keep the glow low.', follow='Keep going. I’ll flicker along.',
        rename='That name really sparks something.', finish='Time to cool down for a minute.'),
    'hoots': dict(
        hello='Hoot! Did I miss anything interesting?', pet='A hoot of approval.',
        treat='An owl-sized bite. Hoo, thank you!', cuddle='These feathers make a good pillow.',
        jump='Up to the next perch!', nap='One eye closed. Then the other.', wake='Hoo’s there? Oh, it’s you.',
        idle=('I saw that cursor move.', 'This is a respectable little perch.'),
        focus='{minutes} minutes. I’ll keep owl watch.', follow='I’ve got my eyes on you.',
        rename='That’s a name worth hooting twice.', finish='Hoot! Time to let those eyes rest.'),
    'rocky': dict(
        hello='Hello from my favorite patch of ground.', pet='Even a little rock likes a pat.',
        treat='A snack to go with this sediment.', cuddle='Solid hug. Ten out of ten.',
        jump='Pebble bounce!', nap='I’m going to sit very, very still.', wake='Well, that rocked.',
        idle=('I like this spot. It’s very grounded.', 'I could use a little fresh gravel.'),
        focus='{minutes} minutes. Steady as a rock.', follow='Coming! Rocks have little legs, you know.',
        rename='That one’s set in stone.', finish='Solid work. Let’s take a breather.'),
    'seedy': dict(
        hello='Hi! My leaves say hello too.', pet='You made both my leaves wiggle.',
        treat='A tiny snack for a growing sprout.', cuddle='Careful of the leaves. Keep hugging.',
        jump='New growth spurt!', nap='Time to fold my leaves.', wake='Leaves up. Good morning!',
        idle=('I think I’m a little taller today.', 'Have you seen any sunlight around here?'),
        focus='{minutes} minutes. I’ll grow quietly.', follow='I’ll turn my leaves your way.',
        rename='That name feels like a fresh leaf.', finish='Finished! Time to stretch toward the light.'),
    'stacky': dict(
        hello='All three of us say hi!', pet='That pat traveled down the whole stack.',
        treat='One snack. We’ll split it three ways.', cuddle='A hug for every layer!',
        jump='One, two, three, jump!', nap='Sleeping from the top down.', wake='All layers are awake!',
        idle=('Top says hello. So does middle. And bottom.', 'We’re practicing our balance.'),
        focus='{minutes} minutes. All three of us can be quiet.', follow='Single file. Good thing we’re stacked.',
        rename='Three votes to keep that name.', finish='All three of us think you earned a break.'),
    'bsod': dict(
        hello='Boot complete. Tiny robot online!', pet='Head pat logged. Blue screen happy.',
        treat='Snack installed successfully.', cuddle='All systems warm and fuzzy.',
        jump='Testing the bounce protocol!', nap='Entering cozy sleep mode.', wake='Reboot complete. Beep!',
        idle=('Blue is a happy color, actually.', 'My antenna says hello.'),
        focus='{minutes} minutes. Running quiet mode.', follow='Tracking a friendly cursor. Beep.',
        rename='Display name updated. Happy beep!', finish='Quiet mode complete. Stretch protocol enabled.'),
    'null-signal': dict(
        hello='No signal. Plenty of company.', pet='That pat came through loud and clear.',
        treat='A snack on the right frequency.', cuddle='Strong connection. No static.',
        jump='Signal spike!', nap='Going off the air for a bit.', wake='Broadcast resumed.',
        idle=('Is this channel on?', 'Quiet static is nice sometimes.'),
        focus='{minutes} minutes. Keeping the airwaves quiet.', follow='Tuning in to your footsteps.',
        rename='New call sign received.', finish='End of transmission. Time for a break.'),
}
VOICES.update({
    pet: {**VOICES['cat' if pet == 'cat-classic' else 'mascot'], **dialogue}
    for pet, dialogue in PET_DIALOGUE.items()
})


def voice_for(pet):
    return VOICES.get(pet, VOICES['mascot'])


class Companion:
    def __init__(self, saved=None, now=None):
        now = time.time() if now is None else now
        self.data = {'name': 'Mochi', 'xp': 0, 'legacy_levels': 0, 'affection': 58., 'fullness': 80., 'energy': 85.,
                     'pets': 0, 'treats': 0, 'catches': 0, 'focus_sessions': 0, 'firefly_rounds': 0,
                     'sleeping': False, 'focus_until': None, 'last_updated': now}
        if isinstance(saved, dict):
            for key in ('xp', 'pets', 'treats', 'catches', 'focus_sessions', 'firefly_rounds'):
                value = saved.get(key)
                if type(value) is int:
                    self.data[key] = max(0, min(10000000, value))
            for key in ('affection', 'fullness', 'energy', 'last_updated', 'focus_until'):
                value = saved.get(key)
                if type(value) in (int, float) and math.isfinite(value):
                    self.data[key] = value if key in ('last_updated', 'focus_until') else max(0., min(100., value))
            # Previously each completed level cost 30 XP. Keep those levels and
            # the leftover XP while keeping lifetime earned XP unchanged.
            old_limit = self.data['xp'] // 30
            legacy = saved.get('legacy_levels', old_limit)
            if type(legacy) is int:
                self.data['legacy_levels'] = max(0, min(legacy, old_limit))
            self.data['sleeping'] = saved.get('sleeping') is True
            self.rename(saved.get('name', 'Mochi'))

    def rename(self, name):
        if isinstance(name, str):
            self.data['name'] = ' '.join(name.split())[:20] or 'Mochi'

    @property
    def level(self):
        return self.friendship_progress[0]

    @property
    def friendship_progress(self):
        """Return current level, XP earned within it, and XP required to advance."""
        legacy = self.data['legacy_levels']
        adjusted_xp = self.data['xp'] + 5 * legacy * (legacy - 1)
        # Completing n levels costs 30 + 40 + ... = 5*n*(n+5).
        completed = (math.isqrt(25 + 4 * (adjusted_xp // 5)) - 5) // 2
        earned = adjusted_xp - 5 * completed * (completed + 5)
        return completed + 1, earned, 30 + 10 * completed

    @property
    def mood(self):
        return self.mood_for('cat')

    def mood_for(self, pet):
        d = self.data
        words = voice_for(pet)['moods']
        if d['focus_until'] is not None:
            return words[0]
        if d['sleeping']:
            return words[1]
        if d['energy'] < 25:
            return words[2]
        if d['fullness'] < 30:
            return words[3]
        return words[4] if d['affection'] >= 75 else words[5]

    def tick(self, now=None):
        now = time.time() if now is None else now
        # Absence never severely penalizes the pet; offline changes are capped.
        hours = min(4., max(0., now - self.data['last_updated']) / 3600)
        self.data['last_updated'] = now
        self.data['fullness'] = max(0., self.data['fullness'] - 4 * hours)
        self.data['affection'] = max(0., self.data['affection'] - 2 * hours)
        self.data['energy'] = max(0., min(100., self.data['energy'] +
                                          (20 if self.data['sleeping'] else -3) * hours))
        if self.data['focus_until'] is not None and now >= self.data['focus_until']:
            self.data['focus_until'] = None
            self.data['focus_sessions'] += 1
            self.data['xp'] += 20
            self.data['affection'] = min(100., self.data['affection'] + 12)
            return ['focus-complete']
        return []

    def interact(self, action):
        d = self.data
        if action == 'pet':
            d['affection'] = min(100., d['affection'] + 8)
            d['pets'] += 1
            d['xp'] += 2
        elif action == 'treat':
            d['fullness'] = min(100., d['fullness'] + 24)
            d['affection'] = min(100., d['affection'] + 4)
            d['treats'] += 1
            d['xp'] += 3
        elif action == 'catch':
            d['affection'] = min(100., d['affection'] + 10)
            d['energy'] = max(0., d['energy'] - 4)
            d['catches'] += 1
            d['xp'] += 6
        elif action == 'cuddle':
            d['affection'] = min(100., d['affection'] + 12)
            d['energy'] = min(100., d['energy'] + 2)
            d['xp'] += 4
        elif action == 'fireflies':
            d['affection'] = min(100., d['affection'] + 8)
            d['firefly_rounds'] += 1
            d['xp'] += 12
        else:
            raise ValueError('Unknown interaction: ' + action)

    def start_focus(self, minutes=25, now=None):
        if minutes not in (15, 25, 50):
            raise ValueError('Choose 15, 25, or 50 minutes')
        self.data['sleeping'] = False
        self.data['focus_until'] = (time.time() if now is None else now) + minutes * 60

    def remaining(self, now=None):
        deadline = self.data['focus_until']
        return max(0, math.ceil(deadline - (time.time() if now is None else now))) if deadline is not None else 0

    def snapshot(self):
        return dict(self.data)
