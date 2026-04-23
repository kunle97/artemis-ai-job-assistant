"""
Inspection normalizer.

Normalizes raw inspected fields into a cleaner, more automation-friendly shape.

Key responsibilities:
- dedupe noisy controls
- normalize labels
- convert adjacent radio inputs with the same name into a single radio_group
"""

from __future__ import annotations


class InspectionNormalizer:
    def normalize(self, inspected_fields: list[dict]) -> list[dict]:
        if not inspected_fields:
            return []

        fields = [self._normalize_field(field) for field in inspected_fields]
        fields = self._group_radio_fields(fields)
        fields = self._drop_redundant_buttons(fields)
        return fields

    def _normalize_field(self, field: dict) -> dict:
        normalized = dict(field)

        normalized["field_type"] = normalized.get("field_type")
        normalized["input_subtype"] = normalized.get("input_subtype")
        normalized["label"] = self._clean_label(normalized.get("label"))
        normalized["name"] = normalized.get("name")
        normalized["placeholder"] = self._clean_label(normalized.get("placeholder"))
        normalized["required"] = bool(normalized.get("required", False))
        normalized["value"] = normalized.get("value")
        normalized["option_value"] = normalized.get("option_value")
        normalized["option_label"] = self._clean_label(normalized.get("option_label"))
        normalized["group_label"] = self._clean_label(normalized.get("group_label"))

        if "options" in normalized and normalized["options"]:
            normalized["options"] = [
                {
                    "label": self._clean_label(option.get("label")),
                    "value": option.get("value"),
                }
                for option in normalized["options"]
            ]

        return normalized

    def _group_radio_fields(self, fields: list[dict]) -> list[dict]:
        grouped: list[dict] = []
        index = 0

        while index < len(fields):
            current = fields[index]

            if not self._is_radio_field(current):
                grouped.append(current)
                index += 1
                continue

            radio_name = current.get("name")
            radio_group = [current]
            next_index = index + 1

            while next_index < len(fields):
                candidate = fields[next_index]
                if not self._is_radio_field(candidate):
                    break
                if candidate.get("name") != radio_name:
                    break
                radio_group.append(candidate)
                next_index += 1

            if len(radio_group) == 1:
                grouped.append(current)
                index += 1
                continue

            grouped.append(self._build_radio_group(radio_group))
            index = next_index

        return grouped

    def _is_radio_field(self, field: dict) -> bool:
        field_type = (field.get("field_type") or "").lower()
        input_subtype = (field.get("input_subtype") or "").lower()

        return (
            (field_type == "radio")
            or (field_type == "input" and input_subtype == "radio")
            or (input_subtype == "radio")
        ) and bool(field.get("name"))

    def _build_radio_group(self, radio_group: list[dict]) -> dict:
        first = radio_group[0]

        group_label = self._first_meaningful_label(radio_group)
        group_required = any(bool(item.get("required")) for item in radio_group)

        options = []
        seen = set()

        for item in radio_group:
            option_label = self._infer_radio_option_label(item)
            option_value = item.get("value") or item.get("option_value") or option_label

            dedupe_key = ((option_label or "").strip().lower(), (option_value or "").strip().lower())
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            options.append(
                {
                    "label": option_label,
                    "value": option_value,
                }
            )

        return {
            "field_type": "radio_group",
            "input_subtype": "radio_group",
            "label": group_label,
            "name": first.get("name"),
            "placeholder": None,
            "required": group_required,
            "options": options,
        }

    def _infer_radio_option_label(self, field: dict) -> str | None:
        if field.get("option_label"):
            return self._clean_label(field.get("option_label"))

        label = self._clean_label(field.get("label"))
        if label:
            return label

        value = field.get("value") or field.get("option_value")
        if isinstance(value, str) and value.strip():
            return value.strip()

        return None

    def _first_meaningful_label(self, radio_group: list[dict]) -> str | None:
        for item in radio_group:
            label = self._clean_label(item.get("group_label"))
            if label:
                return label

        for item in radio_group:
            label = self._clean_label(item.get("label"))
            if not label:
                continue
            lowered = label.lower()
            if lowered not in {"yes", "no", "true", "false"}:
                return label

        return None

    def _drop_redundant_buttons(self, fields: list[dict]) -> list[dict]:
        cleaned: list[dict] = []
        seen_button_labels = set()

        for field in fields:
            if field.get("field_type") != "button":
                cleaned.append(field)
                continue

            label = (field.get("label") or "").strip().lower()
            dedupe_key = (label, field.get("name"))

            if dedupe_key in seen_button_labels:
                continue

            seen_button_labels.add(dedupe_key)
            cleaned.append(field)

        return cleaned

    def _clean_label(self, value: str | None) -> str | None:
        if not value:
            return None

        cleaned = " ".join(str(value).split()).strip()
        return cleaned or None