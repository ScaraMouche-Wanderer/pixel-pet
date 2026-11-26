# Pixel Pet

A tiny floating **pixel cat** with a playful personality, a tossable yarn ball, treats, naps, friendship levels, and a focus buddy. The **Pixel Pet Controls** window includes the original nine Codex pets, with their bundled artwork and frame timings.

The default **Cosmic Cat** has midnight-blue fur, a silver crescent, cyan eyes, a lavender scarf, and a turquoise tail tip. Its default size is **160 px**, 25% larger than before. The cream tabby remains available as **Classic Cat** under **Choose pet**. The size update runs once; later manual size choices are preserved.

Right-click the pet, then choose **Show menu**. In **Appearance**, click a sprite to choose your pet. **Colour** offers **Original**, **Pastel**, and **Moonlight** for the cats, Monkey, Eagle, and Hoots. The other mascots use their original colours. Pet, colour, size, and speed choices apply immediately and are saved.

Open **Pixel Pet** from the application menu, or run:

```sh
/home/voidnode/Projects/pixel-pet/launch.sh
```

By default, the pet, reactions, and toys sit on the desktop behind application windows. Check **Always on top** under **Settings** to put them above your apps. Uncheck it to return to the desktop. Pixel Pet remembers this preference.

- **Right-click** the pet to see **Hide** and **Show menu** next to it. The quick menu closes when another window takes focus.
- **Hide** puts the pet away. Click its tray icon, choose **Show pet** from the tray menu, or reopen **Pixel Pet** to bring it back.
- **Show menu** opens the **Appearance**, **Play**, and **Settings** tabs in a compact window. You can also open it from the tray menu. Move the pointer outside the zoo window or choose **Close** to dismiss it. You can also press **Esc** or switch windows to dismiss it.
- **Hold for 0.7 seconds** to cuddle, or move the pointer back and forth across its head to make it purr.
- **Double-click** for a jump and pixel stars. **Drag** to move the pet.
- **Middle-click** opens the pet card. You can also choose **Open pet card** in **Play**. The card's **Pet** button gives hearts, a wave, and friendship XP.
- The original Codex characters also look toward the pointer using their 16 directional sprites.
- Opening Pixel Pet again brings the running pet home.

## Play together

**Walk around** lets every pet choose new destinations across the usable area of its current display. Eagle and Hoots fly to their next spot. Drag a pet to another display to move its roaming there.

**Autonomous play** is on by default. Cats prowl, pounce, stretch, groom, and chase yarn. The monkey scampers, hops, swings, climbs a desktop edge, and can hang by its tail. Eagle glides with spread wings and Hoots uses quick, fluttering wingbeats. Their **Take flight** routines return to the starting perch. Both birds can also preen.

Choose **Take flight** for either bird, or try more poses under **Play** → **Animate**. These actions are also part of the autonomous mix. Focus sessions, naps, and active toys take priority. **Stop current play** ends the current activity. Use **Autonomous play** to turn the automatic activity off.


In **Play → Animate**, each pet has four exclusive moves. With **Autonomous play** enabled, your pet performs them automatically in shuffled rounds during idle time. **Motion effects** adds animated props, including Seedy’s falling leaves and fruit when its sprite is installed.

**Showtime** runs a short routine from the pet card or **Play** tab. The cat winds up for a Comet pounce, the monkey does a Cartwheel dash, and the eagle performs a Sky corkscrew. Each one returns to its starting point. Routines also appear in the autonomous mix. **Speed** offers Gentle, Normal, and Zoomies. **Motion effects** controls the click-through dust, leaves, and feathers that fade behind the moving pet.

Open a cat’s pet card and select **Chase yarn**. The yarn bounces with gravity, and the cat chases it. Grab the ball and throw it again by dragging and releasing it. Each catch earns XP and adds to its catch count. A round ends at the first catch or after 35 seconds. Starting play closes the card so the toy is immediately usable.

Select **Firefly hunt** from the pet card or **Play** tab. Click five glowing fireflies within 25 seconds. Each one moves after you catch it, and a completed hunt earns 12 friendship XP. Use **Stop current play** to end the round early.

Offer the cat a fish treat, the monkey a banana slice, or the eagle a river fish. Each animal has its own dialogue and snack reaction. **Nap / wake** lets the cat recharge. **Follow me** follows your pointer horizontally for 20 seconds; choose it again from the menu to stop early. **Stop current play** stops movement and puts the yarn away.

