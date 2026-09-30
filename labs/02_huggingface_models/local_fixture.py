"""Sixteen invented local requests; no outside data and no quality benchmark."""


def rows() -> list[dict[str, str]]:
    texts = {
        "create_account": (
            "Create an account",
            "Register a new profile",
            "I want to sign up",
            "Help me join this service",
        ),
        "delete_account": (
            "Delete my account",
            "Close my profile",
            "Remove my registration",
            "I want to leave this service",
        ),
        "edit_account": (
            "Edit my account",
            "Change my profile name",
            "Update profile details",
            "Correct the name on my profile",
        ),
        "switch_account": (
            "Switch accounts",
            "Use my other profile",
            "Change the active user",
            "Sign in with a different account",
        ),
    }
    return [
        {"instruction": text, "intent": intent, "category": "ACCOUNT"}
        for intent, examples in texts.items()
        for text in examples
    ]
