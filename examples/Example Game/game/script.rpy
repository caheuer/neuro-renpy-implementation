define p = Character("[playername]")

init python:
    def notify_func(data):
        text = data.get("text")
        if text is None:
            return (False, "Please supply a valid text.")
        renpy.notify(text)
        return (True, "Text displayed.")
    neuro_action_handlers["notify"] = notify_func


label start:
    python:
        playername = renpy.input("What is your name?", length=20)
        playername = playername.strip()

        if not playername:
            playername = "Neuro"

    "Hello, [playername]! Welcome to this example game."

    p "My name is [playername]."

    $ neuro_give_context("Hi! Only you can see this message.")

    "Neuro just got some context via the Neuro API."

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

        neuro_give_context("You can use the 'notify' action to display a notification. Try it out!", silent=True)

    "Neuro can now use the 'notify' action to display a notification."

label loop:
    "What do you want to do now?"

    menu:
        "Go back to start":
            jump start
        "Force Neuro to display a notification":
            "Neuro will be forced to say hello or bye."
            $ neuro_force_action(["notify"], "Please say hello or bye to chat.")
            jump loop
        "Continue":
            jump continue_game

label continue_game:
    $ neuro_unregister_action("notify")

    "The 'notify' action has been unregistered."

    "This is the end of the example game. Thanks for playing!"
        
