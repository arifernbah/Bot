from typing import Any

class AttrDict(dict):
    """Dictionary subclass enabling attribute-style access to keys while retaining normal dict behaviour.

    This small helper lets the rest of the codebase treat a plain ``dict`` configuration
    (e.g. the one returned by ``auto_config_loader``) as if it were the original
    ``SmartConfig`` object that exposes values via attributes.  It transparently
    supports the usual ``dict`` methods (``.get`` / iteration / etc.) but also allows
    dotted access (``config.is_testnet``) and attribute assignment.  Missing
    attributes resolve to ``None`` (matching ``dict.get(key)`` default behaviour).

    A lightweight ``save_config`` stub is provided so callers such as the Telegram
    command handlers can invoke it safely when the underlying configuration came
    from a plain dictionary.  When desired, the caller can override this method
    with a real implementation.
    """

    # Attribute access -------------------------------------------------------
    def __getattr__(self, item: str) -> Any:
        # Fall-back to dict lookup; return None for missing keys to mimic `.get`.
        return self.get(item, None)

    # Attribute assignment ---------------------------------------------------
    def __setattr__(self, key: str, value: Any) -> None:
        # Ensure we do not overwrite internal dict attributes (like ``keys``).
        if key.startswith('__'):
            super().__setattr__(key, value)
        else:
            self[key] = value

    # Attribute deletion -----------------------------------------------------
    def __delattr__(self, item: str) -> None:
        if item in self:
            del self[item]
        else:
            super().__delattr__(item)

    # Compatibility stubs ----------------------------------------------------
    def save_config(self) -> None:  # noqa: D401 – simple stub
        """Persist the configuration if desired.

        The original ``SmartConfig`` class persists its state to *config.json*.
        When the bot is running with an ``AttrDict`` coming from the automatic
        equity-based loader we usually do not need to write anything to disk, so
        this method is implemented as a no-op to keep backward compatibility.
        """
        # Intentionally left blank – nothing to persist for plain dict configs.
        return