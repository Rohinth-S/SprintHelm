#!/usr/bin/env python3
"""
Self-contained skill and configuration validator for CodinzHub Sprint Guardian.
Validates SKILL.md, team-map.yaml, prompt templates, and agent interface schemas.
"""

from pathlib import Path
import sys
import yaml

ROOT_DIR = Path(__file__).parent.parent


def validate():
    errors = []
    print("[*] Validating CodinzHub Sprint Guardian configuration...")

    # 1. Validate SKILL.md
    skill_file = ROOT_DIR / "SKILL.md"
    if not skill_file.is_file():
        errors.append("SKILL.md is missing from root directory.")
    else:
        content = skill_file.read_text(encoding="utf-8")
        if not content.startswith("---"):
            errors.append("SKILL.md is missing YAML frontmatter header ('---').")
        else:
            parts = content.split("---", 2)
            if len(parts) < 3:
                errors.append("SKILL.md YAML frontmatter is not closed properly.")
            else:
                try:
                    meta = yaml.safe_load(parts[1]) or {}
                    if not meta.get("name"):
                        errors.append("SKILL.md frontmatter is missing 'name' attribute.")
                    if not meta.get("description"):
                        errors.append("SKILL.md frontmatter is missing 'description' attribute.")
                    print(f"    [+] SKILL.md validated: name='{meta.get('name')}', version='{meta.get('metadata', {}).get('version', 'unknown')}'")
                except Exception as e:
                    errors.append(f"SKILL.md YAML frontmatter parsing error: {e}")

    # 2. Validate team-map YAML
    team_map = ROOT_DIR / "references" / "team-map.example.yaml"
    if not team_map.is_file():
        errors.append("references/team-map.example.yaml is missing.")
    else:
        try:
            with open(team_map, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                authorities = (data.get("approval") or {}).get("assigning_authorities") or []
                team = data.get("team") or []
                if not authorities:
                    errors.append("team-map.example.yaml missing approval.assigning_authorities.")
                if not team:
                    errors.append("team-map.example.yaml missing team member declarations.")
                print(f"    [+] team-map.example.yaml validated: {len(team)} team members, {len(authorities)} authorities.")
        except Exception as e:
            errors.append(f"team-map.example.yaml parsing error: {e}")

    # 3. Validate all 9 prompt templates
    expected_modes = [
        "shape-sprint",
        "triage-queue",
        "suggest-owner",
        "balance-load",
        "inspect-sprint",
        "surface-risk",
        "progress-pulse",
        "standup-brief",
        "retro-notes",
    ]
    prompts_dir = ROOT_DIR / "automation" / "prompts"
    for mode in expected_modes:
        p_file = prompts_dir / f"{mode}.md"
        if not p_file.is_file():
            errors.append(f"Missing prompt template: automation/prompts/{mode}.md")
        else:
            size = p_file.stat().st_size
            if size < 50:
                errors.append(f"Prompt template {mode}.md is unusually short ({size} bytes).")

    print(f"    [+] All {len(expected_modes)} prompt templates verified.")

    # 4. Validate agent schema
    agent_yaml = ROOT_DIR / "agents" / "openai.yaml"
    if agent_yaml.is_file():
        try:
            with open(agent_yaml, "r", encoding="utf-8") as f:
                ag_data = yaml.safe_load(f) or {}
                if "interface" not in ag_data:
                    errors.append("agents/openai.yaml missing 'interface' section.")
                print("    [+] agents/openai.yaml schema verified.")
        except Exception as e:
            errors.append(f"agents/openai.yaml parsing error: {e}")

    if errors:
        print("\n[!] VALIDATION FAILED WITH ERRORS:")
        for err in errors:
            print(f"    - {err}")
        sys.exit(1)
    else:
        print("\n[SUCCESS] CodinzHub Sprint Guardian configuration is 100% valid and production-ready!")
        sys.exit(0)


if __name__ == "__main__":
    validate()
