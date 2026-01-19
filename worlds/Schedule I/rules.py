from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import CollectionState
from worlds.generic.Rules import add_rule, set_rule

if TYPE_CHECKING:
    from .world import Schedule1World


def set_all_rules(world: Schedule1World, locationData, eventData) -> None:
    # In order for AP to generate an item layout that is actually possible for the player to complete,
    # we need to define rules for our Entrances and Locations.
    # Note: Regions do not have rules, the Entrances connecting them do!
    # We'll do entrances first, then locations, and then finally we set our victory condition.

    set_all_entrance_rules(world)
    set_all_location_rules(world, locationData, eventData)
    set_completion_condition(world)


def set_all_entrance_rules(world: Schedule1World) -> None:
    # First, we need to actually grab our entrances. Luckily, there is a helper method for this.
    overworld_to_missions = world.get_entrance("Overworld to Missions")
    overworld_to_customer_northtown = world.get_entrance("Overworld to Customer Northtown")

    if not world.options.randomize_cartel_influence:
        cartel_region_westville_to_customer_downtown = world.get_entrance("Cartel Westville to Customer Downtown")
        cartel_region_downtown_to_customer_docks = world.get_entrance("Cartel Downtown to Customer Docks")
        cartel_region_docks_to_customer_suburbia = world.get_entrance("Cartel Docks to Customer Suburbia")
        cartel_region_suburbia_to_customer_uptown = world.get_entrance("Cartel Suburbia to Customer Uptown")
    else:
        overworld_to_customer_downtown = world.get_entrance("Overworld to Customer Downtown")
        overworld_to_customer_docks = world.get_entrance("Overworld to Customer Docks")
        overworld_to_customer_suburbia = world.get_entrance("Overworld to Customer Suburbia")
        overworld_to_customer_uptown = world.get_entrance("Overworld to Customer Uptown")
    
    if world.options.randomize_level_unlocks:
        overworld_to_level_unlocks = world.get_entrance("Overworld to Level Unlocks")
        level_unlocks_to_customer_westville = world.get_entrance("Level Unlocks to Customer Westville")
        if not world.options.randomize_cartel_influence:    
            level_unlocks_to_cartel_westville = world.get_entrance("Level Unlocks to Cartel Westville")
    
    if not world.options.randomize_cartel_influence:
        cartel_region_westville_to_cartel_downtown = world.get_entrance("Cartel Westville to Cartel Downtown")
        cartel_region_downtown_to_cartel_docks = world.get_entrance("Cartel Downtown to Cartel Docks")
        cartel_region_docks_to_cartel_suburbia = world.get_entrance("Cartel Docks to Cartel Suburbia")
        cartel_region_suburbia_to_cartel_uptown = world.get_entrance("Cartel Suburbia to Cartel Uptown")
    
    if world.options.recipe_checks > 0:
        overworld_to_weed_recipe_checks = world.get_entrance("Overworld to Weed Recipe Checks")
        overworld_to_meth_recipe_checks = world.get_entrance("Overworld to Meth Recipe Checks")
        overworld_to_shrooms_recipe_checks = world.get_entrance("Overworld to Shrooms Recipe Checks")
        overworld_to_cocaine_recipe_checks = world.get_entrance("Overworld to Cocaine Recipe Checks")
    
    if world.options.randomize_business_properties or world.options.randomize_drug_making_properties:
        overworld_to_realtor = world.get_entrance("Overworld to Realtor")

    
    # An access rule is a function. We can define this function like any other function.
    # This function must accept exactly one parameter: A "CollectionState".
    # A CollectionState describes the current progress of the players in the multiworld, i.e. what items they have,
    # which regions they've reached, etc.
    # In an access rule, we can ask whether the player has a collected a certain item.
    # We can do this via the state.has(...) function.
    # This function takes an item name, a player number, and an optional count parameter (more on that below)
    # Since a rule only takes a CollectionState parameter, but we also need the player number in the state.has call,
    # our function needs to be locally defined so that it has access to the player number from the outer scope.
    # In our case, we are inside a function that has access to the "world" parameter, so we can use world.player.
    
    # Influence is all the matters when it comes to entrance rules.
    # If Cartel influence is not randomized, then 
    def can_reach_missions(state: CollectionState) -> bool:
        return True  # True always I guess
    
    def can_reach_level_unlocks(state: CollectionState) -> bool:
        return True  # If asking, it's true

    def can_access_northtown_customers(state: CollectionState) -> bool:
        # Can always access northtown
        # This is here because future updates may change this.
        return True
    
    # Check if 7 influence points have been collected for that region
    def can_access_westville(state: CollectionState) -> bool:
        if world.options.randomize_level_unlocks:
            return state.has("Westville Region Unlock", world.player)
        else:
            return True
    
    def can_access_downtown(state: CollectionState) -> bool:
        if world.options.randomize_cartel_influence:
            return state.has_all_counts({"Cartel Influence, Westville": 7}, world.player)
        elif state.has("Downtown Customers Unlocked", world.player):
            return True
        return False
    
    def can_access_docks(state: CollectionState) -> bool:
        if world.options.randomize_cartel_influence:
            return state.has_all_counts({"Cartel Influence, Downtown": 7}, world.player)
        elif state.has("Docks Customers Unlocked", world.player):
            return True
        return False
    
    def can_access_suburbia(state: CollectionState) -> bool:
        if world.options.randomize_cartel_influence:
            return state.has_all_counts({"Cartel Influence, Docks": 7}, world.player)
        elif state.has("Suburbia Customers Unlocked", world.player):
            return True
        return False
    
    def can_access_uptown(state: CollectionState) -> bool:
        if world.options.randomize_cartel_influence:
            return state.has_all_counts({"Cartel Influence, Suburbia": 7}, world.player)
        elif state.has("Uptown Customers Unlocked", world.player):
            return True
        return False
    
    # True for the time being, but could be randomized in the future
    def can_access_weed_recipe_checks(state: CollectionState) -> bool:
        if world.options.randomize_level_unlocks:
            if state.has_any(["Mixing Station Mk II Unlock", "Mixing Station Unlock"], world.player):
                return True
        elif state.has("Rank Hoodlum I Reached", world.player):
            return True
        return False
    
    def can_access_meth_recipe_checks(state: CollectionState) -> bool:
        if world.options.randomize_level_unlocks:
            if state.has_all(("Low-Quality Pseudo Unlock",
                              "Acid Unlock",
                              "Phosphorus Unlock",
                              "Chemistry Station Unlock",
                              "Lab Oven Unlock",
                              "Unlocked Meg or Jerry"), world.player) and state.has_any(
                                  ( "Mixing Station Unlock", 
                                    "Mixing Station Mk II Unlock"), world.player):
                return True
        elif state.has_all(("Unlocked Meg or Jerry", "Rank Hoodlum V Reached"), world.player):
            return True 
        return False
    
    def can_access_shrooms_recipe_checks(state: CollectionState) -> bool:
        if world.options.randomize_level_unlocks:
            if state.has(("Unlocked Elizabeth or Kevin"), world.player) and state.has_any(
                                  ( "Mixing Station Unlock", 
                                    "Mixing Station Mk II Unlock"), world.player):
                return True
        elif state.has_all(("Unlocked Elizabeth or Kevin", "Rank Hoodlum I Reached"), world.player):
            return True
        return False
    
    def can_access_cocaine_recipe_checks(state: CollectionState) -> bool:
        if world.options.randomize_level_unlocks: 
            if  state.has_all(("Coca Seed Unlock",
                                "Cauldron Unlock",
                                "Lab Oven Unlock",
                                "Gasoline Unlock",
                                "Unlocked Javier or Mac"), world.player) and state.has_any(
                                    ( "Mixing Station Unlock", 
                                    "Mixing Station Mk II Unlock"), world.player):
                return True
        elif state.has_all(("Unlocked Javier or Mac", "Rank Enforcer I Reached"), world.player):
            return True
        return False
    
    def can_access_realtor(state: CollectionState) -> bool:
        return True # Always accessible for now
    
    # Now we can set our "can_destroy_bush" rule to our entrance which requires slashing a bush to clear the path.
    # One way to set rules is via the set_rule() function, which works on both Entrances and Locations.
    set_rule(overworld_to_missions, can_reach_missions)  # Always accessible
    set_rule(overworld_to_customer_northtown, can_access_northtown_customers)
    if not world.options.randomize_cartel_influence:
        set_rule(cartel_region_westville_to_customer_downtown, can_access_downtown)
        set_rule(cartel_region_downtown_to_customer_docks, can_access_docks)
        set_rule(cartel_region_docks_to_customer_suburbia, can_access_suburbia)
        set_rule(cartel_region_suburbia_to_customer_uptown, can_access_uptown)
    else:
        set_rule(overworld_to_customer_downtown, can_access_downtown)
        set_rule(overworld_to_customer_docks, can_access_docks)
        set_rule(overworld_to_customer_suburbia, can_access_suburbia)
        set_rule(overworld_to_customer_uptown, can_access_uptown)

    if world.options.randomize_level_unlocks:
        set_rule(overworld_to_level_unlocks, can_reach_level_unlocks) # Always accessible
        set_rule(level_unlocks_to_customer_westville, can_access_westville)
        if not world.options.randomize_cartel_influence:
            set_rule(level_unlocks_to_cartel_westville, can_access_westville)
    
    if not world.options.randomize_cartel_influence:
        set_rule(cartel_region_westville_to_cartel_downtown, can_access_docks)
        set_rule(cartel_region_downtown_to_cartel_docks, can_access_docks)
        set_rule(cartel_region_docks_to_cartel_suburbia, can_access_suburbia)
        set_rule(cartel_region_suburbia_to_cartel_uptown, can_access_uptown)

    if world.options.recipe_checks > 0:
        set_rule(overworld_to_weed_recipe_checks, can_access_weed_recipe_checks)
        set_rule(overworld_to_meth_recipe_checks, can_access_meth_recipe_checks)
        set_rule(overworld_to_shrooms_recipe_checks, can_access_shrooms_recipe_checks)
        set_rule(overworld_to_cocaine_recipe_checks, can_access_cocaine_recipe_checks)

    if world.options.randomize_business_properties or world.options.randomize_drug_making_properties:
        set_rule(overworld_to_realtor, can_access_realtor)
    

