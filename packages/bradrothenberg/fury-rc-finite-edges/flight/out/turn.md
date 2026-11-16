# Turn performance: Fury model against an F-16C (estimates)

Level turns at maximum thrust. Both aircraft with half their internal fuel and two missiles. The Fury numbers come from the weight, thrust, lift and drag estimates in aircraft.md; the F-16 numbers from a public-data reference model. Read differences of 10 to 15 % as within the uncertainty.

| Aircraft | Weight [lb] | Wing loading [lb/ft2] | Thrust at sea level, Mach 0.5 [lbf] | Thrust / weight there |
|---|---:|---:|---:|---:|
| Fury model, 6,730 lb | 6,729 | 46.8 | 3,218 | 0.48 |
| Fury model, 5,000 lb | 5,000 | 34.8 | 3,218 | 0.64 |
| F-16C, afterburner | 23,580 | 78.6 | 29,054 | 1.23 |
| F-16C, military power | 23,580 | 78.6 | 14,764 | 0.63 |

## Sea level

### Tightest turn at each load factor (the lowest speed at which it is available)

| Load factor | Aircraft | Speed [kt true] | Mach | Radius [ft] | Rate [deg/s] | Excess power in the turn [ft/s] | Speed change [kt/s] | Excess power at 1 g on roll-out [ft/s] | Sustained at this g? |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 9 g | Fury model, 6,730 lb | 342 | 0.52 | 1,160 | 28.6 | -574 | -19.0 | +172 | no |
| 9 g | Fury model, 5,000 lb | 293 | 0.44 | 850 | 33.3 | -420 | -16.2 | +230 | no |
| 9 g | F-16C, afterburner | 419 | 0.63 | 1,740 | 23.3 | -384 | -10.3 | +796 | from 480 kt (radius 2,280 ft) |
| 9 g | F-16C, military power | 423 | 0.64 | 1,770 | 23.1 | -875 | -23.4 | +326 | no |
| 7 g | Fury model, 6,730 lb | 300 | 0.45 | 1,150 | 25.2 | -345 | -13.0 | +169 | no |
| 7 g | Fury model, 5,000 lb | 259 | 0.39 | 860 | 29.2 | -230 | -10.0 | +214 | from 341 kt (radius 1,480 ft) |
| 7 g | F-16C, afterburner | 328 | 0.50 | 1,380 | 23.1 | -482 | -16.6 | +623 | from 384 kt (radius 1,880 ft) |
| 7 g | F-16C, military power | 333 | 0.50 | 1,420 | 22.7 | -848 | -28.8 | +291 | no |
| 5 g | Fury model, 6,730 lb | 254 | 0.38 | 1,160 | 21.1 | -153 | -6.8 | +154 | from 324 kt (radius 1,900 ft) |
| 5 g | Fury model, 5,000 lb | 219 | 0.33 | 870 | 24.4 | -72 | -3.7 | +190 | from 245 kt (radius 1,080 ft) |
| 5 g | F-16C, afterburner | 270 | 0.41 | 1,320 | 19.8 | -170 | -7.1 | +504 | from 291 kt (radius 1,530 ft) |
| 5 g | F-16C, military power | 275 | 0.42 | 1,360 | 19.5 | -465 | -19.1 | +248 | from 410 kt (radius 3,040 ft) |
| 3 g | Fury model, 6,730 lb | 197 | 0.30 | 1,210 | 15.7 | -8 | -0.5 | +126 | from 202 kt (radius 1,270 ft) |
| 3 g | Fury model, 5,000 lb | 170 | 0.26 | 900 | 18.2 | +41 | +2.7 | +154 | from 172 kt (radius 930 ft) |
| 3 g | F-16C, afterburner | 211 | 0.32 | 1,390 | 14.7 | +129 | +6.9 | +380 | from 212 kt (radius 1,400 ft) |
| 3 g | F-16C, military power | 211 | 0.32 | 1,390 | 14.7 | -111 | -5.9 | +188 | from 238 kt (radius 1,780 ft) |

