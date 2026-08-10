"""
Pins the demo project's name to the frontend's list of demo project names.

The seeder names the project; the frontend keys behaviour off that exact string — the demo banner,
and the 24h default chart range that the compressed timeline (see test_demo_timeline) needs in order
to bucket hourly instead of collapsing into a single daily bar. Nothing at runtime connects the two,
so a rename on either side is silent: seeding still succeeds and the project still renders, just
without the demo treatment. This test is the connection.

If it fails, the fix is to add the new name to DEMO_PROJECT_NAMES on the frontend, not to loosen the
assertion. That constant is a list precisely so an old name can stay in it while a new one is rolled
out to already-seeded workspaces.
"""
import re
from pathlib import Path

import pytest

from opik_backend.demo_data_generator import DEMO_PROJECT_NAME

FRONTEND_CONSTANTS = (
    Path(__file__).resolve().parents[3] / "opik-frontend" / "src" / "constants" / "shared.ts"
)


def frontend_demo_project_names(source):
    """The string literals inside the frontend's `DEMO_PROJECT_NAMES` array.

    The array is written in terms of other constants (`[DEMO_PROJECT_NAME]`), so each entry is
    resolved against the `export const NAME = "value"` declarations in the same file.
    """
    literals = dict(re.findall(r'export const (\w+)\s*=\s*"([^"]*)"', source))

    array = re.search(
        r"export const DEMO_PROJECT_NAMES[^=]*=\s*\[(.*?)\]", source, re.DOTALL)
    assert array, "DEMO_PROJECT_NAMES array not found in the frontend constants"

    names = []
    for entry in (item.strip() for item in array.group(1).split(",")):
        if not entry:
            continue
        if entry.startswith('"'):
            names.append(entry.strip('"'))
        else:
            assert entry in literals, f"unresolved reference in DEMO_PROJECT_NAMES: {entry}"
            names.append(literals[entry])
    return names


@pytest.mark.skipif(
    not FRONTEND_CONSTANTS.exists(),
    reason="frontend checkout not present (image builds ship the python app alone)",
)
def test_frontend_recognises_the_seeded_demo_project_name():
    names = frontend_demo_project_names(FRONTEND_CONSTANTS.read_text())

    assert DEMO_PROJECT_NAME in names, (
        f"the seeder creates {DEMO_PROJECT_NAME!r} but the frontend only treats {names} as demo "
        f"projects, so the demo banner and the 24h chart default would not apply. Add it to "
        f"DEMO_PROJECT_NAMES in {FRONTEND_CONSTANTS.name}."
    )


@pytest.mark.skipif(
    not FRONTEND_CONSTANTS.exists(),
    reason="frontend checkout not present (image builds ship the python app alone)",
)
def test_the_name_list_is_not_empty_or_blank():
    """Guards the parser itself: an empty list would make the test above vacuous."""
    names = frontend_demo_project_names(FRONTEND_CONSTANTS.read_text())

    assert names, "DEMO_PROJECT_NAMES parsed as empty — the parser or the constant changed shape"
    assert all(name.strip() for name in names)


def test_the_seeder_uses_the_constant_rather_than_a_literal():
    """Both seeding paths must go through the constant, or the pin above only covers one of them."""
    source = (
        Path(__file__).resolve().parents[1].parent
        / "src" / "opik_backend" / "demo_data_generator.py"
    ).read_text()

    # One definition, no stray copies of the string elsewhere in the module.
    assert source.count(f'"{DEMO_PROJECT_NAME}"') == 1
    assert source.count("project_name = DEMO_PROJECT_NAME") == 2