The pet card shows your current pet's portrait, distinct moods, and nickname, care percentages, friendship level, and counts for yarn, firefly hunts, and focus sessions. Use **Rename** to name each pet individually. Shared friendship progress stays on this computer and survives restarts. Care is gentle: nothing dies or disappears, meters decline slowly, and time away is capped at four hours of decline per launch. Each 30 XP raises the friendship level. Naps replenish energy.

## Focus buddy

The pet card starts a 25-minute focus session. **Focus together** in **Play** offers 15, 25, and 50 minutes. The pet settles down, toys stop, and both windows show the remaining time and let you stop the timer. At completion the pet celebrates, earns 20 XP, and sends a desktop notification when `notify-send` is available. A running focus session survives hiding, sleep, and restart. An overdue session completes once at the next launch. Starting a toy, following, or taking a nap explicitly ends an active focus session.

Every selectable pet has its own prewritten speech-bubble lines, including greetings, petting, snacks, naps, and focus sessions. The cats, monkey, and eagle also have matching icons and colors that follow their selected style. The bubble moves below the pet when it needs room at the top of the screen. Its surface passes input through and follows the pet’s desktop layer. Switch off **Little speech bubbles** to disable spontaneous comments and the launch greeting. Direct interactions still show their response.

The cats, monkey, and eagle use nearest-neighbor scaled animation frames. The monkey and eagle are original pixel sprites drawn in `animals.py`. Nine original pets are also included locally: Codex, Dewey, Fireball, Hoots, Rocky, Seedy, Stacky, BSOD, and Null Signal. The pet and reaction overlays have transparent backgrounds; transparent pet pixels and the whole reaction layer pass clicks through to the desktop.

The app uses PySide6 and XWayland to float over desktop windows on GNOME Wayland. Dependencies are already installed here.

Settings live in `~/.config/pixel-pet/settings.json` (respects `XDG_CONFIG_HOME`). Login startup is optional. To remove, quit the pet and remove `~/.local/share/applications/pixel-pet.desktop`, `~/.local/bin/pixel-pet`, `~/.config/autostart/pixel-pet.desktop`, this project, and its settings directory.

After an update, select **Quit** from the tray menu, then open **Pixel Pet** again. The same launcher and existing settings continue to work.

## Rendering and performance

Animation frames and their hit regions are prepared before playback. A stable window shape covers every sprite frame. The pet copies each frame together with its transparent pixels. Reactions use a fixed transparent surface for the current display and repaint the areas affected by bubbles and particles. When a reaction ends, its old pixels are cleared before the surface hides.

The timer uses a precise clock, with 16 ms updates during movement or particles and up to 200 ms between updates at rest. Sprite frames still use their original durations. Focus completion and toy catches update in the current animation pass rather than entering the update loop recursively.

`python benchmark_render.py` runs a repeatable offscreen workload and reports window-shape changes, overlay redraws, and update time. This measures the application's work; it is not a live GNOME compositor or screen-FPS test. Reference: [Qt window masks and painting](https://doc.qt.io/qt-6/qwidget.html), [timer accuracy](https://doc.qt.io/qt-6/qtimer.html).

The bundled sprite files were copied from `/usr/lib/chatgpt/resources/app.asar`, `webview/assets/*-spritesheet-*.webp`, for this computer's local use. They are original OpenAI artwork, not generated replacements. This is a separate desktop overlay; it does not read chats or reproduce Codex's task-status integration.

The pixel cat in `assets/cat.png` was generated with the built-in imagegen tool. Its full prompt is in `assets/cat-prompt.txt`. The generated image was copied into this project and is sliced on its original 4×4 grid at runtime.

The Cosmic Cat in `assets/cat-cosmic.png` was redesigned from that sprite sheet with the built-in imagegen editing tool. Its full prompt is in `assets/cat-cosmic-prompt.txt`. It preserves the same 4×4 animation layout and transparent background.

Official feature reference: [OpenAI Pets documentation](https://learn.chatgpt.com/docs/pets?translationFallback=pt-BR).

Preview: `python pet.py --preview preview`. Run checks with `python -m unittest -v test_pet test_companion`.
