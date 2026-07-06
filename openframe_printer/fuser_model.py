from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class FuserModel:
    ambient_c: float = 25.0
    target_c: float = 178.0
    print_enable_c: float = 160.0
    warn_c: float = 195.0
    fault_c: float = 205.0
    heater_power_w: float = 800.0
    heat_capacity_j_per_c: float = 460.0
    thermal_resistance_c_per_w: float = 0.235
    controller_period_s: float = 0.1
    kp_w_per_c: float = 18.0
    ki_w_per_c_s: float = 0.060
    kd_w_s_per_c: float = 0.0


def simulate_fuser(model: FuserModel | None = None, duration_s: float = 180.0) -> dict:
    m = model or FuserModel()
    dt = m.controller_period_s
    steps = int(duration_s / dt) + 1
    temp = m.ambient_c
    integ = 0.0
    prev_error = m.target_c - temp
    rows = []
    first_print_enable_s = None
    faulted = False
    for i in range(steps):
        t = i * dt
        error = m.target_c - temp
        integ += error * dt
        deriv = (error - prev_error) / dt if i else 0.0
        raw_power = m.kp_w_per_c * error + m.ki_w_per_c_s * integ + m.kd_w_s_per_c * deriv
        power = max(0.0, min(m.heater_power_w, raw_power))
        if temp >= m.fault_c:
            power = 0.0
            faulted = True
        loss = (temp - m.ambient_c) / m.thermal_resistance_c_per_w
        temp += (power - loss) * dt / m.heat_capacity_j_per_c
        if first_print_enable_s is None and temp >= m.print_enable_c:
            first_print_enable_s = t
        rows.append({
            "time_s": round(t, 1),
            "surface_temp_c": round(temp, 3),
            "heater_power_w": round(power, 3),
            "state": "FAULT" if faulted else ("PRINT_READY" if temp >= m.print_enable_c else "WARMING"),
        })
        prev_error = error
    return {
        "model": asdict(m),
        "first_print_enable_s": first_print_enable_s,
        "final_temp_c": rows[-1]["surface_temp_c"],
        "max_temp_c": max(r["surface_temp_c"] for r in rows),
        "faulted": faulted,
        "rows": rows,
    }


if __name__ == "__main__":
    import json
    data = simulate_fuser()
    print(json.dumps({k: v for k, v in data.items() if k != "rows"}, indent=2))