### Limits of the envelope

| Aircraft | Best instantaneous rate | Tightest instantaneous radius | Best sustained rate | Tightest sustained radius | Most g sustained | Top level speed [Mach] | Best 1 g excess power [ft/s] |
|---|---|---|---|---|---|---:|---:|
| Fury model, 6,730 lb | 28.5 deg/s at 341 kt, 9.0 g | 1,150 ft at 331 kt, 8.5 g | 16.7 deg/s at 301 kt, 4.7 g | 1,220 ft at 192 kt, 2.8 g | 5.9 g at 420 kt | 0.87 | 172 |
| Fury model, 5,000 lb | 33.2 deg/s at 294 kt, 9.0 g | 850 ft at 291 kt, 8.9 g | 22.7 deg/s at 298 kt, 6.3 g | 880 ft at 192 kt, 3.8 g | 7.9 g at 420 kt | 0.87 | 235 |
| F-16C, afterburner | 23.5 deg/s at 364 kt, 7.9 g | 1,310 ft at 275 kt, 5.2 g | 20.4 deg/s at 476 kt, 9.0 g | 1,340 ft at 241 kt, 4.0 g | 9.0 g at 480 kt | 0.95 | 1064 |
| F-16C, military power | 23.2 deg/s at 377 kt, 8.1 g | 1,340 ft at 245 kt, 4.1 g | 13.7 deg/s at 318 kt, 4.1 g | 1,490 ft at 179 kt, 2.1 g | 6.1 g at 539 kt | 0.95 | 327 |

### A 180 deg turn from Mach 0.70 at maximum thrust (point mass, constant height)

The load factor asked for is held while the aircraft has it; when the speed falls below what the lift limit needs, the turn goes on at the most it has.

| Load factor asked | Aircraft | Time [s] | Turn diameter [ft] | Entry [kt] | Exit [kt] | g at the exit | Excess power at 1 g on roll-out [ft/s] | Time to regain the entry speed [s] |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 9 g | Fury model, 6,730 lb | 8.0 | 3,750 | 463 | 403 | 9.0 | +161 | 16 |
| 9 g | Fury model, 5,000 lb | 8.4 | 4,120 | 463 | 449 | 9.0 | +190 | 3 |
| 9 g | F-16C, afterburner | 8.3 | 4,050 | 463 | 435 | 9.0 | +823 | 1 |
| 9 g | F-16C, military power | 8.1 | 3,190 | 463 | 272 | 4.9 | +245 | 21 |
| 7 g | Fury model, 6,730 lb | 10.8 | 5,260 | 463 | 444 | 7.0 | +142 | 6 |
| 7 g | Fury model, 5,000 lb | 11.1 | 5,570 | 463 | 471 | 7.0 | +170 | 0 |
| 7 g | F-16C, afterburner | 12.4 | 6,930 | 463 | 601 | 7.0 | +1054 | 0 |
| 7 g | F-16C, military power | 10.1 | 4,660 | 463 | 380 | 7.0 | +316 | 10 |
| 5 g | Fury model, 6,730 lb | 15.8 | 7,940 | 463 | 474 | 5.0 | +122 | 0 |
| 5 g | Fury model, 5,000 lb | 16.2 | 8,370 | 463 | 497 | 5.0 | +140 | 0 |
| 5 g | F-16C, afterburner | 19.5 | 12,690 | 463 | 628 | 5.0 | +990 | 0 |
| 5 g | F-16C, military power | 16.1 | 8,310 | 463 | 498 | 5.0 | +317 | 0 |
| 3 g | Fury model, 6,730 lb | 28.6 | 15,120 | 463 | 514 | 3.0 | +86 | 0 |
| 3 g | Fury model, 5,000 lb | 29.4 | 15,960 | 463 | 535 | 3.0 | +86 | 0 |
| 3 g | F-16C, afterburner | 35.3 | 24,030 | 463 | 628 | 3.0 | +990 | 0 |
| 3 g | F-16C, military power | 32.1 | 19,210 | 463 | 620 | 3.0 | +93 | 0 |

