# Games
This list includes every game the mod was tested with.
Read for each game how well the mod works with the game and recommendations for running the mod with that game.
If you test the mod on a game which is not yet included in this list, feel free to add the game and your experience to this list via pull request.
You may also add some information to the games already listed.


## Doki Doki Literature Club!
Generally, the game works with the mod except at the very start and the very end.
It might get stuck sometimes, needing human intervention.

### Context
All context on the dialogue and poems are given.
Some audiovisual context crucial to the game is missing, such as special fonts, music changing or visual changes.

### Interaction
Neuro can perform almost all actions required for completing the game.
These include chosing menu options, selecting poem words, skipping and more.
However, there are two exceptions:

At the very end of the game, a certain action is required to reach the true ending, which the mod does not support.
Human intervention is needed for this step.

Additionally, the mod does not work with the player name input at the beginning of the game.
If `auto_start` in the config file is set to `True`, this input will be skipped entirely, leaving the player name blank in the dialogue.
It is therefore recommended to launch the game and enter a player name manually before installing the mod, as the player name is saved persistently.

### Recommendations
- Launch the game once before installing the mod and enter a player name manually.
- Set `game_over_action` in the config file to `new_game`


## MILK INSIDE A BAG OF MILK INSIDE A BAG OF MILK
The mod works well with this game.

### Context
All dialogue context is given, however some audiovisual storytelling is missing.

### Interaction
Neuro will be able to completely interact with this game.
However, this includes a language selection at the start of the game.
Neuro CAN choose a language other than English, so be aware of this.

### Recommendations
- Set `save_game` in the config file to `False`


## Slay the Princess — The Pristine Cut
The mod works well with this game when recommendations are observed.

### Context
All dialogue context is given, however some audiovisual storytelling is missing.

### Interaction
Neuro will be able to completely interact with this game.
This includes links to the game's Discord and other links at the very end so beware of this — human intervention to end the game is necessary here otherwise external links will be opened non-stop.

### Recommendations
- Set `save_game` in the config file to `True`
- Set `game_over_action` in the config file to `new_game`
- The game has recorded voice lines. To ensure they are played completely it is recommended to set `progression_mode` to `auto` and `max_progression_time` to `10.0` in the config file.