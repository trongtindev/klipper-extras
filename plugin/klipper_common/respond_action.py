"""Emit Klipper RESPOND TYPE=command / error (Mainsail // action: prompts).

Requires the [respond] extra. No klippy import. Callers own payload text.
"""

from __future__ import annotations


def _escape_msg(payload: str) -> str:
    return payload.replace('"', "'")


def respond_action(gcode, payload: str) -> None:
    """RESPOND TYPE=command MSG=payload → // payload."""
    gcode.run_script_from_command(
        'RESPOND TYPE=command MSG="%s"' % (_escape_msg(payload),)
    )


def respond_error(gcode, payload: str) -> None:
    """RESPOND TYPE=error MSG=payload → !! payload."""
    gcode.run_script_from_command(
        'RESPOND TYPE=error MSG="%s"' % (_escape_msg(payload),)
    )


def prompt_end(gcode) -> None:
    respond_action(gcode, "action:prompt_end")


def prompt_show(gcode, title: str, lines, footer_buttons) -> None:
    """footer_buttons: (label, gcode_or_empty, color_or_empty)."""
    respond_action(gcode, "action:prompt_begin %s" % (title,))
    for line in lines:
        respond_action(gcode, "action:prompt_text %s" % (line,))
    for label, cmd, color in footer_buttons:
        part = "action:prompt_footer_button %s" % (label,)
        if cmd:
            part = "%s|%s" % (part, cmd)
            if color:
                part = "%s|%s" % (part, color)
        elif color:
            part = "%s||%s" % (part, color)
        respond_action(gcode, part)
    respond_action(gcode, "action:prompt_show")
