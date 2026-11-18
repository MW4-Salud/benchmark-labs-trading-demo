# Benchmark Labs Trading Dashboard

**Live demo: [benchmarklabstrading.com](https://www.benchmarklabstrading.com/)**

A weather intelligence site for U.S. energy traders. It shows how point-specific weather forecasts for wind, solar and gas plants can help a trading desk see generation swings before they show up in the market.

> The source code for this project is private. This repo is a public overview for anyone who wants to see what it does and how it was built. I'm happy to walk through the code in an interview.

## What it does

### Interactive map
- National map of weather stations and power plants
- Filter stations by ownership (private or public/government) and status (active or inactive)
- Filter plants by type: wind, solar, natural gas, nuclear, coal and battery storage
- Click a plant to draw radius rings (10, 25, 50 and 100 km) and count the stations around it
- Search for a plant or station

### Forecast explorer
- Compares NOAA and two private weather data providers against real station observations
- Sites, variables (temperature, humidity, wind speed, wind direction) and units (°F or °C) can be switched
- Summary cards show the most accurate provider (RMSE), the spread between best and worst, and bias
- Time series chart with a zoom slider and a hover readout, with station data shown as the "truth" line

### Trading desk overview
- Explains how asset-level forecasts, model benchmarking (GFS, ECMWF, ICON, GEM) and API delivery fit into a trader's workflow
- Demo request call to action

## Tech stack

| Area | Tools |
|------|-------|
| Framework | Next.js, React |
| Styling | Tailwind CSS, Framer Motion |
| Maps | MapLibre GL, react-map-gl |
| Charts | Recharts |
| State | Zustand |
| Hosting | Vercel |
| Data prep | Python (cleaning and geocoding station and power plant data) |

## Code samples

The site's code is private, but these two Python files are taken from my station data pipeline. They only need the standard library.

| File | What it does |
|------|--------------|
| `weather_calcs.py` | Turns raw station readings into trading-relevant numbers: dew point, heat index, wind chill, wet bulb, air density, wind power density, hub-height wind, clear sky index, fire weather index and heating/cooling degree days |
| `dedup_stations.py` | Removes duplicate stations that appear in more than one data source, using a grid so it stays fast with thousands of stations |

Try them:

```
python weather_calcs.py
python dedup_stations.py
```

## What I worked on

- Built the site from scratch
- Designed and built the interactive weather station and power plant map
- Built the forecast explorer and provider comparison charts
- Fixed a geocoding bug that placed Texas natural gas plants in the wrong location
- Ongoing UI improvements

---

© 2026 Benchmark Labs. All rights reserved. This repo does not include the site's code, data or API keys.
