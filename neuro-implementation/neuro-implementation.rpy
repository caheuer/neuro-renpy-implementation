default _neuro_game_started = False

init python:
    DEFAULT_RENPY_SCREENS = {
        # in-game
        "say","choice","input","nvl","nvl_choice","notify","skip_indicator","ctc",
        # menus/system
        "main_menu","navigation","save","load","preferences","confirm","yesno_prompt",
        "help","history","file_picker","joystick_preferences","quick_menu"
    }

    import neuroconfig
    if neuroconfig.save_log:
        config.log = "neuro_log.txt"

    renpy.log("[NEURO] Initializing Neuro Implementation...")

    # We need hmac.py and ssl.py for websocket-client to work in older Ren'Py versions which use Python 2.x
    # However, these break under Python 3.x, so we need to remove them if we're running under Python 3.x
    import sys
    import os
    game_dir = os.path.join(config.basedir, "game")
    if sys.version_info[0] > 2:
        hmac_path = os.path.join(game_dir, "hmac.py")
        ssl_path = os.path.join(game_dir, "ssl.py")
        deleted = False
        if os.path.exists(hmac_path):
            os.remove(hmac_path)
            deleted = True
        if os.path.exists(ssl_path):
            os.remove(ssl_path)
            deleted = True
        if deleted:
            renpy.log("[NEURO] Removed hmac.py and/or ssl.py to ensure compatibility with Python 3.x, restarting the game...")
            renpy.quit(relaunch=True)     

    import websocket
    import json
    import time
    import types

    ### HELPER FUNCTIONS ###

    def _neuro_get_game_name():
        global _neuro_game_name
        try:
            if not _neuro_game_name:
                _neuro_game_name = renpy.config.name
        except:
            _neuro_game_name = renpy.config.name
        finally:
            return _neuro_game_name

    def _neuro_delayed_function(delay, function, *args, **kwargs):
        # We use two different screens to allow multiple delayed functions to be scheduled at the same time
        global _neuro_use_alt_delayed_function_screen
        if "_neuro_use_alt_delayed_function_screen" not in globals():
            _neuro_use_alt_delayed_function_screen = False
        if _neuro_use_alt_delayed_function_screen:
            renpy.show_screen("_neuro_delayed_function_screen_2", delay, function, args, kwargs)
        else:
            renpy.show_screen("_neuro_delayed_function_screen", delay, function, args, kwargs)
        _neuro_use_alt_delayed_function_screen = not _neuro_use_alt_delayed_function_screen

    def _neuro_find_buttons_in_displayble(displayable):
        results = []
        if isinstance(displayable, renpy.display.behavior.Button):
            results.append(displayable)
        if hasattr(displayable, "children"):
            for child in displayable.children:
                results += _neuro_find_buttons_in_displayble(child)
        return results

    def _neuro_get_displayable_text(displayable):
        text_parts = []
        if hasattr(displayable, "text"):
            text_parts.extend(displayable.text)
        if hasattr(displayable, "children"):
            for child in displayable.children:
                text_parts.append(_neuro_get_displayable_text(child))
        text_parts = [str(text).strip() for text in text_parts if str(text).strip()]
        return " ".join(text_parts) if text_parts else ""

    def _neuro_who_to_str(who):
        if who is None:
            return "Narrator"
        elif isinstance(who, str):
            return renpy.translate_string(who)
        elif hasattr(who, "name"):
            try:
                return renpy.translate_string(who.name)
            except:
                return str(who)
        else:
            return str(who)


    ### SAVING / LOADING ###

    def _neuro_save():
        renpy.log("[NEURO] Saving the game...")
        if not store._neuro_game_started:
            renpy.log("[NEURO] Game has not started yet, skipping save.")
            return
        try:
            renpy.save("neuro_save")
        except Exception as e:
            renpy.log("[NEURO] Failed to save the game: {}".format(str(e)))

    def _neuro_can_load():
        return renpy.can_load(renpy.newest_slot())

    def _neuro_load(force_new_game=False):
        if renpy.can_load(renpy.newest_slot()) and not force_new_game:
            # Load the last saved state
            neuro_give_context("Loading your last saved state. You will start off where you left off.", silent=True)
            renpy.load(renpy.newest_slot())
            neuro_give_context("Loading your last saved state failed. Starting a new game instead.", silent=True)
            renpy.log("[NEURO] Failed to load the last saved state: {}".format(str(e)))
        # Start a new game if no save was found or force_new_game is True
        renpy.jump_out_of_context("start")


    ### CONTEXT ###

    def neuro_give_context(message, silent=False):
        if not neuroconfig.give_context:
            return
        msg = {
            "command": "context",
            "game": _neuro_get_game_name(),
            "data": {
                "message": message,
                "silent": silent
            }
        }
        _neuro_send_ws_message(json.dumps(msg))


    ### ACTIONS ###

    _neuro_registered_actions = []

    def neuro_register_action(action_name, action_description, action_schema):
        renpy.log("[NEURO] Registering action: {}".format(action_name))
        neuro_unregister_action(action_name)  # Unregister if already registered
        action = {
            "name": action_name,
            "description": action_description,
            "schema": action_schema
        }
        _neuro_registered_actions.append(action)
        msg = {
            "command": "actions/register",
            "game": _neuro_get_game_name(),
            "data": {
                "actions": [
                    action
                ]
            }
        }
        _neuro_send_ws_message(json.dumps(msg))

    def neuro_unregister_action(action_name):
        renpy.log("[NEURO] Unregistering action: {}".format(action_name))
        _neuro_registered_actions[:] = [action for action in _neuro_registered_actions if action["name"] != action_name]
        msg = {
            "command": "actions/unregister",
            "game": _neuro_get_game_name(),
            "data": {
                "action_names": [action_name]
            }
        }
        _neuro_send_ws_message(json.dumps(msg))

    def neuro_unregister_all_actions():
        if len(_neuro_registered_actions) == 0:
            return
        renpy.log("[NEURO] Unregistering all actions")
        msg = {
            "command": "actions/unregister",
            "game": _neuro_get_game_name(),
            "data": {
                "action_names": [action["name"] for action in _neuro_registered_actions]
            }
        }
        _neuro_send_ws_message(json.dumps(msg))

    def neuro_force_action(action_names, query):
        renpy.log("[NEURO] Forcing actions: {}".format(action_names))
        msg = {
            "command": "actions/force",
            "game": _neuro_get_game_name(),
            "data": {
                "query": query,
                "action_names": action_names
            }
        }
        _neuro_send_ws_message(json.dumps(msg))

    def _neuro_handle_progress_dialogue_action(data):
        renpy.exports.queue_event("dismiss")
        return (True, "Progressing dialogue.")

    def _neuro_handle_continue_action(data):
        renpy.exports.queue_event("dismiss")
        return (True, "Continuing the game.")

    def _neuro_handle_select_option_action(data):
        success = True
        message = ""
        option = data.get("option")
        choice = next((c for c in _neuro_menu_choices if c[0] == option), None)
        if option is None:
            success = False
            message = "ERROR: No option selected."
        elif choice is None:
            success = False
            choices_str = ", ".join(['"' + c[0] + '"' for c in _neuro_menu_choices])
            message = "ERROR: Option '{}' is not valid. Please select one of the available options: {}.".format(option, choices_str)
        else:
            message = "You selected the option: {}".format(option)
            renpy.notify("Selected: \"" + option + "\"")
            renpy.show_screen("_neuro_return_screen", choice[2])
            renpy.restart_interaction()
        return (success, message)

    def _neuro_handle_input_action(data):
        success = True
        message = ""
        user_input = data.get("input")
        if user_input is None:
            success = False
            message = "ERROR: No input provided."
        else:
            message = "You provided the input: {}".format(user_input)
            renpy.notify("Input: \"" + user_input + "\"")
            renpy.show_screen("_neuro_return_screen", user_input)
            renpy.restart_interaction()
        return (success, message)

    def _neuro_click_button(button_txt):
        global _neuro_ui_buttons
        button = next((b for b in _neuro_ui_buttons if _neuro_get_displayable_text(b) == button_txt), None)
        actions = button.action
        if button.action is None:
            actions = button.clicked
        if not isinstance(actions, (list, tuple)):
            actions = [actions]
        for action in actions:
            if action.__class__.__name__ == "Return":
                value = getattr(action, "value", None)
                renpy.show_screen("_neuro_return_screen", value)
                _neuro_ui_buttons = []
                continue
            if action.__class__.__name__ == "Curry":
                fn = getattr(action, "callable", None)
                if getattr(fn, "__name__", None) == "_returns":
                    renpy.show_screen("_neuro_return_screen", action.args[0])
                    _neuro_ui_buttons = []
                    continue
            action()
        renpy.restart_interaction()
        neuro_unregister_action("click_button")

    def _neuro_handle_click_button_action(data):
        success = True
        message = ""
        button_txt = data.get("button")
        button = next((b for b in _neuro_ui_buttons if _neuro_get_displayable_text(b) == button_txt), None)
        if button_txt is None:
            success = False
            message = "ERROR: No button selected."
        elif button is None:
            success = False
            buttons_str = ", ".join([_neuro_get_displayable_text(b) for b in _neuro_ui_buttons])
            message = "ERROR: Button '{}' is not valid. Please select one of the available buttons: {}.".format(button_txt, buttons_str)
        else:
            message = "You clicked the button: {}".format(button_txt)
            renpy.notify("Clicked: \"" + button_txt + "\"")
            renpy.show_screen("_neuro_click_button_screen", button_txt)
            renpy.restart_interaction()
        return (success, message)

    neuro_action_handlers = {
        "progress_dialogue": _neuro_handle_progress_dialogue_action,
        "continue": _neuro_handle_continue_action,
        "select_option": _neuro_handle_select_option_action,
        "input": _neuro_handle_input_action,
        "click_button": _neuro_handle_click_button_action
    }

    def _neuro_handle_action(action_id, action_name, action_json_str):
        renpy.log("[NEURO] Handling action: {} (ID: {})".format(action_name, action_id))
        renpy.log("[NEURO] Action data: {}".format(action_json_str))

        if action_json_str:
            action_json = json.loads(action_json_str)
        else:
            action_json = {}

        success = True
        message = ""

        try:
            success, message = neuro_action_handlers[action_name](action_json)
        except KeyError:
            success = False
            message = "ERROR: Action '{}' is not registered or not supported.".format(action_name)
        except Exception as e:
            success = False
            message = "ERROR: An error occurred while processing the action: {}".format(str(e))

        msg = {
            "command": "action/result",
            "game": _neuro_get_game_name(),
            "data": {
                "id": action_id,
                "success": success,
                "message": message
            }
        }
        _neuro_send_ws_message(json.dumps(msg))


    ### WEBSOCKET CONNECTION ###

    def _neuro_send_ws_message(message, ws=None):
        if ws is None:
            ws = _neuro_ws
        if ws and ws.sock and ws.sock.connected:
            ws.send(message)
            return True
        else:
            return False

    def _neuro_ws_on_open(ws):
        renpy.log("[NEURO] WebSocket connection opened")

        # Send initial message to the server
        msg = {
            "command": "startup",
            "game": _neuro_get_game_name(),
        }
        _neuro_send_ws_message(json.dumps(msg), ws)

        # Give initial context of the game
        neuro_give_context("You are now playing the visual novel '{}'.".format(_neuro_get_game_name()), silent=False)

        # Register all currently registered actions
        if len(_neuro_registered_actions) > 0:
            msg = {
                "command": "actions/register",
                "game": _neuro_get_game_name(),
                "data": {
                    "actions": _neuro_registered_actions
                }
            }
            _neuro_send_ws_message(json.dumps(msg), ws)

    def _neuro_ws_on_message(ws, message):
        renpy.log("[NEURO] Message received: " + message)

        data = json.loads(message)
        if data.get("command") == "action":
            _neuro_handle_action(data.get("data").get("id"), data.get("data").get("name"), data.get("data").get("data"))
        elif data.get("command") == "actions/reregister_all":
            renpy.log("[NEURO] Re-registering all actions")
            msg = {
                "command": "actions/register",
                "game": _neuro_get_game_name(),
                "data": {
                    "actions": _neuro_registered_actions
                }
            }
            _neuro_send_ws_message(json.dumps(msg), ws)

    def _neuro_ws_on_error(ws, error):
        renpy.log("[NEURO] Error occurred:", error)

    def _neuro_ws_on_close(ws, close_status_code, close_msg):
        renpy.log("[NEURO] WebSocket connection closed:", close_status_code, close_msg)

    def _neuro_ws_run():
        global _neuro_ws
        while True:
            _neuro_ws = websocket.WebSocketApp(
                neuroconfig.ws_url,
                on_open=_neuro_ws_on_open,
                on_message=_neuro_ws_on_message,
                on_error=_neuro_ws_on_error,
                on_close=_neuro_ws_on_close
            )
            _neuro_ws.run_forever()
            time.sleep(1) # Wait before trying to reconnect
    renpy.invoke_in_thread(_neuro_ws_run)


    ### REGISTER ACTION AND TIMEOUT FUNCTIONS ###

    # Function to register the progress_dialogue action
    def _neuro_register_progress_dialogue_action_and_deadline():
        neuro_register_action(
            "progress_dialogue",
            "Progress the dialogue.",
            {}
        )
        _neuro_delayed_function(
            neuroconfig.max_progression_time - neuroconfig.min_progression_time,
            neuro_force_action,
            ["progress_dialogue"],
            "Please progress the dialogue using the progress_dialogue action.",
        )

    # Function to register the continue action
    def _neuro_register_continue_action_and_deadline():
        neuro_register_action(
            "continue",
            "Continue the game.",
            {}
        )
        _neuro_delayed_function(
            neuroconfig.max_interaction_time - neuroconfig.min_interaction_time,
            neuro_force_action,
            ["continue"],
            "Please continue the game using the continue action.",
        )

    # Function to register the select_option action
    def _neuro_register_select_option_action_and_deadline(choices):
        neuro_register_action(
            "select_option",
            "Select an option from the menu.",
            {
                "type": "object",
                "properties": {
                    "option": {
                        "type": "string",
                        "enum": [choice[0] for choice in choices],
                    }
                },
                "required": ["option"]
            }
        )
        _neuro_delayed_function(
            neuroconfig.max_interaction_time - neuroconfig.min_interaction_time,
            neuro_force_action,
            ["select_option"],
            "Please select an option using the select_option action.",
        )

    # Function to register the input action
    def _neuro_register_input_action_and_deadline(prompt, default=None):
        neuro_register_action(
            "input",
            "Provide input for the prompt: '{}'.".format(prompt) \
            + (" The default input is '{}'.".format(default) if default else ""),
            {
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "Your input for the prompt '{}'.".format(prompt),
                    }
                },
                "required": ["input"]
            }
        )
        _neuro_delayed_function(
            neuroconfig.max_interaction_time - neuroconfig.min_interaction_time,
            neuro_force_action,
            ["input"],
            "Please provide input using the input action.",
        )

    # Function to register the click_button action
    def _neuro_register_click_button_action_and_deadline():
        neuro_register_action(
            "click_button",
            "Click a button on the screen.",
            {
                "type": "object",
                "properties": {
                    "button": {
                        "type": "string",
                        "enum": [_neuro_get_displayable_text(button) for button in _neuro_ui_buttons],
                    }
                },
                "required": ["button"]
            }
        )
        _neuro_delayed_function(
            neuroconfig.max_interaction_time - neuroconfig.min_interaction_time,
            neuro_force_action,
            ["click_button"],
            "Please click a button using the click_button action.",
        )


    ### REN'PY OVERWRITES ###

    # Register the label callback
    def _neuro_on_label(name, jumped):
        # Hide all delayed function screens when a label is jumped to
        # This is to ensure that the delayed function screen does not keep on running on menus
        try:
            renpy.hide("_neuro_delayed_function_screen")
        except:
            pass
        if "main_menu" in name:
            if store._neuro_game_started:
                # Game has just ended, start a new game or close the game window depending on the game_over_action config
                if neuroconfig.game_over_action == "new_game":
                    neuro_give_context("The game is over. Starting a new game.", silent=True)
                    _neuro_delayed_function(
                        5.0,
                        _neuro_load,
                        True
                    )
                elif neuroconfig.game_over_action == "close":
                    neuro_give_context("The game is over. Closing the game window.", silent=True)
                    _neuro_delayed_function(
                        5.0,
                        renpy.quit
                    )
            else:
                # Auto-start the game if the main menu is loaded and auto_start is enabled
                if neuroconfig.auto_start:
                    _neuro_delayed_function(
                        5.0,
                        _neuro_load
                    )
            store._neuro_game_started = False
            
        # Set the game started flag if the label is "start"
        if "start" in name:
            store._neuro_game_started = True
    try:
        config.label_callbacks.append(_neuro_on_label)
    except:
        # Older Ren'Py versions may not have label_callbacks but use config.label_callback instead
        old_label_callback = config.label_callback
        def new_label_callback(name, jumped):
            if old_label_callback is not None:
                old_label_callback(name, jumped)
            _neuro_on_label(name, jumped)
        config.label_callback = new_label_callback

    # Overwrite the default say function
    _neuro_original_say = renpy.exports.say
    def _neuro_custom_say(who, what, interact=True, *args, **kwargs):
        renpy.hide_screen("_neuro_delayed_function_screen")

        _neuro_save()

        neuro_unregister_action("progress_dialogue")
        neuro_unregister_action("continue")
        neuro_unregister_action("select_option")
        neuro_unregister_action("click_button")

        neuro_give_context(_neuro_who_to_str(who) + ": " + renpy.exports.substitute(what), silent=neuroconfig.silent_dialogue)

        if neuroconfig.progression_mode == "action":
            _neuro_delayed_function(
                neuroconfig.min_progression_time,
                _neuro_register_progress_dialogue_action_and_deadline
            )
        elif neuroconfig.progression_mode == "auto":
            _neuro_delayed_function(
                neuroconfig.max_progression_time,
                renpy.exports.queue_event,
                "dismiss",
            )

        return _neuro_original_say(who, what, interact, *args, **kwargs)
    renpy.exports.say = _neuro_custom_say
    del _neuro_custom_say

    # Overwrite the default menu function
    _neuro_original_menu = renpy.exports.menu
    def _neuro_custom_menu(items, *args, **kwargs):
        global _neuro_menu_choices
        _neuro_menu_choices = items

        neuro_unregister_action("progress_dialogue")

        if neuroconfig.allow_interaction:
            _neuro_delayed_function(
                neuroconfig.min_interaction_time,
                _neuro_register_select_option_action_and_deadline,
                _neuro_menu_choices
            )

        neuro_give_context("A menu appears with the following choices: " + ", ".join(["\"" + choice[0] + "\"" for choice in _neuro_menu_choices]) + "." \
            + (" You must choose one using select_option." if neuroconfig.allow_interaction else ""),
            silent=neuroconfig.silent_choices)
        
        rv = _neuro_original_menu(items, *args, **kwargs)
        neuro_unregister_all_actions()

        return rv
    renpy.exports.menu = _neuro_custom_menu
    del _neuro_custom_menu

    # Overwrite the default input function
    _neuro_original_input = renpy.exports.input
    def _neuro_custom_input(prompt, default=None, *args, **kwargs):
        neuro_unregister_action("progress_dialogue")

        if neuroconfig.allow_interaction:
            _neuro_delayed_function(
                neuroconfig.min_interaction_time,
                _neuro_register_input_action_and_deadline,
                prompt,
                default,
            )

        neuro_give_context("An input prompt appears with the following message: '{}'.".format(prompt) \
            + (" The default input is '{}'.".format(default) if default else "") \
            + (" You must provide input using the input action." if neuroconfig.allow_interaction else ""),
            silent=neuroconfig.silent_choices)

        rv = _neuro_original_input(prompt, default, *args, **kwargs)
        neuro_unregister_all_actions()

        return rv
    renpy.exports.input = _neuro_custom_input
    del _neuro_custom_input

    # Overwrite the default show screen function to catch custom menus, modals, etc.
    _neuro_original_show_screen = renpy.exports.show_screen
    def _neuro_handle_screen(screen_name):
        try:
            screen = renpy.exports.get_screen(screen_name)
            if screen is None:
                renpy.log("[NEURO] Screen '{}' not found.".format(screen_name))
                return
            buttons = _neuro_find_buttons_in_displayble(screen)
            if neuroconfig.allow_interaction and len(buttons) > 0:
                global _neuro_ui_buttons
                _neuro_ui_buttons = buttons
                _neuro_delayed_function(
                    neuroconfig.min_interaction_time,
                    _neuro_register_click_button_action_and_deadline
                )
            neuro_give_context(
                "A {} screen appears with the following content:\n\"{}\"".format(screen_name, _neuro_get_displayable_text(screen)) \
                + ("\nYou must interact with the screen using the actions provided to you." if neuroconfig.allow_interaction and len(buttons) > 0 else ""),
                silent=neuroconfig.silent_choices
            )
        except Exception as e:
            renpy.log("[NEURO] Error handling screen '{}': {}".format(screen_name, str(e)))
    def _neuro_custom_show_screen(screen_name, *args, **kwargs):
        _neuro_original_show_screen(screen_name, *args, **kwargs)
        if screen_name.startswith("_neuro"):
            return
        if screen_name in DEFAULT_RENPY_SCREENS:
            return

        neuro_unregister_action("progress_dialogue")

        _neuro_delayed_function(
            0.1,
            _neuro_handle_screen,
            screen_name
        )
    renpy.exports.show_screen = _neuro_custom_show_screen
    del _neuro_custom_show_screen

    # Overwrite the default ui.button function to catch buttons created in code
    _neuro_original_ui_button = renpy.ui.button
    def _neuro_custom_ui_button(*args, **kwargs):
        button = _neuro_original_ui_button(*args, **kwargs)
        if neuroconfig.allow_interaction:
            global _neuro_ui_buttons
            try:
                _neuro_ui_buttons.append(button)
            except:
                _neuro_ui_buttons = [button]
        return button
    renpy.ui.button = _neuro_custom_ui_button
    del _neuro_custom_ui_button

    # Overwrite the default ui.textbutton function to catch text buttons created in code
    _neuro_original_ui_textbutton = renpy.ui.textbutton
    def _neuro_custom_ui_textbutton(*args, **kwargs):
        button = renpy.display.behavior.Button(**kwargs)
        text = renpy.text.text.Text(args[0])
        button.add(text)
        if neuroconfig.allow_interaction:
            global _neuro_ui_buttons
            try:
                _neuro_ui_buttons.append(button)
            except:
                _neuro_ui_buttons = [button]
        return _neuro_original_ui_textbutton(*args, **kwargs)
    renpy.ui.textbutton = _neuro_custom_ui_textbutton
    del _neuro_custom_ui_textbutton

    # Overwrite the default ui.imagebutton function to catch image buttons created in code
    _neuro_original_ui_imagebutton = renpy.ui.imagebutton
    def _neuro_custom_ui_imagebutton(*args, **kwargs):
        button = _neuro_original_ui_imagebutton(*args, **kwargs)
        if neuroconfig.allow_interaction:
            global _neuro_ui_buttons
            try:
                _neuro_ui_buttons.append(button)
            except:
                _neuro_ui_buttons = [button]
        return button
    renpy.ui.imagebutton = _neuro_custom_ui_imagebutton
    del _neuro_custom_ui_imagebutton

    # Overwrite the default ui.interact function to catch whenever the game expects user interaction
    _neuro_original_ui_interact = renpy.ui.interact
    def _neuro_custom_ui_interact(*args, **kwargs):
        global _neuro_ui_buttons
        if '_neuro_ui_buttons' in globals() and len(_neuro_ui_buttons) > 0:
            # There are buttons available to interact with
            neuro_unregister_action("progress_dialogue")
            if neuroconfig.allow_interaction:
                _neuro_delayed_function(
                    neuroconfig.min_interaction_time,
                    _neuro_register_click_button_action_and_deadline
                )
        elif "type" in kwargs and kwargs["type"] == "pause" and store._neuro_game_started:
            # The game is paused, allow continuing
            neuro_unregister_action("progress_dialogue")
            if neuroconfig.allow_interaction:
                _neuro_delayed_function(
                    neuroconfig.min_interaction_time,
                    _neuro_register_continue_action_and_deadline
                )
        rv = _neuro_original_ui_interact(*args, **kwargs)
        neuro_unregister_action("click_button")
        return rv
    renpy.ui.interact = _neuro_custom_ui_interact
    del _neuro_custom_ui_interact


screen _neuro_delayed_function_screen(delay, function, args, kwargs):
    zorder 1000
    modal False
    timer delay action [Hide("_neuro_delayed_function_screen"), Function(function, *args, **kwargs)]

screen _neuro_delayed_function_screen_2(delay, function, args, kwargs):
    zorder 1000
    modal False
    timer delay action [Hide("_neuro_delayed_function_screen_2"), Function(function, *args, **kwargs)]

screen _neuro_return_screen(value):
    zorder 1000
    modal False
    timer 0.1 action [Hide("_neuro_return_screen"), Return(value)]

screen _neuro_click_button_screen(button_txt):
    zorder 1000
    modal False
    timer 0.1 action [Hide("_neuro_click_button_screen"), Function(_neuro_click_button, button_txt)]