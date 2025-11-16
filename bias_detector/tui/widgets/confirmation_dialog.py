"""
Confirmation Dialog Widget for TUI.

Provides modal confirmation dialogs for destructive actions.
"""

from typing import Optional, Callable
from textual.app import ComposeResult
from textual.containers import Center, Vertical, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Static, Checkbox
from textual.binding import Binding


class ConfirmationDialog(ModalScreen[bool]):
    """
    Modal confirmation dialog for destructive actions.

    Features:
    - Customizable title and message
    - Yes/No buttons with keyboard shortcuts
    - Optional "Don't ask again" checkbox
    - Configurable button labels
    """

    BINDINGS = [
        Binding("y", "confirm", "Yes"),
        Binding("n", "cancel", "No"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        title: str = "Confirm Action",
        message: str = "Are you sure?",
        confirm_text: str = "Yes",
        cancel_text: str = "No",
        show_dont_ask: bool = False,
        dont_ask_text: str = "Don't ask again",
        **kwargs
    ):
        """Initialize confirmation dialog.

        Args:
            title: Dialog title
            message: Confirmation message
            confirm_text: Text for confirm button
            cancel_text: Text for cancel button
            show_dont_ask: Whether to show "Don't ask again" checkbox
            dont_ask_text: Text for "Don't ask again" checkbox
        """
        super().__init__(**kwargs)
        self.title = title
        self.message = message or "Are you sure?"
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
        self.show_dont_ask = show_dont_ask
        self.dont_ask_text = dont_ask_text
        self.dont_ask_checked = False

    def compose(self) -> ComposeResult:
        """Compose the confirmation dialog."""
        with Center():
            with Vertical(classes="confirmation-dialog"):
                # Title
                yield Static(self.title, classes="dialog-title")

                # Message
                yield Static(self.message or "Are you sure?", classes="dialog-message")

                # Don't ask again checkbox (optional)
                if self.show_dont_ask:
                    yield Checkbox(
                        self.dont_ask_text,
                        value=self.dont_ask_checked,
                        id="dont-ask-checkbox",
                        classes="dont-ask-checkbox"
                    )

                # Buttons
                with Horizontal(classes="dialog-buttons"):
                    yield Button(
                        self.cancel_text,
                        variant="default",
                        id="cancel-button",
                        classes="cancel-button"
                    )
                    yield Button(
                        self.confirm_text,
                        variant="error",  # Red for destructive actions
                        id="confirm-button",
                        classes="confirm-button"
                    )

    def on_checkbox_changed(self, event) -> None:
        """Handle don't ask again checkbox changes."""
        if event.checkbox.id == "dont-ask-checkbox":
            self.dont_ask_checked = event.checkbox.value

    def on_button_pressed(self, event) -> None:
        """Handle button presses."""
        if event.button.id == "confirm-button":
            self.action_confirm()
        elif event.button.id == "cancel-button":
            self.action_cancel()

    def action_confirm(self) -> None:
        """Confirm the action."""
        self.dismiss(True)

    def action_cancel(self) -> None:
        """Cancel the action."""
        self.dismiss(False)

    @property
    def dont_ask_again(self) -> bool:
        """Get whether user selected 'Don't ask again'."""
        return self.dont_ask_checked


class ConfirmationManager:
    """
    Manager for confirmation dialogs with user preferences.

    Remembers "Don't ask again" choices and provides convenient methods
    for common confirmation scenarios.
    """

    def __init__(self):
        """Initialize confirmation manager."""
        self._dont_ask_again = {}  # action -> bool

    def should_ask(self, action: str) -> bool:
        """Check if we should ask for confirmation for an action."""
        return not self._dont_ask_again.get(action, False)

    def set_dont_ask_again(self, action: str, dont_ask: bool) -> None:
        """Set the 'don't ask again' preference for an action."""
        self._dont_ask_again[action] = dont_ask

    def confirm_delete(self, item_type: str, item_name: str) -> bool:
        """Confirm deletion of an item (placeholder - always returns True for now)."""
        action = f"delete_{item_type}"
        if not self.should_ask(action):
            return True
        # TODO: Implement proper confirmation dialog
        return True

    def confirm_cancel(self, item_type: str, item_name: str) -> bool:
        """Confirm cancellation of an operation (placeholder - always returns True for now)."""
        action = f"cancel_{item_type}"
        if not self.should_ask(action):
            return True
        # TODO: Implement proper confirmation dialog
        return True

    def confirm_reset(self, item_type: str) -> bool:
        """Confirm reset of configuration (placeholder - always returns True for now)."""
        action = f"reset_{item_type}"
        if not self.should_ask(action):
            return True
        # TODO: Implement proper confirmation dialog
        return True


# Global confirmation manager instance
confirmation_manager = ConfirmationManager()