from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, Any, Union

from BaseClasses import CollectionState
from worlds.generic.Rules import add_rule, set_rule

from . import items
from .options import check_option_condition

if TYPE_CHECKING:
    from .world import Schedule1World


def set_all_rules(world: Schedule1World, locationData, regionData, victoryData) -> None:
    # In order for AP to generate an item layout that is actually possible for the player to complete,
    # we need to define rules for our Entrances and Locations.
    # Note: Regions do not have rules, the Entrances connecting them do!
    # We'll do entrances first, then locations, and then finally we set our victory condition.

    set_all_entrance_rules(world, regionData)
    set_all_location_rules(world, locationData)
    set_completion_condition(world, victoryData)


# Customers, dealers and suppliers are alternate routes to the same unlock: any one of them is
# enough. Every other option group (level unlocks, cartel influence, properties, ...) is a hard
# gate that must always hold on top of that.
PEOPLE_UNLOCK_OPTIONS = frozenset({
    "randomize_customers",
    "randomize_dealers",
    "randomize_suppliers",
})


def is_people_unlock_condition(condition_key: str) -> bool:
    """
    Check whether a requirement group is a customer/dealer/supplier unlock route.

    Only non-negated parts count. In a key like "randomize_cartel_influence&!randomize_customers"
    the "!randomize_customers" part is an applicability guard, not a requirement source, so that
    group is a hard gate rather than an unlock route.
    """
    positive_options = {
        part.strip() for part in condition_key.split('&')
        if part.strip() and not part.strip().startswith('!')
    }
    return bool(positive_options & PEOPLE_UNLOCK_OPTIONS)


def referenced_item_names(method_name: str, value: Any) -> list[str]:
    """Collect every item name a requirement value refers to, so they can be validated."""
    if method_name == "has":
        return [value]

    if method_name == "has_any":
        groups = value if value and isinstance(value[0], list) else [value]
        return [name for group in groups for name in group]

    if method_name in ("has_all", "has_all_counts"):
        # has_all is a list of names, has_all_counts is a dict keyed by name
        return list(value)

    if method_name == "has_from_list":
        tiers = value if isinstance(value, list) else [value]
        return [name for tier in tiers for name in tier]

    return []


def build_requirement_check(world: Schedule1World, method_name: str, value: Any) -> Callable[[CollectionState], bool]:
    """Build a requirement check function based on the method name and value from JSON."""

    # A misspelled item name can never be satisfied, which quietly weakens or over-tightens
    # logic depending on the check it sits in. Catch it at generation time instead.
    # A non-string entry means the value is the wrong shape for this method, which is worth
    # reporting the same way rather than blowing up later with a confusing error.
    unknown_items = [name for name in referenced_item_names(method_name, value)
                     if not isinstance(name, str) or name not in items.ITEM_NAME_TO_ID]
    if unknown_items:
        raise ValueError(
            f"Unknown item name(s) {unknown_items} in a '{method_name}' requirement. "
            f"They must exactly match a key in items.json."
        )

    if method_name == "has":
        # value is a single item name string
        return lambda state, v=value: state.has(v, world.player)
    
    elif method_name == "has_any":
        # value is a list of lists, e.g. [["Item1", "Item2"], ["Item3", "Item4"]]
        # Each inner list is its own requirement, so the player needs at least one item out of
        # every list. This mirrors how has_from_list treats a list of dicts.
        # A bare list of item names is accepted as a single group.
        groups = value if value and isinstance(value[0], list) else [value]
        return lambda state, g=groups: all(
            state.has_any(items, world.player) for items in g
        )

    elif method_name == "has_all":
        # value is a list of item names
        return lambda state, v=value: state.has_all(v, world.player)
    
    elif method_name == "has_all_counts":
        # value is a dict of {item_name: count}
        return lambda state, v=value: state.has_all_counts(v, world.player)
    
    elif method_name == "has_from_list":
        # value can be:
        # - A single dict: {item_name: count, ...} where all counts are the same
        # - A list of dicts: [{item_name: count, ...}, ...] for multiple tiers
        # For a list, we build checks for each dict and require all to pass
        if isinstance(value, list):
            # List of dicts - build a check for each dict
            checks = []
            for tier_dict in value:
                keys = list(tier_dict.keys())
                count = list(tier_dict.values())[0]  # All values in a tier should be the same
                checks.append((keys, count))
            return lambda state, c=checks: all(
                state.has_from_list(keys, world.player, count) for keys, count in c
            )
        else:
            # Single dict
            keys = list(value.keys())
            count = list(value.values())[0]  # All values should be the same count
            return lambda state, k=keys, c=count: state.has_from_list(k, world.player, c)
    
    # An unrecognised method is a typo in the JSON data. Returning an always-true check here
    # would silently drop the requirement from logic, so fail loudly instead.
    raise ValueError(
        f"Unknown requirement method '{method_name}' in the JSON data. "
        f"Supported methods: has, has_any, has_all, has_all_counts, has_from_list."
    )