## 15,000 ft

### Tightest turn at each load factor (the lowest speed at which it is available)

| Load factor | Aircraft | Speed [kt true] | Mach | Radius [ft] | Rate [deg/s] | Excess power in the turn [ft/s] | Speed change [kt/s] | Excess power at 1 g on roll-out [ft/s] | Sustained at this g? |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 9 g | Fury model, 6,730 lb | 466 | 0.74 | 2,150 | 21.0 | -729 | -17.7 | +85 | no |
| 9 g | Fury model, 5,000 lb | 382 | 0.61 | 1,440 | 25.6 | -644 | -19.0 | +129 | no |
| 9 g | F-16C, afterburner | 512 | 0.82 | 2,590 | 19.1 | -948 | -20.9 | +714 | no |
| 9 g | F-16C, military power | 515 | 0.82 | 2,630 | 19.0 | -1443 | -31.6 | +249 | no |
| 7 g | Fury model, 6,730 lb | 393 | 0.63 | 1,970 | 19.3 | -513 | -14.8 | +92 | no |
| 7 g | Fury model, 5,000 lb | 328 | 0.52 | 1,380 | 23.1 | -425 | -14.6 | +127 | no |
| 7 g | F-16C, afterburner | 408 | 0.65 | 2,130 | 18.5 | -988 | -27.3 | +540 | from 545 kt (radius 3,800 ft) |
| 7 g | F-16C, military power | 413 | 0.66 | 2,180 | 18.3 | -1349 | -36.9 | +224 | no |
| 5 g | Fury model, 6,730 lb | 321 | 0.51 | 1,860 | 16.7 | -294 | -10.4 | +89 | no |
| 5 g | Fury model, 5,000 lb | 276 | 0.44 | 1,370 | 19.4 | -217 | -8.9 | +117 | from 442 kt (radius 3,530 ft) |
| 5 g | F-16C, afterburner | 339 | 0.54 | 2,070 | 15.8 | -506 | -16.9 | +423 | from 410 kt (radius 3,040 ft) |
| 5 g | F-16C, military power | 344 | 0.55 | 2,140 | 15.6 | -774 | -25.4 | +187 | no |
| 3 g | Fury model, 6,730 lb | 248 | 0.40 | 1,920 | 12.5 | -97 | -4.4 | +75 | from 323 kt (radius 3,260 ft) |
| 3 g | Fury model, 5,000 lb | 214 | 0.34 | 1,430 | 14.5 | -50 | -2.7 | +97 | from 244 kt (radius 1,870 ft) |
| 3 g | F-16C, afterburner | 263 | 0.42 | 2,170 | 11.7 | -69 | -3.0 | +301 | from 276 kt (radius 2,380 ft) |
| 3 g | F-16C, military power | 263 | 0.42 | 2,170 | 11.7 | -288 | -12.4 | +132 | from 366 kt (radius 4,200 ft) |

### Limits of the envelope

| Aircraft | Best instantaneous rate | Tightest instantaneous radius | Best sustained rate | Tightest sustained radius | Most g sustained | Top level speed [Mach] | Best 1 g excess power [ft/s] |
|---|---|---|---|---|---|---:|---:|
| Fury model, 6,730 lb | 21.0 deg/s at 464 kt, 9.0 g | 1,850 ft at 313 kt, 4.8 g | 9.6 deg/s at 326 kt, 3.0 g | 2,330 ft at 185 kt, 1.6 g | 3.8 g at 476 kt | 0.91 | 93 |
| Fury model, 5,000 lb | 25.6 deg/s at 382 kt, 9.0 g | 1,360 ft at 313 kt, 6.5 g | 13.3 deg/s at 313 kt, 3.9 g | 1,530 ft at 182 kt, 2.2 g | 5.0 g at 476 kt | 0.92 | 129 |
| F-16C, afterburner | 19.1 deg/s at 489 kt, 8.6 g | 2,060 ft at 319 kt, 4.5 g | 13.9 deg/s at 542 kt, 7.0 g | 2,230 ft at 244 kt, 2.6 g | 7.3 g at 589 kt | 0.95 | 778 |
| F-16C, military power | 19.0 deg/s at 501 kt, 8.8 g | 2,130 ft at 294 kt, 3.7 g | 8.5 deg/s at 501 kt, 4.0 g | 2,990 ft at 197 kt, 1.5 g | 4.2 g at 548 kt | 0.95 | 251 |

