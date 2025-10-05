# Functions for Developers
If you are a developer including this mod in your own game, you can use the following functions to give extra context or provide extra functions via Neuro Game API.
Check out [the example project](examples/Example%20Game/game/script.rpy) for implementation.

### neuro_give_context
function neuro_give_context(message, silent=False)

Give context to Neuro.\
message (string): The string to be given to Neuro as context.\
silent (bool): If the context should be silently. If set to false, Neuro will reply to the context given.

Example:

python:
  neuro_give_context("A wild Vedal appears on screen!", silent=True)


### neuro_action_handlers
dict neuro_action_handlers

The functions to execute once an action is sent via Neuro Game API.
Add your function(data) to the dict to define custom functions.
Be sure to return a (success, message) tuple.

Example:

python:
  def notify_func(data):
    text = data.get("text")
    if text is None:
      return (False, "Please supply a valid text.")
    renpy.notify(text)
    return (True, "Text displayed.")
  
  neuro_action_handlers["notify"] = notify_func


### neuro_register_action
function neuro_register_action(action_name, action_description, action_schema)

Register an action with the Neuro Game API.\
action_name (string): The name of the action. This should be a lowercase string, with words separated by underscores or dashes (e.g. "join_friend_lobby", "use_item").\
action_description (string): A description of what the action does.\
schema (dict): A JSON schema describing the expected return data.

Example:

python:
  neuro_register_action(
    "notify",
    "Display text on the screen for a short period of time",
    {
      "type": "object",
      "properties": {
        "text": {
          "type": "string",
          "enum": ["hello", "bye"],
        }
      },
      "required": ["text"]
    }
  )


### neuro_unregister_action
function neuro_unregister_action(action_name)

Unregister an action with the Neuro Game API.\
action_name (string): The name of the action.

Example:

python:
  neuro_unregister_action("notify")


### neuro_unregister_all_actions
function neuro_unregister_all_actions()

> [!WARNING]
> This may interfere with the mod's built-in actions.

Unregister all currently registered actions with the Neuro Game API.

Example:

python:
  neuro_unregister_all_actions()


### neuro_force_action
function neuro_force_action(action_names, query)

Force one or more actions with the Neuro Game API.\
action_names (list(string)): The names of the actions to force.\
query (string): A message that is sent along the force.


Example:

python:
  neuro_force_action(["notify"], "Please say hello or bye to chat.")