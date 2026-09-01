"""RESPOND TYPE=command prompt helper."""

from klipper_extras.respond_action import (
    prompt_end,
    prompt_show,
    respond_action,
    respond_error,
)


class _Gcode:
    def __init__(self):
        self.scripts = []

    def run_script_from_command(self, script):
        self.scripts.append(script)


def test_respond_action_and_error():
    gcode = _Gcode()
    respond_action(gcode, "action:prompt_begin Hello")
    respond_error(gcode, "cold")
    assert gcode.scripts[0] == 'RESPOND TYPE=command MSG="action:prompt_begin Hello"'
    assert gcode.scripts[1] == 'RESPOND TYPE=error MSG="cold"'


def test_escape_quotes():
    gcode = _Gcode()
    respond_action(gcode, 'say "hi"')
    assert gcode.scripts[0] == 'RESPOND TYPE=command MSG="say \'hi\'"'


def test_prompt_show_order():
    gcode = _Gcode()
    prompt_show(
        gcode,
        "RESUME aborted",
        ["Extruder not hot enough."],
        [("Ok", "RESPOND TYPE=command MSG=action:prompt_end", "")],
    )
    prompt_end(gcode)
    assert gcode.scripts[0].endswith('MSG="action:prompt_begin RESUME aborted"')
    assert "prompt_text Extruder not hot enough." in gcode.scripts[1]
    assert "prompt_footer_button Ok|RESPOND TYPE=command MSG=action:prompt_end" in gcode.scripts[2]
    assert gcode.scripts[3].endswith('MSG="action:prompt_show"')
    assert gcode.scripts[4].endswith('MSG="action:prompt_end"')
