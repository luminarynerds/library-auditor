import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "data", "plain_language_map.json")


class TestPlainLanguageMap:
    def setup_method(self):
        with open(DATA_PATH) as f:
            self.mapping = json.load(f)

    def test_has_common_rules(self):
        required_rules = ["image-alt", "color-contrast", "label", "link-name", "html-has-lang"]
        for rule in required_rules:
            assert rule in self.mapping, f"Missing rule: {rule}"

    def test_each_entry_has_required_fields(self):
        for rule_id, entry in self.mapping.items():
            assert "title" in entry, f"{rule_id} missing title"
            assert "description" in entry, f"{rule_id} missing description"
            assert "fix" in entry, f"{rule_id} missing fix"
            assert "wcag" in entry, f"{rule_id} missing wcag"
            assert "impact" in entry, f"{rule_id} missing impact"
            assert "effort" in entry, f"{rule_id} missing effort"
            assert "help_url" in entry, f"{rule_id} missing help_url"
            assert entry["effort"] in ("quick", "developer", "redesign"), f"{rule_id} invalid effort"

    def test_no_jargon_in_titles(self):
        jargon = ["ARIA", "DOM", "axe", "a11y", "wcag", "element"]
        for rule_id, entry in self.mapping.items():
            title = entry["title"].lower()
            for word in jargon:
                assert word.lower() not in title, f"{rule_id} title contains jargon: '{word}'"
