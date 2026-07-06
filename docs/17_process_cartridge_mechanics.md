# 17. Process cartridge mechanics

The OpenFrame process cartridge is a new module. It is not authenticated by a chip. It can expose a resistor ID for capacity or cartridge family, but the printer must not refuse to print based on vendor identity.

## Cartridge envelope

| Dimension | Rev A target |
|---|---:|
| Cartridge width | 255 mm |
| Cartridge depth | 92 mm |
| Cartridge height | 86 mm |
| OPC drum diameter | 30.0 mm |
| Developer roller diameter | 16.0 mm |
| Primary charge roller diameter | 10.0 mm |
| Waste toner channel height | 12 mm |
| Toner hopper starting capacity | 80 g |

## Internal components

| Component | Requirement |
|---|---|
| OPC drum | 30 mm diameter organic photoconductor, replaceable as cartridge submodule |
| Primary charge roller | Conductive rubber roller, spring loaded, service-cleanable |
| Developer roller | Conductive/magnetic roller depending on toner system selected |
| Doctor blade | Adjustable mount, 80-180 µm setup sweep |
| Toner hopper | Screwless service hatch with gasket; no DRM lockout |
| Agitator | Low-speed paddle or auger, keyed but not authentication-locked |
| Waste toner path | Passive scraper into sealed waste channel |
| Spring contacts | PCR, developer, and ID resistor contacts on serviceable contact block |

## Initial toner target

| Parameter | Rev A target |
|---|---:|
| Toner color | black |
| Toner particle size | 6-8 µm |
| Dense black laydown | 0.55 mg/cm² |
| Office page coverage assumption | 5% |
| Calculated toner per 5% Letter page | 0.0166 g developed to paper |
| Naive 80 g upper bound at 5% | about 4800 pages, explicitly not rated |
| Loss-adjusted 80 g rating target | about 4000 pages |
| Waste cavity requirement | at least 28 cm³ with margin |

The calculated yield is a mass-balance estimate, not a marketing claim. The active consumables number comes from `out/v2_toner_mass_balance.json` and `out/v2_toner_artifact_consistency.json`, not this prose table. It includes transfer loss and hopper residual; calibration pages, cleaning cycles, density choices, and third-party toner behavior must be reported as uncertainty rather than used as lockout logic.

## Contact layout

| Contact | Signal | Range |
|---|---|---:|
| C1 | PCR_HV | Rev D Option A: −900 to −1400 V DC; Option B: −450 to −750 V DC plus 1.7 kVpp AC |
| C2 | DEV_ROLLER_BIAS | −150 to −500 V, nominal −320 V |
| C3 | DEV_MON / CART_ID_RES mux | 0 to 3.3 V sense; optional Rev D nanoamp current-sense mode |
| C4 | CART_GND | 0 V guarded return |

The transfer roller is separate from the process cartridge so the user does not replace it every time toner is replaced. The old Rev A −720 V PCR assumption is retired; do not use the historical Rev A connector range for an active cartridge quote.

## Lab-only developer research contacts

The production cartridge may keep the developer subsystem simple. The Rev B lab cartridge should expose optional developer sub-bias contacts so toner mass and toner charge can be studied instead of hidden. Rev D adds an optional measurement path for H8: the developer roller as an in-situ electrostatic probe. See `hardware/ofp_m1_revB_lab_developer_bias_options.csv` and `out/v2_dev_probe_budget.json`.

| Contact | Signal | Initial lab range | Purpose |
|---|---|---:|---|
| L1 | DEV_BLADE_BIAS | -300 to -900 V | regulating blade charge-shaping rail |
| L2 | TONER_SUPPLY_BIAS | -500 to -800 V | toner supply roller rail |
| L3 | DEV_GUARD_RETURN | 0 V | guarded return/reference for measurements |
| L4 | DEV_MON_TIA | nanoamp signal path | optional Rev D current-sense path for developer-probe experiments |

These are lab-only rails until density, fog, and q/m experiments prove they are worth the extra contacts and safety burden. They must not become consumable authentication or lockout contacts.

## Mechanical adjustments built into Rev A

- Developer-to-drum center distance: ±0.5 mm.
- Doctor blade gap: 80-180 µm sweep.
- Charge roller spring force: 1.5-3.0 N per side setup range.
- Cartridge latch repeatability target: ±0.15 mm at drum axis.
- Drum axial float target: less than 0.25 mm.

## Failure modes to design around

| Failure | Design response |
|---|---|
| Toner leak | Labyrinth seals plus replaceable gasket strips |
| Drum scratch | Drum is visible and replaceable without replacing whole printer |
| Weak density | User/service menu exposes density calibration values |
| Background fog | Charge/developer/exposure sweeps are documented |
| Waste overflow | Mechanical counter plus visible waste channel inspection window |
| Bad contact | Spring contact block is replaceable separately |
