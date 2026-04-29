# High-Fidelity Aircraft Specification Database (NATO/Sweden)

AIRCRAFT_DB = {
    "gripen-e": {
        "name": "JAS 39 Gripen E",
        "role": "fighter",
        "origin": "sweden",
        "fuel_max": 3400, # kg
        "range_km": 1500,
        "weapon_capacity": {
            "standard": {"meteor": 4, "iris-t": 2},
            "heavy": {"meteor": 6, "iris-t": 2} # No drop tanks
        },
        "drop_tank_bonus": 800, # km additional range
        "drop_tank_penalty": 2 # loses 2 weapon pylons
    },
    "f-35a": {
        "name": "F-35A Lightning II",
        "role": "fighter",
        "origin": "usa",
        "fuel_max": 8278, # kg
        "range_km": 2200,
        "weapon_capacity": {
            "stealth": {"amraam": 4},
            "beast": {"amraam": 6, "sidewinder": 2}
        },
        "drop_tank_bonus": 0, # F-35 usually doesn't use external tanks in stealth
        "drop_tank_penalty": 0
    },
    "globaleye": {
        "name": "Saab GlobalEye",
        "role": "awacs",
        "origin": "sweden",
        "fuel_max": 15000,
        "range_km": 11000, # 11+ hours endurance
        "weapon_capacity": {}, # Non-kinetic
        "drop_tank_bonus": 0,
        "drop_tank_penalty": 0
    },
    "e-3": {
        "name": "E-3 Sentry (AWACS)",
        "role": "awacs",
        "origin": "usa",
        "fuel_max": 90000,
        "range_km": 9000,
        "weapon_capacity": {}, # Non-kinetic
        "drop_tank_bonus": 0,
        "drop_tank_penalty": 0
    }
}
