"""Layer B — the Claude Code plugin/marketplace manifests are well-formed, so
`/plugin marketplace add pmoust/greek-electricity-toolkit` keeps working."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(rel):
    return json.load(open(os.path.join(ROOT, rel), encoding="utf-8"))


def test_marketplace_manifest_well_formed():
    m = _load(".claude-plugin/marketplace.json")
    assert m.get("name")
    assert isinstance(m.get("plugins"), list) and m["plugins"], "marketplace must list >=1 plugin"
    for p in m["plugins"]:
        assert p.get("name"), "each plugin needs a name"
        assert p.get("source"), "each plugin needs a source"
        assert p.get("description"), "each plugin needs a description"


def test_plugin_manifest_matches_marketplace():
    p = _load(".claude-plugin/plugin.json")
    for field in ("name", "version", "description", "license"):
        assert p.get(field), f"plugin.json missing {field}"
    names = {pl["name"] for pl in _load(".claude-plugin/marketplace.json")["plugins"]}
    assert p["name"] in names, "plugin.json name not listed in marketplace.json"


def test_plugin_exposes_the_skill():
    # source "./" => plugin root is the repo; Claude Code discovers skills under skills/.
    skills_dir = os.path.join(ROOT, "skills")
    found = []
    for entry in os.listdir(skills_dir):
        skill_md = os.path.join(skills_dir, entry, "SKILL.md")
        if os.path.isfile(skill_md):  # follows the symlink to .claude/skills/<name>
            found.append(entry)
    assert "greek-electricity-bill-analysis" in found, \
        f"plugin must expose the skill via skills/; found {found}"