def build_rule_from_requirements(world: Schedule1World, requirements: Union[bool, Dict[str, Any]], combine_people_unlocks: bool = True) -> Callable[[CollectionState], bool]:
    """
    Build a rule function from the requirements structure.

    requirements can be:
    - True (always accessible)
    - A dict with option conditions as keys

    combine_people_unlocks: If True, the customer/dealer/supplier groups are OR'd together
                            (any one of them unlocks the check) and every other group is AND'd
                            on top. If False, ALL applicable groups must be satisfied.
    """
    if requirements is True:
        return lambda state: True
    
    if not isinstance(requirements, dict):
        return lambda state: True
    
    # Build list of (option_name, checks) pairs
    condition_checks: list[tuple[str, list[Callable[[CollectionState], bool]]]] = []
    
    for option_name, checks in requirements.items():
        if not isinstance(checks, dict):
            continue
        
        check_functions = []
        for method_name, value in checks.items():
            check_func = build_requirement_check(world, method_name, value)
            check_functions.append(check_func)
        
        if check_functions:
            condition_checks.append((option_name, check_functions))
    
    if not condition_checks:
        return lambda state: True
    
    def rule_function(state: CollectionState) -> bool:
        unlock_results = []
        gate_results = []

        for condition_key, check_functions in condition_checks:
            if not check_option_condition(world, condition_key):
                # This option condition does not apply, so its checks are irrelevant
                continue

            # All checks within this condition must pass
            option_result = all(check(state) for check in check_functions)

            if combine_people_unlocks and is_people_unlock_condition(condition_key):
                unlock_results.append(option_result)
            else:
                gate_results.append(option_result)

        # Customer/dealer/supplier groups are alternate routes: at least one must pass.
        if unlock_results and not any(unlock_results):
            return False

        # Every other applicable group is a hard gate and must pass regardless.
        # With no applicable groups at all, both lists are empty and the rule passes.
        return all(gate_results)

    return rule_function


def set_all_entrance_rules(world: Schedule1World, regionData) -> None:
    """Set entrance rules based on region connection requirements from regions.json."""
    
    # Load all entrances into a dictionary once
    entrances_dict: Dict[str, Any] = {}
    
    for region_name, region_info in regionData.regions.items():
        for connected_region_name, requirements in region_info.connections.items():
            entrance_name = f"{region_name} to {connected_region_name}"
            try:
                entrances_dict[entrance_name] = world.get_entrance(entrance_name)
            except KeyError:
                # Entrance might not exist if region wasn't created
                continue
    
    # Set rules for each entrance
    for region_name, region_info in regionData.regions.items():
        for connected_region_name, requirements in region_info.connections.items():
            entrance_name = f"{region_name} to {connected_region_name}"
            
            if entrance_name not in entrances_dict:
                continue
            
            entrance = entrances_dict[entrance_name]
            rule = build_rule_from_requirements(world, requirements)
            set_rule(entrance, rule)


def set_all_location_rules(world: Schedule1World, locationData) -> None:
    """Set location rules based on requirements from locations.json."""
    
    # Build a dict of location name -> location object for locations that exist
    locations_dict: Dict[str, Any] = {}
    
    for loc_name, loc_data in locationData.locations.items():
        # Skip supplier locations if randomize_suppliers is enabled (they don't exist)
        if world.options.randomize_suppliers and "Supplier" in loc_data.tags:
            continue
        
        try:
            locations_dict[loc_name] = world.get_location(loc_name)
        except KeyError:
            # Location might not exist
            continue
    
    # Set rules for each location
    for loc_name, loc_data in locationData.locations.items():
        if loc_name not in locations_dict:
            continue
        
        location = locations_dict[loc_name]
        requirements = loc_data.requirements

        rule = build_rule_from_requirements(world, requirements)
        set_rule(location, rule)


def set_completion_condition(world: Schedule1World, victoryData) -> None:
    # Victory conditions are loaded from victory.json
    # Goal options:
    #   0 = bomb_fragments_only: collect N bomb fragments
    #   1 = missions_only: complete cartel missions
    #   2 = missions_networth: complete cartel missions (networth checked in-game)
    #   3 = missions_bomb_fragments: complete cartel missions AND collect N bomb fragments
    #   4 = missions_networth_bomb_fragments: complete cartel missions AND collect N bomb fragments (networth in-game)
    #   5 = bomb_fragments_networth: collect N bomb fragments (networth checked in-game)

    requires_missions = world.options.goal in (1, 2, 3, 4)
    requires_fragments = world.options.goal in (0, 3, 4, 5)

    rules: list[Callable[[CollectionState], bool]] = []

    if requires_missions:
        # victory.json lists customers and suppliers as independent goal requirements rather than
        # as alternate unlock routes, so every group is AND'd here.
        rules.append(build_rule_from_requirements(world, victoryData.requirements, combine_people_unlocks=False))

    if requires_fragments:
        fragments_required = int(world.options.number_of_bomb_fragments_required)
        rules.append(lambda state, count=fragments_required: state.has("Bomb Fragment", world.player, count))

    # Every valid goal (0-4) populates at least one rule
    world.multiworld.completion_condition[world.player] = lambda state: all(rule(state) for rule in rules)