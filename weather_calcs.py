# weather_calcs.py
# Derived weather variables I calculate for each weather station.
# These turn raw readings (temperature, humidity, wind, sun) into numbers
# that matter for energy trading, like wind power and heating/cooling demand.
#
# Inputs are in US units (F, mph, inHg, W/m2) because that's what the
# station feeds use.

import math
from datetime import datetime, timezone


def f_to_c(temp_f):
    return (temp_f - 32) * 5 / 9


def dew_point(temp_f, rh):
    # Magnus formula
    t = f_to_c(temp_f)
    rh = max(1, min(100, rh))
    a = math.log(rh / 100) + (17.625 * t) / (243.04 + t)
    dew_c = 243.04 * a / (17.625 - a)
    return round(dew_c * 9 / 5 + 32, 2)


def heat_index(temp_f, rh):
    # NWS heat index, only used above 80F
    if temp_f < 80:
        return None
    t = temp_f
    r = rh
    hi = (-42.379 + 2.04901523 * t + 10.14333127 * r
          - 0.22475541 * t * r - 0.00683783 * t * t
          - 0.05481717 * r * r + 0.00122874 * t * t * r
          + 0.00085282 * t * r * r - 0.00000199 * t * t * r * r)
    return round(hi, 2)


def wind_chill(temp_f, wind_mph):
    # NWS wind chill, only used at 50F or colder with some wind
    if temp_f > 50 or wind_mph < 3:
        return None
    v = wind_mph ** 0.16
    return round(35.74 + 0.6215 * temp_f - 35.75 * v + 0.4275 * temp_f * v, 2)


def vapor_pressure_deficit(temp_f, rh):
    # in kPa
    t = f_to_c(temp_f)
    saturation = 0.6108 * math.exp(17.27 * t / (t + 237.3))
    return round(saturation * (1 - rh / 100), 4)


def wet_bulb(temp_f, rh):
    # Stull (2011) approximation
    t = f_to_c(temp_f)
    tw = (t * math.atan(0.151977 * (rh + 8.313659) ** 0.5)
          + math.atan(t + rh) - math.atan(rh - 1.676331)
          + 0.00391838 * rh ** 1.5 * math.atan(0.023101 * rh)
          - 4.686035)
    return round(tw * 9 / 5 + 32, 2)


def air_density(temp_f, pressure_inhg):
    # kg/m3, from the ideal gas law
    pressure_pa = pressure_inhg * 3386.39
    temp_k = f_to_c(temp_f) + 273.15
    return round(pressure_pa / (287.05 * temp_k), 4)


def wind_power_density(wind_mph, temp_f=None, pressure_inhg=None):
    # W/m2 = 0.5 * air density * speed^3
    if temp_f is not None and pressure_inhg is not None:
        rho = air_density(temp_f, pressure_inhg)
    else:
        rho = 1.225  # standard sea level air
    speed_ms = wind_mph * 0.44704
    return round(0.5 * rho * speed_ms ** 3, 2)


def hub_height_wind(wind_mph, hub_m=80, sensor_m=10):
    # power law to estimate wind at turbine height from a 10 m sensor
    return round(wind_mph * (hub_m / sensor_m) ** 0.143, 2)


def gust_risk(gust_mph):
    # 0 = calm, 4 = severe
    if gust_mph < 20:
        return 0
    elif gust_mph < 35:
        return 1
    elif gust_mph < 50:
        return 2
    elif gust_mph < 65:
        return 3
    return 4


def clear_sky_index(solar_wm2, lat, day_of_year, hour_utc):
    # measured sun divided by what a clear sky would give at that moment
    decl = math.radians(23.45 * math.sin(math.radians(360 / 365 * (day_of_year - 81))))
    lat_r = math.radians(lat)
    hour_angle = math.radians(15 * (hour_utc - 12))
    cos_zenith = (math.sin(lat_r) * math.sin(decl)
                  + math.cos(lat_r) * math.cos(decl) * math.cos(hour_angle))
    if cos_zenith <= 0:
        return None  # sun is down

    top_of_atmosphere = 1361 * (1 + 0.033 * math.cos(math.radians(360 / 365 * day_of_year)))
    clear_sky = top_of_atmosphere * cos_zenith * 0.75
    if clear_sky < 10:
        return None
    return round(min(solar_wm2 / clear_sky, 1.5), 4)


def fire_weather_index(temp_f, rh, wind_mph, precip_24h=0):
    # simple 0-100 score: dry, hot and windy = higher risk
    if precip_24h > 0.25:
        return max(0, round(10 - precip_24h * 20, 1))
    dryness = (100 - rh) / 100
    heat = max(0, (temp_f - 50) / 60)
    wind = min(1.0, wind_mph / 30)
    score = (dryness * 0.45 + heat * 0.35 + wind * 0.20) * 100
    return round(max(0, min(100, score)), 1)


def heating_degree_days(temp_f, base=65):
    return round(max(0, base - temp_f), 2)


def cooling_degree_days(temp_f, base=65):
    return round(max(0, temp_f - base), 2)


def derived_variables(obs, lat):
    # obs is one station reading, for example:
    # {"temp_f": 92, "rh": 40, "wind_mph": 14, "wind_gust_mph": 25,
    #  "solar_wm2": 850, "pressure_inhg": 29.9, "precip_24h": 0}
    now = datetime.now(timezone.utc)
    day = now.timetuple().tm_yday
    hour = now.hour + now.minute / 60

    temp = obs.get("temp_f")
    rh = obs.get("rh")
    wind = obs.get("wind_mph")
    gust = obs.get("wind_gust_mph")
    solar = obs.get("solar_wm2")
    pressure = obs.get("pressure_inhg")
    precip = obs.get("precip_24h", 0)

    result = {}

    if temp is not None and rh is not None:
        result["dew_point_f"] = dew_point(temp, rh)
        result["heat_index_f"] = heat_index(temp, rh)
        result["vpd_kpa"] = vapor_pressure_deficit(temp, rh)
        result["wet_bulb_f"] = wet_bulb(temp, rh)

    if temp is not None:
        result["hdd"] = heating_degree_days(temp)
        result["cdd"] = cooling_degree_days(temp)

    if temp is not None and pressure is not None:
        result["air_density_kgm3"] = air_density(temp, pressure)

    if wind is not None:
        result["wind_power_density_wm2"] = wind_power_density(wind, temp, pressure)
        result["hub_wind_80m_mph"] = hub_height_wind(wind)
        if temp is not None:
            result["wind_chill_f"] = wind_chill(temp, wind)
        if temp is not None and rh is not None:
            result["fire_weather_index"] = fire_weather_index(temp, rh, wind, precip)

    if gust is not None:
        result["gust_risk"] = gust_risk(gust)

    if solar is not None:
        result["clear_sky_index"] = clear_sky_index(solar, lat, day, hour)

    return result


if __name__ == "__main__":
    # example reading (made up numbers)
    reading = {"temp_f": 94, "rh": 38, "wind_mph": 16, "wind_gust_mph": 27,
               "solar_wm2": 820, "pressure_inhg": 29.92, "precip_24h": 0}
    for name, value in derived_variables(reading, lat=31.0).items():
        print(name, "=", value)
