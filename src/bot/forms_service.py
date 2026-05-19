from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class FormStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    HIDDEN = "hidden"


class FormFieldType(str, Enum):
    SHORT_TEXT = "short_text"
    LONG_TEXT = "long_text"
    NUMBER = "number"
    SELECT = "select"
    MULTISELECT = "multiselect"
    DATE = "date"
    BOOLEAN = "boolean"


@dataclass
class FormField:
    id: str
    form_id: str
    label: str
    type: FormFieldType
    required: bool = False
    options: list[str] = field(default_factory=list)
    order: int = 0
    validation_rules: dict[str, Any] = field(default_factory=dict)


@dataclass
class Form:
    id: str
    title: str
    description: str
    status: FormStatus
    created_by: str
    fields: list[FormField] = field(default_factory=list)


@dataclass
class FormSubmission:
    id: str
    form_id: str
    user_id: str
    answers: dict[str, Any]
    created_at: datetime


class FormValidationError(ValueError):
    pass


class FormService:
    def __init__(self) -> None:
        self._forms: dict[str, Form] = {}
        self._submissions: dict[str, list[FormSubmission]] = {}

    def create_form(self, title: str, description: str, created_by: str) -> Form:
        form = Form(
            id=str(uuid4()),
            title=title,
            description=description,
            status=FormStatus.DRAFT,
            created_by=created_by,
        )
        self._forms[form.id] = form
        return form

    def get_form(self, form_id: str) -> Form:
        form = self._forms.get(form_id)
        if not form:
            raise KeyError(f"Form not found: {form_id}")
        return form

    def list_forms(self) -> list[Form]:
        return list(self._forms.values())

    def add_field(
        self,
        form_id: str,
        label: str,
        field_type: str,
        required: bool = False,
        options: list[str] | None = None,
        order: int = 0,
        validation_rules: dict[str, Any] | None = None,
    ) -> FormField:
        form = self.get_form(form_id)
        options = options or []
        rules = validation_rules or {}
        normalized_type = FormFieldType(field_type)
        self._validate_field_definition(normalized_type, options, rules)

        field_obj = FormField(
            id=str(uuid4()),
            form_id=form_id,
            label=label,
            type=normalized_type,
            required=required,
            options=options,
            order=order,
            validation_rules=rules,
        )
        form.fields.append(field_obj)
        form.fields.sort(key=lambda f: f.order)
        return field_obj

    def update_field(self, form_id: str, field_id: str, **changes: Any) -> FormField:
        form = self.get_form(form_id)
        field_obj = self._find_field(form, field_id)

        new_type = FormFieldType(changes.get("type", field_obj.type))
        new_options = changes.get("options", field_obj.options)
        new_rules = changes.get("validation_rules", field_obj.validation_rules)
        self._validate_field_definition(new_type, new_options, new_rules)

        for attr in ("label", "required", "options", "order", "validation_rules"):
            if attr in changes:
                setattr(field_obj, attr, changes[attr])
        if "type" in changes:
            field_obj.type = new_type

        form.fields.sort(key=lambda f: f.order)
        return field_obj

    def remove_field(self, form_id: str, field_id: str) -> None:
        form = self.get_form(form_id)
        field_obj = self._find_field(form, field_id)
        form.fields.remove(field_obj)

    def publish_form(self, form_id: str) -> Form:
        form = self.get_form(form_id)
        form.status = FormStatus.PUBLISHED
        return form

    def hide_form(self, form_id: str) -> Form:
        form = self.get_form(form_id)
        form.status = FormStatus.HIDDEN
        return form

    def submit_form(self, form_id: str, user_id: str, answers: dict[str, Any]) -> FormSubmission:
        form = self.get_form(form_id)
        self._validate_answers(form, answers)

        submission = FormSubmission(
            id=str(uuid4()),
            form_id=form_id,
            user_id=user_id,
            answers=answers,
            created_at=datetime.now(timezone.utc),
        )
        self._submissions.setdefault(form_id, []).append(submission)
        return submission

    def as_lolka_ui_schema(self, form_id: str) -> dict[str, Any]:
        form = self.get_form(form_id)
        return {
            "id": form.id,
            "title": form.title,
            "description": form.description,
            "status": form.status.value,
            "fields": [
                {
                    "id": field_obj.id,
                    "label": field_obj.label,
                    "type": field_obj.type.value,
                    "required": field_obj.required,
                    "options": field_obj.options,
                    "order": field_obj.order,
                    "validation": field_obj.validation_rules,
                }
                for field_obj in sorted(form.fields, key=lambda item: item.order)
            ],
        }

    def _find_field(self, form: Form, field_id: str) -> FormField:
        for field_obj in form.fields:
            if field_obj.id == field_id:
                return field_obj
        raise KeyError(f"Field not found: {field_id}")

    def _validate_field_definition(
        self,
        field_type: FormFieldType,
        options: list[str],
        rules: dict[str, Any],
    ) -> None:
        if field_type in (FormFieldType.SELECT, FormFieldType.MULTISELECT) and not options:
            raise FormValidationError("Select/multiselect fields must have options")

        if field_type not in (FormFieldType.SELECT, FormFieldType.MULTISELECT) and options:
            raise FormValidationError("Only select/multiselect fields can have options")

        allowed_rules = {"min_length", "max_length", "min", "max"}
        unsupported = set(rules.keys()) - allowed_rules
        if unsupported:
            raise FormValidationError(f"Unsupported validation rules: {sorted(unsupported)}")

    def _validate_answers(self, form: Form, answers: dict[str, Any]) -> None:
        for field_obj in form.fields:
            value = answers.get(field_obj.id)
            if field_obj.required and value in (None, "", []):
                raise FormValidationError(f"Field '{field_obj.label}' is required")
            if value in (None, "", []):
                continue

            if field_obj.type in (FormFieldType.SHORT_TEXT, FormFieldType.LONG_TEXT):
                if not isinstance(value, str):
                    raise FormValidationError(f"Field '{field_obj.label}' must be text")
                min_length = field_obj.validation_rules.get("min_length")
                max_length = field_obj.validation_rules.get("max_length")
                if min_length is not None and len(value) < min_length:
                    raise FormValidationError(f"Field '{field_obj.label}' too short")
                if max_length is not None and len(value) > max_length:
                    raise FormValidationError(f"Field '{field_obj.label}' too long")

            elif field_obj.type == FormFieldType.NUMBER:
                if not isinstance(value, (int, float)):
                    raise FormValidationError(f"Field '{field_obj.label}' must be number")
                min_value = field_obj.validation_rules.get("min")
                max_value = field_obj.validation_rules.get("max")
                if min_value is not None and value < min_value:
                    raise FormValidationError(f"Field '{field_obj.label}' below min")
                if max_value is not None and value > max_value:
                    raise FormValidationError(f"Field '{field_obj.label}' above max")

            elif field_obj.type == FormFieldType.SELECT:
                if value not in field_obj.options:
                    raise FormValidationError(f"Field '{field_obj.label}' contains invalid option")

            elif field_obj.type == FormFieldType.MULTISELECT:
                if not isinstance(value, list):
                    raise FormValidationError(f"Field '{field_obj.label}' must be a list")
                invalid = [item for item in value if item not in field_obj.options]
                if invalid:
                    raise FormValidationError(f"Field '{field_obj.label}' contains invalid options: {invalid}")

            elif field_obj.type == FormFieldType.DATE:
                if not isinstance(value, str):
                    raise FormValidationError(f"Field '{field_obj.label}' must be ISO date string")
                try:
                    datetime.fromisoformat(value)
                except ValueError as exc:
                    raise FormValidationError(f"Field '{field_obj.label}' has invalid date") from exc

            elif field_obj.type == FormFieldType.BOOLEAN and not isinstance(value, bool):
                raise FormValidationError(f"Field '{field_obj.label}' must be boolean")
