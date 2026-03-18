from __future__ import annotations

import shlex
from typing import Sequence

from dingtalk_cli.output import emit_success, set_output_state
from dingtalk_cli.utils.repl_skin import ReplSkin


COMMAND_HINTS = [
    "auth setup",
    "auth set-operator",
    "auth status",
    "workspace list",
    "workspace info",
    "node list",
    "node info",
    "node resolve-url",
    "doc create",
    "doc read",
    "doc overwrite",
    "doc delete",
    "workbook sheets",
    "workbook info",
    "workbook read",
    "member add",
    "member update",
    "member remove",
    "--json workspace list",
    "help",
    "quit",
]


def run_repl(dispatch: callable[[Sequence[str], bool], int]) -> None:
    skin = ReplSkin("dingtalk-cli")
    session = skin.create_prompt_session(COMMAND_HINTS)
    skin.print_banner()
    set_output_state(json_output=False, repl_mode=True)

    while True:
        try:
            line = skin.get_input(session)
        except EOFError:
            break
        except KeyboardInterrupt:
            skin.warning("已取消当前输入。")
            continue

        if not line.strip():
            continue
        if line.strip() in {"quit", "exit"}:
            break
        if line.strip() == "help":
            emit_success({"commands": COMMAND_HINTS}, "可用命令：")
            continue

        args = shlex.split(line)
        if args and args[0] == "dingtalk-cli":
            args = args[1:]
        if not args:
            continue
        dispatch(args, False)
        set_output_state(json_output=False, repl_mode=True)

    skin.print_goodbye()
