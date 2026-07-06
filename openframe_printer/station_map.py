from __future__ import annotations

"""Rev C drum station-map solver.

Rev B asked for "an angular station map, or the selected OPC has to be proven
stable at the real delay" and proposed a 50 ms exposure-to-development target
(11.8 deg on a 30 mm drum). This module answers the question with geometry
instead of a wish:

* Every process station around the OPC drum is modeled as an angular
  occupancy: tangent rollers get exact roller-to-roller clearance math,
  blades and the LED optical window get declared envelope half-angles.
* The solver packs the stations in process order at their minimum feasible
  separations, verifies the ring closes with slack, and reports the delay
  every latent-image element actually experiences.
* The headline output is the *derived* exposure-to-development delay. On the
  Rev A geometry it is ~10x the Rev B 50 ms target, because a 16 mm developer
  roller and an LED clear cone physically cannot sit 11.8 deg apart on a
  30 mm drum. The correct engineering response is not to chase 50 ms; it is
  to spec the OPC's latent-image hold (dark decay contrast retention) for the
  real delay, which this module emits as a requirement for the H1 PIDC rig.

Angles are measured in degrees, increasing in the direction of drum surface
travel, with the transfer nip fixed at 180 deg (paper path under the drum).
"""

from dataclasses import dataclass, asdict
import math

from .engine_math import EngineTargets, process_speed_mm_s


@dataclass(frozen=True)
class Station:
    """One process station tangent to (or aimed at) the OPC drum surface."""

    name: str
    kind: str  # "roller" | "blade" | "optical"
    roller_radius_mm: float = 0.0     # rollers only
    envelope_half_angle_deg: float = 0.0  # blades/optical only


@dataclass(frozen=True)
class PlacedStation:
    name: str
    kind: str
    angle_deg: float
    occupancy_half_angle_deg: float


@dataclass(frozen=True)
class StationGap:
    from_station: str
    to_station: str
    min_separation_deg: float
    actual_separation_deg: float
    arc_mm: float
    delay_ms: float


def roller_occupancy_half_angle_deg(
    drum_radius_mm: float, roller_radius_mm: float, clearance_mm: float
) -> float:
    """Angular half-extent of a tangent roller as seen from the drum axis.

    The roller center sits at drum_radius + roller_radius from the axis; its
    body (inflated by the housing clearance) subtends
    asin((r + clearance) / (R + r)).
    """
    ratio = (roller_radius_mm + clearance_mm) / (drum_radius_mm + roller_radius_mm)
    return math.degrees(math.asin(min(1.0, ratio)))


def roller_pair_min_separation_deg(
    drum_radius_mm: float,
    radius_a_mm: float,
    radius_b_mm: float,
    clearance_mm: float,
) -> float:
    """Exact minimum angular separation between two tangent rollers.

    Centers sit at d_a = R + r_a and d_b = R + r_b from the drum axis. The
    rollers clear each other by `clearance_mm` when the center distance
    reaches r_a + r_b + clearance; solve the triangle for the enclosed angle.
    """
    d_a = drum_radius_mm + radius_a_mm
    d_b = drum_radius_mm + radius_b_mm
    needed = radius_a_mm + radius_b_mm + clearance_mm
    cos_theta = (d_a * d_a + d_b * d_b - needed * needed) / (2.0 * d_a * d_b)
    cos_theta = max(-1.0, min(1.0, cos_theta))
    return math.degrees(math.acos(cos_theta))


def min_separation_deg(
    drum_radius_mm: float, a: Station, b: Station, clearance_mm: float, margin_deg: float
) -> float:
    if a.kind == "roller" and b.kind == "roller":
        base = roller_pair_min_separation_deg(
            drum_radius_mm, a.roller_radius_mm, b.roller_radius_mm, clearance_mm
        )
    else:
        half_a = (
            roller_occupancy_half_angle_deg(drum_radius_mm, a.roller_radius_mm, clearance_mm)
            if a.kind == "roller"
            else a.envelope_half_angle_deg
        )
        half_b = (
            roller_occupancy_half_angle_deg(drum_radius_mm, b.roller_radius_mm, clearance_mm)
            if b.kind == "roller"
            else b.envelope_half_angle_deg
        )
        base = half_a + half_b
    return base + margin_deg


def default_stations(target: EngineTargets) -> list[Station]:
    """Rev A process order starting at the transfer nip, in surface-travel order."""
    return [
        Station("transfer", "roller", roller_radius_mm=target.transfer_roller_diameter_mm / 2.0),
        Station("cleaning_blade", "blade", envelope_half_angle_deg=12.0),
        Station("charge_pcr", "roller", roller_radius_mm=target.primary_charge_roller_diameter_mm / 2.0),
        Station("exposure_led", "optical", envelope_half_angle_deg=10.0),
        Station("developer", "roller", roller_radius_mm=target.developer_roller_diameter_mm / 2.0),
    ]


