import inspect
from django.apps import apps
from .access_rules import AccessRules


class Ability:
    def __init__(self, access_rules: AccessRules):
        self.access_rules = access_rules

    def validate_model(self, action, model):
        can_count = 0
        cannot_count = 0
        model_abilities = filter(
            lambda c: c["model"] == model and c["action"] == action,
            self.access_rules.rules,
        )
        for c in model_abilities:
            if c["type"] == "can":
                can_count += 1
            if c["type"] == "cannot":
                cannot_count += 1

        if cannot_count > 0:
            return False
        if can_count == 0:
            return False
        return True

    def validate_instance(self, action, instance):
        model = instance._meta.model
        model_abilities = filter(
            lambda c: c["model"] == model and c["action"] == action,
            self.access_rules.rules,
        )

        query_sets = []
        for c in model_abilities:
            if c["type"] == "can":
                qs = model.objects.all().filter(
                    pk=instance.id, **c.get("conditions", {})
                )

            if c["type"] == "cannot":
                raise NotImplementedError("cannot-type rules are not yet implemented")

            query_sets.append(qs)

        if len(query_sets) == 0:
            return False

        can_query_set = query_sets.pop()
        for qs in query_sets:
            can_query_set |= qs

        return can_query_set.count() > 0

    def can(self, action, model_or_instance) -> bool:
        action = self.access_rules.alias_to_action(action)
        if inspect.isclass(model_or_instance):
            return self.validate_model(action, model_or_instance)
        else:
            return self.validate_instance(action, model_or_instance)

    def queryset_for(self, action, model):
        action = self.access_rules.alias_to_action(action)

        model_abilities = filter(
            lambda c: c["model"] == model and c["action"] == action,
            self.access_rules.rules,
        )

        query_sets = []
        for c in model_abilities:
            if c["type"] == "can" and "conditions" in c:
                qs = model.objects.all().filter(**c.get("conditions", {}))

            if c["type"] == "cannot":
                raise NotImplementedError("cannot-type rules are not yet implemented")

            query_sets.append(qs)

        if len(query_sets) == 0:
            return model.objects.none()

        can_query_set = query_sets.pop()
        for qs in query_sets:
            can_query_set |= qs

        return can_query_set