def set_all_location_rules(world: Schedule1World, locationData, eventData) -> None:
    # NOTE: I had to hardcode these requirement types because it was impossible to pass function references

    # Reference for relevant locations
    locations = {}
    # Used to store requirements from events/locations
    requirements = {}
    requirements_type = ""

    # locations
    for location in locationData.locations.values():
        if "Permanent" in location.tags:
            locations[location.name] = world.get_location(location.name)
        elif world.options.randomize_level_unlocks:
            if "Level Up Reward" in location.tags:
                locations[location.name] = world.get_location(location.name)

    # events
    for event in eventData.events.values():
        if "Permanent" in event.tags:
            locations[event.locationName] = world.get_location(event.locationName)
        if world.options.goal != 1:
            if "Cartel" in event.tags:
                locations[event.locationName] = world.get_location(event.locationName)
        if world.options.goal < 2:
            if "Networth" in event.tags:
                locations[event.locationName] = world.get_location(event.locationName)
    
    # locations 
    # missions - always location checks - no alt requirements
    for location in locationData.locations.values():
        if "Mission" in location.tags:
            if "Level Up Reward Required" in location.tags:
                if world.options.randomize_level_unlocks:
                    requirements = location.requirements
                    requirements_type = location.requirements_type
                else:
                    requirements = location.requirements_alt
                    requirements_type = location.requirements_alt_type
                set_rule(locations[location.name], lambda state, reqs=requirements: state.has_all_counts(
                    reqs, world.player))
            elif "Customers Unlocked Required" in location.tags:
                if world.options.randomize_customers:
                    requirements = location.requirements
                    requirements_type = location.requirements_type
                else:
                    requirements = location.requirements_alt
                    requirements_type = location.requirements_alt_type
                set_rule(locations[location.name], lambda state, reqs=requirements: state.has_all_counts(
                    reqs, world.player))
            else:
                if location.requirements_type == "has_all_counts":
                    set_rule(locations[location.name], lambda state, reqs=location.requirements: state.has_all_counts(
                        reqs, world.player))
                elif location.requirements_type == "has_any_count":
                    set_rule(locations[location.name], lambda state, reqs=location.requirements: state.has_any_count(
                        reqs, world.player))
    
    # level unlocks
    for location in locationData.locations.values():
        if "Level Up Reward" in location.tags:
            if world.options.randomize_level_unlocks:
                requirements = location.requirements
                requirements_type = location.requirements_type
            else:
                requirements = location.requirements_alt
                requirements_type = location.requirements_alt_type
            if requirements_type == "has_any_count":
                set_rule(locations[location.name], lambda state, reqs=requirements: state.has_any_count(
                    reqs, world.player))
                
    # Events
    # missions - always location checks - no alt requirements
    for event in eventData.events.values():
        if "Mission" in event.tags:
            if "Level Up Reward Required" in event.tags:
                if world.options.randomize_level_unlocks:
                    requirements = event.requirements
                    requirements_type = event.requirements_type
                else:
                    requirements = event.requirements_alt
                    requirements_type = event.requirements_alt_type
                set_rule(locations[event.locationName], lambda state, reqs=requirements: state.has_all_counts(
                    reqs, world.player))
            elif "Customers Unlocked Required" in event.tags:
                if world.options.randomize_customers:
                    requirements = event.requirements
                    requirements_type = event.requirements_type
                else:
                    requirements = event.requirements_alt
                    requirements_type = event.requirements_alt_type
                set_rule(locations[event.locationName], lambda state, reqs=requirements: state.has_all_counts(
                    reqs, world.player))
            else:
                if event.requirements_type == "has_all_counts":
                    set_rule(locations[event.locationName], lambda state, reqs=event.requirements: state.has_all_counts(
                        reqs, world.player))
                elif event.requirements_type == "has_any_count":
                    set_rule(locations[event.locationName], lambda state, reqs=event.requirements: state.has_any_count(
                        reqs, world.player))

    # business properties
    for event in eventData.events.values():
        if world.options.randomize_business_properties:
            requirements = event.requirements
            requirements_type = event.requirements_type
        else: 
            requirements = event.requirements_alt
            requirements_type = event.requirements_alt_type
        if "Business Properties" in event.tags:
            if requirements_type == "has_all_counts":
                set_rule(locations[event.locationName], lambda state, reqs=requirements: state.has_all_counts(
                    reqs, world.player))
            elif requirements_type == "has_any_count":
                set_rule(locations[event.locationName], lambda state, reqs=requirements: state.has_any_count(
                    reqs, world.player))

    # Customer releated unlocks
    for event in eventData.events.values():
        if world.options.randomize_customers:
            requirements = event.requirements
            requirements_type = event.requirements_type
        else:
            requirements = event.requirements_alt
            requirements_type = event.requirements_alt_type
        if "Customers Unlocked" in event.tags:
            if requirements_type == "has_from_list":
                req_keys = list(requirements.keys())
                req_value = list(requirements.values())[0]
                set_rule(locations[event.locationName], lambda state, keys=req_keys, val=req_value: state.has_from_list(
                    keys, world.player, val))
            elif requirements_type == "has_any_count":
                set_rule(locations[event.locationName], lambda state, reqs=requirements: state.has_any_count(
                    reqs, world.player))
                
    # cartel influence
    for event in eventData.events.values():
        if world.options.randomize_cartel_influence:
            requirements = event.requirements
            requirements_type = event.requirements_type
        else:
            requirements = event.requirements_alt
            requirements_type = event.requirements_alt_type
        if "Cartel Influence" in event.tags:
            if requirements_type == "has_all_counts":
                set_rule(locations[event.locationName], lambda state, reqs=requirements: state.has_all_counts(
                    reqs, world.player))
            elif requirements_type == "has_any_count":
                set_rule(locations[event.locationName], lambda state, reqs=requirements: state.has_any_count(
                    reqs, world.player))

    # level unlocks
    for event in eventData.events.values():
        if "Level Up Reward" in event.tags:
            if world.options.randomize_level_unlocks:
                requirements = event.requirements
                requirements_type = event.requirements_type
            else:
                requirements = event.requirements_alt
                requirements_type = event.requirements_alt_type
            if requirements_type == "has_any_count":
                set_rule(locations[event.locationName], lambda state, reqs=requirements: state.has_any_count(
                    reqs, world.player))

    # Only need uptown unlocked to start cartel mission
    # Need 20 cocaine to finish it however
    if world.options.goal != 1:
        for event in eventData.events.values():
            if event.locationName == "Cartel Defeated":
                set_rule(locations[event.locationName], lambda state, reqs=event.requirements: state.has_all_counts(
                    reqs, world.player
                ))
    if world.options.goal < 2:
        # Always accessible because money is always obtainable.
        # Maybe we should say you need to unlock cocaine recipe checks to get money?
        # Will stay hardcoded until requirements are made if any
        set_rule(locations["Networth Goal Reached"], lambda state: True)  

def set_completion_condition(world: Schedule1World) -> None:
    # We'll keep this hardcoded as well for now.
    # There shouldn't be too many differences in how victory is achieved.
    if world.options.goal == 0:
        world.multiworld.completion_condition[world.player] = lambda state: state.has_all(
            ("Cartel Defeated", "Networth Goal Reached"), world.player)
    elif world.options.goal == 1:
        world.multiworld.completion_condition[world.player] = lambda state: state.has(
            "Networth Goal Reached", world.player)
    elif world.options.goal == 2:
        world.multiworld.completion_condition[world.player] = lambda state: state.has(
            "Cartel Defeated", world.player)