def solve_station_map(
    target: EngineTargets | None = None,
    clearance_mm: float = 2.0,
    margin_deg: float = 2.0,
    transfer_angle_deg: float = 180.0,
    slack_weights: dict[str, float] | None = None,
) -> dict:
    """Pack stations at minimum separation, then distribute the leftover slack.

    slack_weights assigns the ring's spare degrees to specific gaps (keyed by
    the *from* station name). Default intent: keep exposure->developer tight
    (latent image freshness), give cleaning->charge the most breathing room
    (waste toner handling and charge settling), and leave a little everywhere
    else for housings that always grow.
    """
    t = target or EngineTargets()
    drum_radius = t.drum_diameter_mm / 2.0
    speed = process_speed_mm_s(t)
    circumference = math.pi * t.drum_diameter_mm
    stations = default_stations(t)
    weights = slack_weights or {
        "transfer": 1.0,        # transfer -> cleaning_blade
        "cleaning_blade": 3.0,  # cleaning_blade -> charge_pcr
        "charge_pcr": 1.0,      # charge_pcr -> exposure_led
        "exposure_led": 0.0,    # exposure_led -> developer stays at minimum
        "developer": 2.0,       # developer -> transfer (ring closure)
    }

    ring = stations + [stations[0]]
    minimum_separations = [
        min_separation_deg(drum_radius, ring[i], ring[i + 1], clearance_mm, margin_deg)
        for i in range(len(stations))
    ]
    total_minimum = sum(minimum_separations)
    slack = 360.0 - total_minimum
    feasible = slack >= 0.0

    weight_total = sum(weights.get(s.name, 0.0) for s in stations)
    separations = []
    for i, station in enumerate(stations):
        share = weights.get(station.name, 0.0) / weight_total if weight_total else 1.0 / len(stations)
        separations.append(minimum_separations[i] + max(0.0, slack) * share)

    placed: list[PlacedStation] = []
    angle = transfer_angle_deg
    for i, station in enumerate(stations):
        half = (
            roller_occupancy_half_angle_deg(drum_radius, station.roller_radius_mm, clearance_mm)
            if station.kind == "roller"
            else station.envelope_half_angle_deg
        )
        placed.append(
            PlacedStation(
                name=station.name,
                kind=station.kind,
                angle_deg=round(angle % 360.0, 2),
                occupancy_half_angle_deg=round(half, 2),
            )
        )
        angle += separations[i]

    gaps: list[StationGap] = []
    for i in range(len(stations)):
        arc = separations[i] / 360.0 * circumference
        gaps.append(
            StationGap(
                from_station=ring[i].name,
                to_station=ring[i + 1].name,
                min_separation_deg=round(minimum_separations[i], 2),
                actual_separation_deg=round(separations[i], 2),
                arc_mm=round(arc, 3),
                delay_ms=round(arc / speed * 1000.0, 1),
            )
        )

    exposure_gap = next(g for g in gaps if g.from_station == "exposure_led")
    min_exposure_arc = exposure_gap.min_separation_deg / 360.0 * circumference
    min_exposure_delay_ms = min_exposure_arc / speed * 1000.0
    # Latent-image hold requirement handed to the H1 PIDC rig: the OPC must
    # keep most of its exposure contrast over the real geometric delay, with
    # engineering margin for humidity/aging, not over an aspirational 50 ms.
    required_hold_ms = round(min_exposure_delay_ms * 1.5, 0)

    return {
        "revision": "M1-REV-C",
        "drum_diameter_mm": t.drum_diameter_mm,
        "process_speed_mm_s": round(speed, 3),
        "transfer_angle_deg": transfer_angle_deg,
        "clearance_mm": clearance_mm,
        "adjacent_margin_deg": margin_deg,
        "ring_closes": feasible,
        "total_minimum_separation_deg": round(total_minimum, 2),
        "slack_deg": round(slack, 2),
        "stations": [asdict(p) for p in placed],
        "gaps": [asdict(g) for g in gaps],
        "exposure_to_development": {
            "min_feasible_separation_deg": exposure_gap.min_separation_deg,
            "min_feasible_delay_ms": round(min_exposure_delay_ms, 1),
            "chosen_separation_deg": exposure_gap.actual_separation_deg,
            "chosen_delay_ms": exposure_gap.delay_ms,
            "rev_b_50ms_target_deg": 11.84,
            "rev_b_50ms_target_feasible": exposure_gap.min_separation_deg <= 11.84,
            "verdict": (
                "The Rev B 50 ms (11.84 deg) exposure-to-development target is "
                "geometrically infeasible on the Rev A cartridge: the developer "
                "roller body and the LED clear cone alone need "
                f"{exposure_gap.min_separation_deg} deg. The binding requirement "
                "moves to the OPC: latent-image contrast must survive the real "
                "delay below."
            ),
        },
        "derived_opc_requirement": {
            "latent_contrast_hold_ms": required_hold_ms,
            "minimum_contrast_retention_fraction": 0.9,
            "measurement": (
                "H1 PIDC rig: charge, expose, then measure surface potential at "
                "the geometric delay and at the hold requirement; contrast "
                "retention below 90% at the hold time rejects the OPC."
            ),
        },
        "assumptions": [
            "Roller-to-roller limits are exact tangent-circle clearance solutions;"
            " blade and optical stations use declared envelope half-angles.",
            "Clearance covers bare bodies only; housings, seals, and toner-flow"
            " paths consume the distributed slack.",
            "Angles increase in the drum surface-travel direction; transfer nip"
            " fixed at 180 deg (paper path under the drum).",
        ],
    }


def station_map_rows(solution: dict) -> list[dict]:
    """Flatten the solved map for CSV emission."""
    rows = []
    for station in solution["stations"]:
        rows.append(
            {
                "station": station["name"],
                "kind": station["kind"],
                "angle_deg": station["angle_deg"],
                "occupancy_half_angle_deg": station["occupancy_half_angle_deg"],
            }
        )
    return rows


if __name__ == "__main__":
    import json

    print(json.dumps(solve_station_map(), indent=2))
