# Neuro Ren'Py Implementation
*A universal Ren'Py mod for the Neuro Game API*

This is a universal mod for (almost) all Ren'Py games for AIs to control the game using the [Neuro Game API](https://github.com/VedalAI/neuro-sdk/blob/main/API/SPECIFICATION.md).
It works for all games written in Ren'Py as long as they only include fairly standard Ren'Py functionalities.
For more on what functionalities this mod supports, see the [Functions and Features](#functions-and-features) section.
For specific games, see the [Games](#games) section.

This mod can also be used by developers who want to include Neuro Game API support in their Ren'Py game. For more information, see the [For Developers](#for-developers) section.

## Installation and Setup
1. [Download the mod via GitHub](https://github.com/caheuer/neuro-renpy-implementation/archive/refs/heads/main.zip)
2. Extract the files using your favorite ZIP file extractor
3. Copy the **contents** (not the folder itself!) of the `neuro-implementation` folder into the `game` folder of the Ren'Py game.
Each Ren'Py game installation will have a `game` folder.
4. Edit `neuroconfig.py` to configurate the mod to your liking.
You can open the file with any text file editor, such as Notepad on Windows.
For certain use-cases (e.g. context only), check out the templates in the `config-templates` folder.
To use a template, please copy-paste the **contents** of the template file whilst keeping the name of the file in the `game` folder `neuroconfig.py`.
5. Start the game as usual. It will automatically connect with the Neuro API and immediately announce the game name.

> [!WARNING]
> If you have `auto_start` and `save_game` both set to `True` (which it is by default), the game will automatically start with your last save.
> Please make sure to delete all your save files beforehand if you wish the game to automatically start a new game, instead of your old save.

## Functions and Features

### General
- Connecting to Neuro API via WebSocket with automatic connection recovery on disconnect
- Auto-starting the game with new game or last save if available
- Auto-saving the game
- Turning on and off features in a config file to customize for different use-cases and games

### Context
- Announcing game name, new game and save game load
- Dialogue (speakers and text)
- Choices in menu screens
- Text in custom screens

### Interaction
- Choice menus (Ren'Py `menu:`s)
- Text inputs (`renpy.input`)
- Clicking buttons on custom screens
- Clicking buttons on screen when `ui.interact` is called
- Continuing the game when user input is awaited in `renpy.pause`

### Work In Progress / Future
- Giving more context about sounds played and images displayed on screen
- Supporting the proposed `shutdown` commands

## Games
In general, the mod will work well on simple Ren'Py games.
However, some games might implement custom functionality which may break the mod.

Currently, the mod has been tested on the following games:
- Doki Doki Literature Club!
- MILK INSIDE A BAG OF MILK INSIDE A BAG OF MILK
- Slay the Princess — The Pristine Cut

In general, the mod worked for all these games to some degree.
Please check [GAMES.md](GAMES.md) for more details and hints on running the mod on these games.
Do not hesitate to test the mod on other games and note your results there as well.

## For Developers
If you are a Ren'Py game developer, you can use this mod to easily add support for the Neuro Game API to your game.

To add this mod to your game, [download the project from GitHub](https://github.com/caheuer/neuro-renpy-implementation/archive/refs/heads/main.zip) and simply add the contents of the `neuro-implentation` folder into the `game` folder of your project.
You can find the `game` folder under `Open Directory > game` in your Ren'Py launcher.
Then launch the game like you usually do.

When you build your project, the mod should be automatically included.
Please be aware that the mod currently only works for desktop builds due to limitations with the websocket package used by this mod.
Web, Android and iOS builds are not be able to connect via websocket.

Please test if your game runs properly with the implementation before building.
I recommend using the software [Tony by Pasu4](https://github.com/Pasu4/neuro-api-tony) for this.

If you would like to give extra context or provide extra functions via Neuro Game API, you can use the functions described in [FUNCTIONS.md](FUNCTIONS.md).

Check out [the example project](examples/Example%20Game) for a Ren'Py project that uses the Neuro Game API and its extra functions for developers.
Copy it into your Ren'Py project folder to launch it with the Ren'Py launcher.

Mentioning the mod or me in your game is not neccessary, however if you wish to do so, please attribute "ChrisAusDemKlo" (my Twitch and Discord username).


## Contributing
If you find any bugs or functions missing for your use case, do not hesitate to create an issue on this GitHub repo or contact me through any channel.
If you are able to, you may also create a pull request on this repo.
In either case, I'll try to get back to you as soon as possible.

## Licenses
This mod uses third-party modules for some of its functionality.

It uses the [WebSocket client library for Python version 0.40.0](https://pypi.org/project/websocket-client/0.40.0/), licensed under the [GNU General Public License](neuro-implementation/websocket/LICENSE).

It includes [six.py version 1.17.0](https://pypi.org/project/six/), licensed under the MIT License.

It includes the json module, hmac.py and ssl.py, which are part of the [Python 2.7 Standard Library](https://github.com/python/cpython/tree/2.7), licensed under the [Python License](LICENSE.python.txt).

All other code and content in this repository is licensed under the [MIT License](LICENSE).

## Thanks
I would like to thank:
- [Vedal987](https://github.com/Vedal987) for creating Neuro-sama and Evil Neuro
- [Alex](https://github.com/Alexejhero) for helping create the Neuro API specs and SDKs
- [Pasu4](https://github.com/Pasu4) for creating the graphical testing software Tony for the Neuro API
