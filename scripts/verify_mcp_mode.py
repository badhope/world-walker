"""MCP standalone mode contract.

This is a static contract check on purpose: it verifies the prompt/protocol
surface that external hosts consume, without needing a live MCP client.
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAIL = []


def check(name, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + name + (("   " + detail) if detail else ""))
    if not ok:
        FAIL.append(name)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


server = read("mcp_server.py")
brief = server.split('NEW_GAME_BRIEF = """', 1)[1].split('"""', 1)[0]
session_zero = server.split('SESSION_ZERO_BRIEF = """', 1)[1].split('"""', 1)[0]
protocol = read("docs/MCP_PLAY.md")
primitives = read("mcp_primitives.py")

check("M1 session_zero prompt is registered",
      'name="session_zero"' in server and "def session_zero" in server)
check("M2 session_zero asks the four opening questions",
      all(word in session_zero for word in ("类型", "玩法", "角色", "体验")))
check("M3 new_game brief requires publish_prose",
      "publish_prose" in brief)
check("M4 new_game brief forbids open_panel",
      "不要调用 open_panel" in brief and "open_panel" not in
      brief.replace("不要调用 open_panel", ""))
check("M5 MCP protocol doc exists and is panel-free",
      os.path.isfile(os.path.join(ROOT, "docs", "MCP_PLAY.md"))
      and "不调用 `open_panel`" in protocol)
check("M6 protocol resource points at docs/MCP_PLAY.md",
      "MCP_PLAY.md" in primitives and "GAME_MASTER_PROTOCOL" not in primitives)
check("M7 retired protocol file is gone",
      not os.path.exists(os.path.join(ROOT, "GAME_MASTER_PROTOCOL.md")))
check("M8 world bible is required before narration",
      "世界前提" in session_zero and "canon_init" in session_zero
      and "canon_brief" in brief and "canon_commit" in brief)

print("\n%d/%d passed" % (8 - len(FAIL) if FAIL else 8, 8))
raise SystemExit(1 if FAIL else 0)