### A 180 deg turn from Mach 0.80 at maximum thrust (point mass, constant height)

The load factor asked for is held while the aircraft has it; when the speed falls below what the lift limit needs, the turn goes on at the most it has.

| Load factor asked | Aircraft | Time [s] | Turn diameter [ft] | Entry [kt] | Exit [kt] | g at the exit | Excess power at 1 g on roll-out [ft/s] | Time to regain the entry speed [s] |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 9 g | Fury model, 6,730 lb | 9.1 | 4,130 | 501 | 360 | 6.1 | +92 | 62 |
| 9 g | Fury model, 5,000 lb | 8.6 | 4,270 | 501 | 421 | 9.0 | +127 | 28 |
| 9 g | F-16C, afterburner | 10.7 | 4,290 | 501 | 292 | 3.7 | +345 | 14 |
| 9 g | F-16C, military power | 12.5 | 4,340 | 501 | 232 | 2.3 | +108 | 45 |
| 7 g | Fury model, 6,730 lb | 10.9 | 5,400 | 501 | 408 | 7.0 | +92 | 44 |
| 7 g | Fury model, 5,000 lb | 11.5 | 6,000 | 501 | 467 | 7.0 | +117 | 13 |
| 7 g | F-16C, afterburner | 11.0 | 5,510 | 501 | 378 | 6.1 | +487 | 8 |
| 7 g | F-16C, military power | 12.1 | 4,560 | 501 | 248 | 2.7 | +121 | 42 |
| 5 g | Fury model, 6,730 lb | 16.4 | 8,570 | 501 | 472 | 5.0 | +84 | 16 |
| 5 g | Fury model, 5,000 lb | 16.9 | 9,080 | 501 | 501 | 5.0 | +107 | 0 |
| 5 g | F-16C, afterburner | 18.9 | 11,620 | 501 | 595 | 5.0 | +757 | 0 |
| 5 g | F-16C, military power | 15.6 | 7,760 | 501 | 414 | 5.0 | +225 | 15 |
| 3 g | Fury model, 6,730 lb | 29.8 | 16,320 | 501 | 519 | 3.0 | +72 | 0 |
| 3 g | Fury model, 5,000 lb | 30.5 | 17,150 | 501 | 542 | 3.0 | +84 | 0 |
| 3 g | F-16C, afterburner | 34.1 | 21,900 | 501 | 595 | 3.0 | +757 | 0 |
| 3 g | F-16C, military power | 31.7 | 18,550 | 501 | 584 | 3.0 | +167 | 0 |

## How far the Fury answers move with the assumptions (sea level, 6,730 lb)

| Case | 9 g: lowest speed [kt] | 9 g: radius [ft] | 9 g: excess power [ft/s] | Most g sustained | 5 g sustained? |
|---|---:|---:|---:|---:|---|
| as stated | 342 | 1,160 | -574 | 5.9 | yes |
| usable CLmax + 0.15 | 319 | 1,010 | -633 | 5.9 | yes |
| usable CLmax - 0.15 | 374 | 1,380 | -504 | 5.8 | yes |
| thrust + 15 % | 342 | 1,160 | -530 | 6.8 | yes |
| thrust - 15 % | 342 | 1,150 | -618 | 5.0 | no |
| drag + 15 % | 342 | 1,160 | -700 | 5.1 | yes |
| drag - 15 % | 342 | 1,160 | -448 | 7.0 | yes |
| drag as the flow solution gives it | 342 | 1,160 | -897 | 5.3 | yes |