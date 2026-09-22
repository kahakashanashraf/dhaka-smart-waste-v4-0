#!/usr/bin/env python3
"""Generate Dhaka Smart Waste Synthetic IoT Dataset V4.0 — One-Year 2025.

V4.0 is a one-year, literature-calibrated, context-aware urban digital-twin dataset with:
- 5,000 persistent synthetic bins across five Dhaka neighborhoods
- the full 2025 calendar (365 days x 24 hours = 43,800,000 hourly observations)
- Bangladesh 2025 public-holiday, Ramadan, school-break, and special working-day logic
- monthly Dhaka temperature/rainfall seasonality calibrated to published climate normals
- land-use subtypes (fish/vegetable/general markets, school/college,
  parks/recreation, restaurants, garment factories, etc.)
- density/catchment-driven generation rather than a simplistic slum multiplier
- institution open/closed behavior and holiday reductions
- land-use-specific hourly activity patterns
- dynamic 8-part waste composition that sums to 100%
- informal recyclable recovery before waste enters the bin
- separate waste mass, bulk density, volume, and sensor fill level
- road accessibility and collection-service effects
- Friday prayer and Eid-ul-Adha scenario flags/multipliers
- weather variation, battery depletion, packet loss, and sensor anomalies

IMPORTANT: This is synthetic, scenario-based data. Numerical multipliers are
simulation parameters intended to create plausible, inspectable relationships;
they are not direct field measurements of Dhaka bins.
"""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import json, math
import numpy as np
import h5py

SEED = 20260902
RNG = np.random.default_rng(SEED)
OUT_DIR = Path(__file__).resolve().parent
OUT_H5 = OUT_DIR / 'dhaka_smart_waste_v4_0_2025.h5'

N_BINS = 5000
N_DAYS = 365
HOURS_PER_DAY = 24
N_HOURS = N_DAYS * HOURS_PER_DAY
N_ROWS = N_BINS * N_HOURS
BD_TZ = timezone(timedelta(hours=6))
START_DATE = datetime(2025, 1, 1, 0, 0, 0, tzinfo=BD_TZ)
EID_DAY = datetime(2025, 6, 7, tzinfo=BD_TZ).date()
EID_PERIOD_START = datetime(2025, 6, 5, tzinfo=BD_TZ).date()
EID_PERIOD_END = datetime(2025, 6, 12, tzinfo=BD_TZ).date()
EID_FITR_DAY = datetime(2025, 3, 31, tzinfo=BD_TZ).date()
EID_FITR_START = datetime(2025, 3, 29, tzinfo=BD_TZ).date()
EID_FITR_END = datetime(2025, 4, 3, tzinfo=BD_TZ).date()
RAMADAN_START = datetime(2025, 3, 2, tzinfo=BD_TZ).date()
RAMADAN_END = datetime(2025, 3, 30, tzinfo=BD_TZ).date()
SCHOOL_RAMADAN_BREAK_START = datetime(2025, 3, 2, tzinfo=BD_TZ).date()
SCHOOL_RAMADAN_BREAK_END = datetime(2025, 4, 7, tzinfo=BD_TZ).date()
SCHOOL_SUMMER_EID_BREAK_START = datetime(2025, 6, 1, tzinfo=BD_TZ).date()
SCHOOL_SUMMER_EID_BREAK_END = datetime(2025, 6, 19, tzinfo=BD_TZ).date()
SCHOOL_DURGA_BREAK_START = datetime(2025, 9, 28, tzinfo=BD_TZ).date()
SCHOOL_DURGA_BREAK_END = datetime(2025, 10, 7, tzinfo=BD_TZ).date()
SPECIAL_WORKING_DAYS = {datetime(2025,5,17,tzinfo=BD_TZ).date(), datetime(2025,5,24,tzinfo=BD_TZ).date()}

AREA_COUNTS = {
    'Residential': 1300,
    'Commercial': 700,
    'Slum': 800,
    'Market': 700,
    'Office': 600,
    'Education': 350,
    'Garments': 200,
    'Recreation': 350,
}
assert sum(AREA_COUNTS.values()) == N_BINS

SUBTYPE_RULES = {
    'Residential': (['Apartment Residential','Dense Residential'], [0.55,0.45]),
    'Commercial': (['Shopping','Restaurant/Food Zone','Mixed Commercial'], [0.35,0.45,0.20]),
    'Slum': (['Informal Settlement'], [1.0]),
    'Market': (['Fish Market','Vegetable Market','General Market'], [0.35,0.35,0.30]),
    'Office': (['Government Office','Private Office'], [0.45,0.55]),
    'Education': (['School','College/University'], [0.60,0.40]),
    'Garments': (['Garment Factory'], [1.0]),
    'Recreation': (['Park','Playground','Entertainment Center'], [0.50,0.25,0.25]),
}

NEIGHBORHOOD_COUNTS = {
    'Mirpur': 1046,
    'Gulshan/Banani': 1023,
    'Dhanmondi': 997,
    'Old Dhaka': 972,
    'Motijheel': 962,
}
NEIGHBORHOOD_CENTERS = {
    'Mirpur': (23.8067, 90.3687),
    'Gulshan/Banani': (23.7930, 90.4145),
    'Dhanmondi': (23.7465, 90.3760),
    'Old Dhaka': (23.7104, 90.4074),
    'Motijheel': (23.7334, 90.4172),
}

# Volume choices are synthetic container sizes in litres.
AREA_VOLUME_CHOICES = {
    'Residential': ([240, 360, 660], [0.25,0.50,0.25]),
    'Commercial': ([360, 660, 1100], [0.15,0.55,0.30]),
    'Slum': ([240, 360, 660], [0.40,0.45,0.15]),
    'Market': ([660, 1100], [0.40,0.60]),
    'Office': ([240, 360, 660], [0.15,0.55,0.30]),
    'Education': ([240, 360, 660], [0.20,0.55,0.25]),
    'Garments': ([660, 1100], [0.30,0.70]),
    'Recreation': ([240, 360, 660], [0.30,0.50,0.20]),
}

AREA_PLACEMENT = {
    'Residential': ['Roadside','Indoor'],
    'Commercial': ['Roadside','Near market','Office'],
    'Slum': ['Roadside','Near market'],
    'Market': ['Near market','Roadside'],
    'Office': ['Office','Roadside'],
    'Education': ['School','Roadside'],
    'Garments': ['Office','Roadside'],
    'Recreation': ['Roadside','Park'],
}
AREA_BUSINESS = {
    'Residential': ['None','Restaurant','Market'],
    'Commercial': ['Office','Restaurant','Market','Shopping'],
    'Slum': ['Market','Restaurant','None'],
    'Market': ['Market','Restaurant'],
    'Office': ['Office','Restaurant'],
    'Education': ['None','Market','Restaurant'],
    'Garments': ['Garments','Market'],
    'Recreation': ['Restaurant','None','Market'],
}
AREA_POI = {
    'Residential': (['None','Mosque','School','Market'], [0.48,0.24,0.13,0.15]),
    'Commercial': (['None','Mosque','Market','Office'], [0.42,0.18,0.25,0.15]),
    'Slum': (['None','Mosque','Market'], [0.35,0.34,0.31]),
    'Market': (['Market','Mosque','None'], [0.53,0.27,0.20]),
    'Office': (['Office','Mosque','None'], [0.58,0.12,0.30]),
    'Education': (['School','Mosque','None'], [0.70,0.10,0.20]),
    'Garments': (['Office','Mosque','Market'], [0.43,0.12,0.45]),
    'Recreation': (['Park','Mosque','None'], [0.62,0.12,0.26]),
}

AREA_CODE = {k:i for i,k in enumerate(AREA_COUNTS)}
SUBTYPE_CATS = sorted({s for vals,_ in SUBTYPE_RULES.values() for s in vals})
SUBTYPE_CODE = {k:i for i,k in enumerate(SUBTYPE_CATS)}
DENSITY_CATS = ['Low','Medium','High']
INCOME_CATS = ['NA','Low','Lower-middle','Middle','Upper-middle','High']
ACCESS_CATS = ['Easy','Moderate','Difficult']
SERVICE_CATS = ['Good','Moderate','Limited']
PLACEMENT_CATS = sorted({x for vals in AREA_PLACEMENT.values() for x in vals})
BUSINESS_CATS = sorted({x for vals in AREA_BUSINESS.values() for x in vals})
POI_CATS = sorted({x for vals,_ in AREA_POI.values() for x in vals})

EVENT_CATS = ['Normal','Weekend','Public Holiday','Eid-ul-Fitr Holiday','Eid-ul-Fitr','Eid-ul-Adha Holiday','Eid-ul-Adha','Durga Puja Holiday']
WEATHER_CATS = ['Sunny','Cloudy','Rainy','Storm']
TIME_SLOT_CATS = ['Night','Morning','Afternoon','Evening']
SEASON_CATS = ['Winter','Pre-monsoon','Monsoon','Post-monsoon']
HOLIDAY_CATS = ['None','Shab-e-Barat','Language Martyrs Day','Independence Day','Shab-e-Qadr/Jumuatul-Wida','Eid-ul-Fitr','Bangla New Year','May Day','Buddha Purnima','Eid-ul-Adha','Ashura','Janmashtami','Eid-e-Milad-un-Nabi','Durga Puja','Victory Day','Christmas Day']
INSTITUTION_STATUS_CATS = ['Not applicable','Open','Closed']
SENSOR_ERROR_CATS = ['none','saturation_low','saturation_high','spike']
COMPOSITION_CATS = [
    'organic_food','fish_meat','animal_residue','plastic',
    'paper_cardboard','textile','metal_glass','green_other'
]
DOMINANT_WASTE_CATS = COMPOSITION_CATS.copy()
# Approximate synthetic bulk densities (kg/m^3) used only by the simulator.
COMP_DENSITY = np.array([260, 520, 560, 70, 90, 110, 900, 180], dtype=np.float32)
RECYCLABLE_IDX = np.array([3,4,5,6], dtype=np.int64)

# Base composition by land-use subtype. Each row is normalized below.
BASE_COMP = {
    'Apartment Residential': [0.45,0.05,0.01,0.18,0.12,0.05,0.04,0.10],
    'Dense Residential':     [0.50,0.05,0.01,0.16,0.10,0.05,0.03,0.10],
    'Informal Settlement':   [0.55,0.06,0.01,0.12,0.08,0.06,0.03,0.09],
    'Fish Market':           [0.15,0.60,0.01,0.10,0.03,0.01,0.02,0.08],
    'Vegetable Market':      [0.60,0.02,0.01,0.12,0.04,0.01,0.02,0.18],
    'General Market':        [0.35,0.05,0.01,0.20,0.12,0.06,0.07,0.14],
    'Shopping':              [0.20,0.02,0.01,0.30,0.20,0.08,0.08,0.11],
    'Restaurant/Food Zone':  [0.55,0.08,0.01,0.18,0.08,0.02,0.03,0.05],
    'Mixed Commercial':      [0.30,0.03,0.01,0.25,0.17,0.08,0.06,0.10],
    'Government Office':     [0.22,0.02,0.01,0.18,0.30,0.05,0.05,0.17],
    'Private Office':        [0.22,0.02,0.01,0.18,0.30,0.05,0.05,0.17],
    'School':                [0.25,0.02,0.01,0.20,0.32,0.03,0.03,0.14],
    'College/University':    [0.30,0.02,0.01,0.22,0.25,0.04,0.04,0.12],
    'Garment Factory':       [0.10,0.01,0.01,0.12,0.08,0.58,0.04,0.06],
    'Park':                  [0.30,0.01,0.01,0.35,0.15,0.02,0.04,0.12],
    'Playground':            [0.25,0.01,0.01,0.38,0.18,0.02,0.04,0.11],
    'Entertainment Center':  [0.28,0.02,0.01,0.40,0.15,0.03,0.04,0.07],
}
for k,v in BASE_COMP.items():
    a = np.array(v, dtype=np.float32)
    BASE_COMP[k] = a / a.sum()

# Non-residential baseline kg/h at an equivalent catchment load of 100.
SUBTYPE_BASE_KGPH = {
    'Fish Market': 1.40, 'Vegetable Market': 1.20, 'General Market': 0.92,
    'Shopping': 0.78, 'Restaurant/Food Zone': 1.12, 'Mixed Commercial': 0.86,
    'Government Office': 0.52, 'Private Office': 0.58,
    'School': 0.50, 'College/University': 0.66,
    'Garment Factory': 1.00,
    'Park': 0.44, 'Playground': 0.36, 'Entertainment Center': 0.76,
}

DENSITY_MULT = {'Low':0.85,'Medium':1.00,'High':1.15}
PER_CAPITA = {'Low':0.270,'Lower-middle':0.305,'Middle':0.371,'Upper-middle':0.389,'High':0.504}


def exact_shuffled_labels(counts):
    arr = np.concatenate([np.repeat(k,v) for k,v in counts.items()])
    RNG.shuffle(arr)
    return arr

area = exact_shuffled_labels(AREA_COUNTS)
neighborhood = exact_shuffled_labels(NEIGHBORHOOD_COUNTS)
subtype = np.empty(N_BINS, dtype=object)
for i,a in enumerate(area):
    vals, probs = SUBTYPE_RULES[a]
    subtype[i] = RNG.choice(vals, p=probs)

bin_index = np.arange(N_BINS, dtype=np.int32)
bin_id = np.array([f'DH-{i+1:05d}' for i in range(N_BINS)], dtype='S10')
city = np.array(['Dhaka']*N_BINS, dtype='S8')

# Assign density based on land use; neighborhood is not used as a socioeconomic proxy.
pop_density = np.empty(N_BINS, dtype='S8')
for i,(a,s) in enumerate(zip(area,subtype)):
    if a == 'Slum' or s == 'Dense Residential':
        d = RNG.choice(['High','Medium'], p=[0.88,0.12])
    elif a in ('Market','Commercial','Garments'):
        d = RNG.choice(['High','Medium','Low'], p=[0.48,0.44,0.08])
    elif a in ('Office','Education'):
        d = RNG.choice(['High','Medium','Low'], p=[0.28,0.58,0.14])
    elif a == 'Recreation':
        d = RNG.choice(['High','Medium','Low'], p=[0.15,0.48,0.37])
    else:
        d = RNG.choice(['High','Medium','Low'], p=[0.32,0.53,0.15])
    pop_density[i] = d.encode()
dens_str = np.char.decode(pop_density)

# Synthetic equivalent population/load served by each bin.
catchment = np.empty(N_BINS, dtype=np.int32)
for i,d in enumerate(dens_str):
    if d == 'High': lo,hi = 150,350
    elif d == 'Medium': lo,hi = 70,170
    else: lo,hi = 25,90
    # public/commercial bins represent a visitor/user equivalent rather than residents.
    if area[i] in ('Market','Commercial','Recreation'):
        hi = int(hi*1.20)
    catchment[i] = RNG.integers(lo, hi+1)

income = np.array(['NA']*N_BINS, dtype='S16')
per_capita = np.full(N_BINS, np.nan, dtype=np.float32)
bin_capture_fraction = np.full(N_BINS, np.nan, dtype=np.float32)
for i,a in enumerate(area):
    if a == 'Slum':
        inc = RNG.choice(['Low','Lower-middle'], p=[0.72,0.28])
    elif a == 'Residential':
        inc = RNG.choice(['Low','Lower-middle','Middle','Upper-middle','High'], p=[0.08,0.20,0.34,0.23,0.15])
    else:
        continue
    income[i] = inc.encode()
    per_capita[i] = np.float32(PER_CAPITA[inc] * RNG.lognormal(0,0.08))
    bin_capture_fraction[i] = np.float32(RNG.uniform(0.35,0.65))

# Synthetic static infrastructure.
bin_volume_liter = np.empty(N_BINS, dtype=np.float32)
placement = np.empty(N_BINS, dtype='S16')
nearby_business = np.empty(N_BINS, dtype='S20')
nearby_poi = np.empty(N_BINS, dtype='S12')
road_access = np.empty(N_BINS, dtype='S12')
service_level = np.empty(N_BINS, dtype='S10')
informal_recovery_rate = np.empty(N_BINS, dtype=np.float32)
battery_drain = RNG.uniform(0.018,0.035,N_BINS).astype(np.float32)
friday_prayer_multiplier = RNG.uniform(3.0,5.0,N_BINS).astype(np.float32)
eid_day_multiplier = np.ones(N_BINS,dtype=np.float32)
collection_interval_hours = np.empty(N_BINS,dtype=np.uint8)
threshold = np.empty(N_BINS,dtype=np.float32)

for i,a in enumerate(area):
    vals,probs = AREA_VOLUME_CHOICES[a]
    bin_volume_liter[i] = RNG.choice(vals,p=probs)
    placement[i] = RNG.choice(AREA_PLACEMENT[a]).encode()
    nearby_business[i] = RNG.choice(AREA_BUSINESS[a]).encode()
    pv,pp = AREA_POI[a]
    nearby_poi[i] = RNG.choice(pv,p=pp).encode()

    if a == 'Slum':
        acc = RNG.choice(['Moderate','Difficult'], p=[0.36,0.64])
    elif a == 'Market':
        acc = RNG.choice(['Easy','Moderate','Difficult'], p=[0.28,0.54,0.18])
    elif a == 'Recreation':
        acc = RNG.choice(['Easy','Moderate','Difficult'], p=[0.52,0.40,0.08])
    else:
        acc = RNG.choice(['Easy','Moderate','Difficult'], p=[0.55,0.38,0.07])
    road_access[i] = acc.encode()

    if acc == 'Difficult':
        srv = RNG.choice(['Moderate','Limited'], p=[0.38,0.62])
    elif acc == 'Moderate':
        srv = RNG.choice(['Good','Moderate','Limited'], p=[0.20,0.67,0.13])
    else:
        srv = RNG.choice(['Good','Moderate'], p=[0.72,0.28])
    service_level[i] = srv.encode()

    # Informal recovery is highest where recyclable streams are concentrated.
    rr = {
        'Residential':(0.05,0.14),'Slum':(0.08,0.20),'Market':(0.04,0.12),
        'Commercial':(0.09,0.20),'Office':(0.11,0.23),'Education':(0.07,0.16),
        'Garments':(0.30,0.52),'Recreation':(0.03,0.09)
    }[a]
    informal_recovery_rate[i] = RNG.uniform(*rr)

    base_int = {'Market':4,'Commercial':6,'Residential':6,'Slum':6,'Office':8,
                'Education':8,'Garments':6,'Recreation':8}[a]
    if srv == 'Limited': base_int += 2
    elif srv == 'Good' and base_int > 4: base_int -= 1
    collection_interval_hours[i] = np.uint8(base_int)

    d = dens_str[i]
    t = 75.0 if d == 'High' else 80.0 if d == 'Medium' else 85.0
    if a == 'Slum': t = min(t,72.0)
    if a == 'Market': t = min(t,75.0)
    threshold[i] = t

    if a == 'Residential': eid_day_multiplier[i] = RNG.uniform(4.0,7.0)
    elif a == 'Slum': eid_day_multiplier[i] = RNG.uniform(3.0,5.0)
    elif subtype[i] in ('Fish Market','General Market','Vegetable Market'): eid_day_multiplier[i] = RNG.uniform(1.8,3.0)
    elif subtype[i] == 'Restaurant/Food Zone': eid_day_multiplier[i] = RNG.uniform(1.3,1.8)
    elif a == 'Recreation': eid_day_multiplier[i] = RNG.uniform(1.2,1.7)

# Base generation. Residential/slum use population and per-capita parameters;
# other areas use activity-specific rates scaled by equivalent catchment load.
baseline_kgph = np.empty(N_BINS,dtype=np.float32)
density_load_multiplier = np.array([DENSITY_MULT[x] for x in dens_str],dtype=np.float32)
for i,(a,s) in enumerate(zip(area,subtype)):
    if a in ('Residential','Slum'):
        base = catchment[i] * per_capita[i] / 24.0 * bin_capture_fraction[i]
    else:
        base = SUBTYPE_BASE_KGPH[s] * (0.55 + 0.45*catchment[i]/100.0)
    baseline_kgph[i] = np.float32(base * density_load_multiplier[i] * RNG.lognormal(0,0.12))

# Synthetic coordinates around neighborhood centers; they are not real bin coordinates.
lat = np.empty(N_BINS,dtype=np.float32); lon = np.empty(N_BINS,dtype=np.float32)
for n in NEIGHBORHOOD_COUNTS:
    msk = neighborhood == n
    m = msk.sum(); clat,clon = NEIGHBORHOOD_CENTERS[n]
    lat[msk] = (clat + RNG.normal(0,0.008,m)).astype(np.float32)
    lon[msk] = (clon + RNG.normal(0,0.009,m)).astype(np.float32)

# Per-bin base composition matrix.
base_comp = np.vstack([BASE_COMP[s] for s in subtype]).astype(np.float32)
subtype_code = np.array([SUBTYPE_CODE[s] for s in subtype],dtype=np.uint8)
area_code = np.array([AREA_CODE[a] for a in area],dtype=np.uint8)
poi_str = np.char.decode(nearby_poi)
mosque_mask = poi_str == 'Mosque'
residential_mask = area == 'Residential'
slum_mask = area == 'Slum'
education_mask = area == 'Education'
recreation_mask = area == 'Recreation'
office_mask = area == 'Office'
market_mask = area == 'Market'
garment_mask = area == 'Garments'

# Nominal mass capacity is only descriptive; fill is volume-based.
nominal_mass_capacity_kg = (bin_volume_liter * 0.18).astype(np.float32)

# Citywide hourly context calibrated to Dhaka monthly climate normals.
# JMA/Tokyo Climate Center normals used here (mean temperature C, precipitation mm):
MONTHLY_MEAN_TEMP_C = {1:18.2,2:21.7,3:26.2,4:28.4,5:28.5,6:29.2,7:28.9,8:29.0,9:28.9,10:27.6,11:23.7,12:19.6}
MONTHLY_PRECIP_MM = {1:7.5,2:23.7,3:48.2,4:148.5,5:299.5,6:311.8,7:362.5,8:296.0,9:235.4,10:165.4,11:14.2,12:16.0}
MONTHLY_HUMIDITY_BASE = {1:66,2:63,3:61,4:67,5:75,6:82,7:84,8:84,9:82,10:77,11:70,12:67}

# Official/public-calendar dates used for government-office closure logic.
# Moon-dependent dates use the dates actually observed/announced in Bangladesh in 2025.
HOLIDAY_BY_DATE = {}
def _add_holiday(d0, d1, label):
    d=d0
    while d<=d1:
        HOLIDAY_BY_DATE[d]=label; d += timedelta(days=1)
_add_holiday(datetime(2025,2,15,tzinfo=BD_TZ).date(), datetime(2025,2,15,tzinfo=BD_TZ).date(), 'Shab-e-Barat')
_add_holiday(datetime(2025,2,21,tzinfo=BD_TZ).date(), datetime(2025,2,21,tzinfo=BD_TZ).date(), 'Language Martyrs Day')
_add_holiday(datetime(2025,3,26,tzinfo=BD_TZ).date(), datetime(2025,3,26,tzinfo=BD_TZ).date(), 'Independence Day')
_add_holiday(datetime(2025,3,28,tzinfo=BD_TZ).date(), datetime(2025,3,28,tzinfo=BD_TZ).date(), 'Shab-e-Qadr/Jumuatul-Wida')
_add_holiday(EID_FITR_START, EID_FITR_END, 'Eid-ul-Fitr')
_add_holiday(datetime(2025,4,14,tzinfo=BD_TZ).date(), datetime(2025,4,14,tzinfo=BD_TZ).date(), 'Bangla New Year')
_add_holiday(datetime(2025,5,1,tzinfo=BD_TZ).date(), datetime(2025,5,1,tzinfo=BD_TZ).date(), 'May Day')
_add_holiday(datetime(2025,5,11,tzinfo=BD_TZ).date(), datetime(2025,5,11,tzinfo=BD_TZ).date(), 'Buddha Purnima')
_add_holiday(EID_PERIOD_START, EID_PERIOD_END, 'Eid-ul-Adha')
_add_holiday(datetime(2025,7,6,tzinfo=BD_TZ).date(), datetime(2025,7,6,tzinfo=BD_TZ).date(), 'Ashura')
_add_holiday(datetime(2025,8,16,tzinfo=BD_TZ).date(), datetime(2025,8,16,tzinfo=BD_TZ).date(), 'Janmashtami')
_add_holiday(datetime(2025,9,6,tzinfo=BD_TZ).date(), datetime(2025,9,6,tzinfo=BD_TZ).date(), 'Eid-e-Milad-un-Nabi')
_add_holiday(datetime(2025,10,1,tzinfo=BD_TZ).date(), datetime(2025,10,2,tzinfo=BD_TZ).date(), 'Durga Puja')
_add_holiday(datetime(2025,12,16,tzinfo=BD_TZ).date(), datetime(2025,12,16,tzinfo=BD_TZ).date(), 'Victory Day')
_add_holiday(datetime(2025,12,25,tzinfo=BD_TZ).date(), datetime(2025,12,25,tzinfo=BD_TZ).date(), 'Christmas Day')
HOLIDAY_CODE = {k:i for i,k in enumerate(HOLIDAY_CATS)}


def season_for_month(month):
    if month in (12,1,2): return 0
    if month in (3,4,5): return 1
    if month in (6,7,8,9): return 2
    return 3


def school_break(d):
    return ((SCHOOL_RAMADAN_BREAK_START <= d <= SCHOOL_RAMADAN_BREAK_END) or
            (SCHOOL_SUMMER_EID_BREAK_START <= d <= SCHOOL_SUMMER_EID_BREAK_END) or
            (SCHOOL_DURGA_BREAK_START <= d <= SCHOOL_DURGA_BREAK_END))


def office_closed(d, dow):
    if d in SPECIAL_WORKING_DAYS:
        return False
    return (dow in (4,5)) or (d in HOLIDAY_BY_DATE)

# First create persistent citywide weather/rainfall states. Monthly precipitation is
# subsequently scaled so each synthetic month's total matches the cited climate normal.
weather_state = np.empty(N_HOURS,dtype=np.uint8)
rain_raw = np.zeros(N_HOURS,dtype=np.float32)
prev_weather = 0
for h in range(N_HOURS):
    ts = START_DATE + timedelta(hours=h); mo=ts.month
    precip=MONTHLY_PRECIP_MM[mo]
    rain_p = float(np.clip(0.018 + precip/720.0, 0.025, 0.56))
    storm_p = float(np.clip((precip-80.0)/3600.0, 0.003, 0.075))
    cloud_p = float(np.clip(0.16 + 0.18*(precip/362.5),0.16,0.34))
    sunny_p = max(0.04,1.0-rain_p-storm_p-cloud_p)
    probs=np.array([sunny_p,cloud_p,rain_p,storm_p],dtype=float); probs/=probs.sum()
    # Weather persistence creates multi-hour spells instead of independent hourly jumps.
    if h==0 or RNG.random() < (0.15 if prev_weather in (0,1) else 0.28):
        w=int(RNG.choice(4,p=probs))
    else:
        w=int(prev_weather)
    weather_state[h]=w; prev_weather=w
    if w==2: rain_raw[h]=RNG.gamma(1.5,1.2)
    elif w==3: rain_raw[h]=RNG.gamma(2.2,2.8)

# Scale hourly rain so monthly sums equal published Dhaka precipitation normals.
for mo in range(1,13):
    idx=np.array([(START_DATE+timedelta(hours=h)).month==mo for h in range(N_HOURS)])
    sm=float(rain_raw[idx].sum())
    if sm>0: rain_raw[idx] *= np.float32(MONTHLY_PRECIP_MM[mo]/sm)

ctx = []
daily_anomaly=0.0
last_date=None
for h in range(N_HOURS):
    ts = START_DATE + timedelta(hours=h)
    d = ts.date(); dow = ts.weekday(); hour = ts.hour; mo=ts.month
    if d != last_date:
        daily_anomaly = 0.72*daily_anomaly + float(RNG.normal(0,0.75))
        last_date=d
    weekend = dow in (4,5) and d not in SPECIAL_WORKING_DAYS
    is_ramadan = RAMADAN_START <= d <= RAMADAN_END
    is_eid_fitr = d == EID_FITR_DAY
    is_eid_fitr_period = EID_FITR_START <= d <= EID_FITR_END
    is_eid = d == EID_DAY
    is_eid_period = EID_PERIOD_START <= d <= EID_PERIOD_END
    is_durga_break = SCHOOL_DURGA_BREAK_START <= d <= SCHOOL_DURGA_BREAK_END
    public_holiday = d in HOLIDAY_BY_DATE
    hlabel=HOLIDAY_BY_DATE.get(d,'None')
    hcode=HOLIDAY_CODE[hlabel]
    if is_eid: event=6
    elif is_eid_period: event=5
    elif is_eid_fitr: event=4
    elif is_eid_fitr_period: event=3
    elif hlabel=='Durga Puja': event=7
    elif public_holiday: event=2
    elif weekend: event=1
    else: event=0
    prayer = (dow == 4 and 12 <= hour <= 14)
    season = season_for_month(mo)
    weather=int(weather_state[h]); rainfall=float(rain_raw[h])
    # Monthly normal + diurnal cycle. Amplitude is smaller in wet monsoon months.
    amp = 5.0 if mo in (12,1,2) else 4.4 if mo in (3,4,5) else 3.2 if mo in (6,7,8,9) else 4.0
    temp = MONTHLY_MEAN_TEMP_C[mo] + amp*math.sin(2*math.pi*(hour/24.0-0.27)) + daily_anomaly
    humid = MONTHLY_HUMIDITY_BASE[mo] - 7.0*math.sin(2*math.pi*(hour/24.0-0.27))
    if weather == 1: temp -= 0.6; humid += 5
    elif weather == 2: temp -= 1.6; humid += 11
    elif weather == 3: temp -= 2.6; humid += 17
    temp = float(np.clip(temp + RNG.normal(0,0.35),12,40))
    humid = float(np.clip(humid + RNG.normal(0,1.3),38,99))
    school_closed_today = school_break(d) or weekend or public_holiday
    # University calendars differ by institution. We model public holidays/weekends and
    # Eid blocks as closures, while Ramadan reduces daytime activity rather than forcing closure.
    college_closed_today = weekend or public_holiday or is_eid_fitr_period or is_eid_period
    office_closed_today = office_closed(d,dow)
    ctx.append((int(ts.timestamp()),dow,hour,event,weekend,prayer,is_eid_period,is_eid,
                is_eid_fitr_period,is_eid_fitr,is_ramadan,is_durga_break,public_holiday,hcode,
                season,weather,rainfall,temp,humid,school_closed_today,college_closed_today,office_closed_today))

def activity_multiplier_vector(hour,dow,weekend,event,weather,is_ramadan,season,hcode,
                               school_closed_today,college_closed_today,office_closed_today):
    """Land-use and subtype-specific activity multipliers for the 2025 calendar.

    Calendar dates are evidence-based where available. Fine-grained behavioral
    coefficients remain scenario assumptions and are intentionally documented as such.
    """
    m = np.ones(N_BINS,dtype=np.float32)
    hlabel = HOLIDAY_CATS[int(hcode)]

    # Residential / informal settlements: morning and evening accumulation peaks.
    m[residential_mask] *= (1.34 if 18 <= hour <= 22 else 1.14 if 6 <= hour <= 9 else 0.92)
    m[slum_mask] *= (1.25 if (6 <= hour <= 9 or 18 <= hour <= 23) else 1.00)
    if is_ramadan:
        # Scenario: household food preparation/packaging shifts toward late afternoon/evening.
        if 15 <= hour <= 21:
            m[residential_mask|slum_mask] *= 1.16
        elif 6 <= hour <= 14:
            m[residential_mask|slum_mask] *= 0.95

    # Market subtypes.
    fish = subtype == 'Fish Market'; veg = subtype == 'Vegetable Market'; genm = subtype == 'General Market'
    m[fish] *= (1.86 if 5 <= hour <= 10 else 1.18 if 16 <= hour <= 19 else 0.70)
    m[veg] *= (1.72 if 6 <= hour <= 11 else 1.18 if 16 <= hour <= 19 else 0.71)
    m[genm] *= (1.43 if 7 <= hour <= 13 else 1.27 if 16 <= hour <= 20 else 0.79)
    if is_ramadan and 14 <= hour <= 19:
        m[market_mask] *= 1.18

    # Commercial subtypes.
    shopping = subtype == 'Shopping'; rest = subtype == 'Restaurant/Food Zone'; mixed = subtype == 'Mixed Commercial'
    if is_ramadan:
        # Daytime restaurant waste is reduced while iftar/dinner preparation is elevated.
        m[shopping] *= (1.48 if 15 <= hour <= 22 else 0.58)
        m[rest] *= (2.15 if 16 <= hour <= 22 else 0.38 if 6 <= hour <= 15 else 0.62)
        m[mixed] *= (1.38 if 14 <= hour <= 22 else 0.68)
    else:
        m[shopping] *= (1.45 if 11 <= hour <= 21 else 0.60)
        m[rest] *= (1.65 if 12 <= hour <= 15 else 1.85 if 18 <= hour <= 23 else 0.58)
        m[mixed] *= (1.35 if 10 <= hour <= 21 else 0.72)

    # Government/private offices. Official Ramadan office hours were 09:00-15:30.
    if not office_closed_today:
        if is_ramadan:
            m[office_mask] *= (1.35 if 9 <= hour <= 15 else 0.20)
        else:
            m[office_mask] *= (1.40 if 9 <= hour <= 18 else 0.22)
    else:
        m[office_mask] *= 0.25

    # Education: schools follow the published 2025 secondary-school long breaks.
    school = subtype == 'School'; college = subtype == 'College/University'
    if school_closed_today:
        m[school] *= 0.20
    else:
        m[school] *= (1.45 if 7 <= hour <= 15 else 0.18)
    if college_closed_today:
        m[college] *= 0.24
    else:
        cm = (1.34 if 8 <= hour <= 17 else 0.22)
        if is_ramadan: cm *= 0.78
        m[college] *= cm

    # Garment factories: large textile stream but a large share is recovered as jhut.
    if event in (3,4,5,6):
        m[garment_mask] *= 0.52
    elif weekend:
        m[garment_mask] *= 0.72
    else:
        m[garment_mask] *= (1.38 if 8 <= hour <= 20 else 0.40)

    # Recreation: evening/weekend/holiday demand; rainfall suppresses outdoor footfall.
    park = subtype == 'Park'; play = subtype == 'Playground'; ent = subtype == 'Entertainment Center'
    m[park] *= (1.55 if 16 <= hour <= 21 else 1.20 if 6 <= hour <= 9 else 0.55)
    m[play] *= (1.50 if 15 <= hour <= 20 else 0.60)
    m[ent] *= (1.60 if 17 <= hour <= 23 else 0.62)
    if weekend: m[recreation_mask] *= 1.42
    if hlabel != 'None': m[recreation_mask] *= 1.16
    if hlabel == 'Bangla New Year':
        m[recreation_mask|shopping] *= 1.38
    if hlabel == 'Durga Puja':
        m[recreation_mask|shopping] *= 1.24

    # Weekend effects on selected public/commercial sources.
    if weekend:
        m[market_mask] *= 1.11
        m[rest] *= 1.17
        m[shopping] *= 1.11

    # Weather primarily affects outdoor activity and collection, not total citywide waste strongly.
    if weather == 2:  # Rain
        m[recreation_mask] *= 0.60
        m[market_mask] *= 0.93
        m[residential_mask] *= 1.03
    elif weather == 3:  # Storm
        m[recreation_mask] *= 0.35
        m[market_mask] *= 0.84
        m[residential_mask] *= 1.05

    # Small seasonal modulation only; literature suggests overall seasonal differences are not substantial.
    seasonal = (0.97,1.01,1.03,0.99)[int(season)]
    m *= np.float32(seasonal)
    return m


if OUT_H5.exists(): OUT_H5.unlink()
with h5py.File(OUT_H5,'w') as f:
    f.attrs['dataset_title'] = 'Dhaka Smart Waste Synthetic IoT Dataset V4.0 — One-Year 2025'
    f.attrs['version'] = '4.0'
    f.attrs['seed'] = SEED
    f.attrs['n_bins'] = N_BINS; f.attrs['n_days'] = N_DAYS; f.attrs['n_rows'] = N_ROWS
    f.attrs['start_local'] = START_DATE.isoformat()
    f.attrs['end_local'] = (START_DATE + timedelta(hours=N_HOURS-1)).isoformat()
    f.attrs['timezone'] = 'Asia/Dhaka (UTC+06:00)'
    f.attrs['weekend_definition'] = 'Friday-Saturday'
    f.attrs['eid_ul_adha_2025_date'] = str(EID_DAY)
    f.attrs['eid_holiday_window'] = f'{EID_PERIOD_START}..{EID_PERIOD_END}'
    f.attrs['eid_ul_fitr_2025_date'] = str(EID_FITR_DAY)
    f.attrs['eid_ul_fitr_holiday_window'] = f'{EID_FITR_START}..{EID_FITR_END}'
    f.attrs['ramadan_2025_window'] = f'{RAMADAN_START}..{RAMADAN_END}'
    f.attrs['school_ramadan_break'] = f'{SCHOOL_RAMADAN_BREAK_START}..{SCHOOL_RAMADAN_BREAK_END}'
    f.attrs['school_summer_eid_break'] = f'{SCHOOL_SUMMER_EID_BREAK_START}..{SCHOOL_SUMMER_EID_BREAK_END}'
    f.attrs['school_durga_break'] = f'{SCHOOL_DURGA_BREAK_START}..{SCHOOL_DURGA_BREAK_END}'
    f.attrs['special_working_days'] = '2025-05-17;2025-05-24'
    f.attrs['climate_calibration'] = 'Dhaka monthly mean temperature and precipitation normals from JMA/Tokyo Climate Center ClimatView.'
    f.attrs['sensor_noise_sigma_fill_percent'] = 1.5
    f.attrs['packet_loss_probability'] = 0.005
    f.attrs['sensor_anomaly_probability'] = 0.001
    f.attrs['synthetic_coordinates'] = True
    f.attrs['method_note'] = 'One-year scenario-based synthetic digital twin. Calendar/climate anchors and selected waste parameters are literature-calibrated; fine-grained behavioral multipliers are transparent simulation assumptions, not direct field measurements.'

    g = f.create_group('bins')
    static = {
        'bin_index':bin_index, 'bin_id':bin_id, 'city':city,
        'area_type':np.array(area,dtype='S16'), 'land_use_subtype':np.array(subtype,dtype='S24'),
        'neighborhood':np.array(neighborhood,dtype='S20'),
        'bin_volume_liter':bin_volume_liter, 'nominal_mass_capacity_kg':nominal_mass_capacity_kg,
        'latitude':lat, 'longitude':lon, 'placement':placement,
        'nearby_business_type':nearby_business, 'nearby_poi_type':nearby_poi,
        'population_density':pop_density, 'catchment_population_equivalent':catchment,
        'income_band':income, 'per_capita_waste_kg_day':per_capita,
        'bin_capture_fraction':bin_capture_fraction,
        'density_load_multiplier':density_load_multiplier,
        'baseline_generation_kg_per_hour':baseline_kgph,
        'road_accessibility':road_access, 'collection_service_level':service_level,
        'collection_interval_hours':collection_interval_hours,
        'informal_recovery_rate':informal_recovery_rate,
        'collection_threshold_percent':threshold,
        'battery_drain_percent_per_hour':battery_drain,
        'friday_prayer_multiplier':friday_prayer_multiplier,
        'eid_day_multiplier':eid_day_multiplier,
        'base_composition_percent':(base_comp*100).astype(np.float32),
    }
    for name,arr in static.items():
        g.create_dataset(name,data=arr,compression='lzf',shuffle=True)
    g.attrs['base_composition_categories'] = json.dumps(COMPOSITION_CATS)

    o = f.create_group('observations')
    dtypes = {
        'bin_index':np.int32, 'timestamp_unix':np.int64, 'date_index':np.uint16,
        'day_of_week':np.uint8, 'hour':np.uint8, 'time_slot_code':np.uint8, 'event_code':np.uint8,
        'is_weekend':np.uint8, 'is_public_holiday':np.uint8, 'holiday_code':np.uint8,
        'season_code':np.uint8, 'weather_code':np.uint8, 'rainfall_mm_hour':np.float32,
        'temperature_c':np.float32, 'humidity_percent':np.float32,
        'institution_status_code':np.uint8, 'school_calendar_closed':np.uint8,
        'college_calendar_closed':np.uint8, 'office_calendar_closed':np.uint8,
        'is_special_working_day':np.uint8,
        'activity_multiplier':np.float32,
        'gross_waste_generation_kg':np.float32, 'informal_recovery_kg':np.float32,
        'waste_entering_bin_kg':np.float32, 'waste_volume_liter':np.float32,
        'waste_bulk_density_kg_m3':np.float32,
        'organic_food_pct':np.uint8, 'fish_meat_pct':np.uint8, 'animal_residue_pct':np.uint8,
        'plastic_pct':np.uint8, 'paper_cardboard_pct':np.uint8, 'textile_pct':np.uint8,
        'metal_glass_pct':np.uint8, 'green_other_pct':np.uint8,
        'dominant_waste_code':np.uint8,
        'true_fill_level_percent':np.float32, 'fill_level_percent':np.float32,
        'predicted_fill_level_percent':np.float32, 'collection_threshold_percent':np.float32,
        'needs_collection':np.uint8, 'is_collection_due':np.uint8,
        'collection_event':np.uint8, 'hours_since_last_collection':np.float32,
        'collection_delay_minutes':np.float32,
        'overflow_kg':np.float32, 'predicted_overflow_kg_4h':np.float32,
        'battery_level_percent':np.float32, 'battery_maintenance_event':np.uint8, 'is_packet_loss':np.uint8,
        'is_sensor_anomaly':np.uint8, 'sensor_error_code':np.uint8,
        'is_friday_prayer_window':np.uint8, 'friday_effect_active':np.uint8,
        'is_ramadan':np.uint8, 'is_eid_fitr_period':np.uint8, 'is_eid_fitr_day':np.uint8,
        'is_eid_period':np.uint8, 'is_eid_day':np.uint8,
        'is_durga_puja_school_break':np.uint8,
    }
    ds = {}
    chunk = min(240_000,N_ROWS)
    for name,dtype in dtypes.items():
        fv = np.nan if np.issubdtype(dtype,np.floating) else 0
        ds[name] = o.create_dataset(name,shape=(N_ROWS,),dtype=dtype,chunks=(chunk,),compression='lzf',shuffle=True,fillvalue=fv)
    o.attrs['event_categories'] = json.dumps(EVENT_CATS)
    o.attrs['weather_categories'] = json.dumps(WEATHER_CATS)
    o.attrs['time_slot_categories'] = json.dumps(TIME_SLOT_CATS)
    o.attrs['season_categories'] = json.dumps(SEASON_CATS)
    o.attrs['holiday_categories'] = json.dumps(HOLIDAY_CATS)
    o.attrs['institution_status_categories'] = json.dumps(INSTITUTION_STATUS_CATS)
    o.attrs['dominant_waste_categories'] = json.dumps(DOMINANT_WASTE_CATS)
    o.attrs['sensor_error_categories'] = json.dumps(SENSOR_ERROR_CATS)
    o.attrs['composition_note'] = 'Eight percentage fields describe residual waste entering the bin after synthetic informal recovery and sum to exactly 100.'
    o.attrs['fill_note'] = 'true_fill_level is latent volume-based ground truth; fill_level is noisy sensor observation and is NaN during packet loss.'

    # State variables are volume-based for fill, plus hours since collection.
    current_volume_l = bin_volume_liter * RNG.uniform(0.05,0.22,N_BINS).astype(np.float32)
    battery_state = RNG.uniform(95,100,N_BINS).astype(np.float32)
    hours_since_collect = RNG.uniform(0,collection_interval_hours.astype(float),N_BINS).astype(np.float32)
    due_delay_hours = np.zeros(N_BINS,dtype=np.float32)

    access_str = np.char.decode(road_access); service_str = np.char.decode(service_level)
    service_prob = np.where(service_str=='Good',0.96,np.where(service_str=='Moderate',0.86,0.72)).astype(np.float32)
    service_prob *= np.where(access_str=='Difficult',0.82,np.where(access_str=='Moderate',0.93,1.0)).astype(np.float32)

    write_pos = 0
    comp_names = ['organic_food_pct','fish_meat_pct','animal_residue_pct','plastic_pct','paper_cardboard_pct','textile_pct','metal_glass_pct','green_other_pct']
    for day_idx in range(N_DAYS):
        shape = (24,N_BINS)
        B = {name:np.empty(shape,dtype=dtype) for name,dtype in dtypes.items()}
        for hh in range(24):
            gh = day_idx*24 + hh
            (ts_epoch,dow,hour,event,weekend,prayer,is_eid_period,is_eid,
             is_eid_fitr_period,is_eid_fitr,is_ramadan,is_durga_break,public_holiday,hcode,
             season,weather,rainfall_mm,temp_base,humid_base,school_closed_today,
             college_closed_today,office_closed_today) = ctx[gh]

            act = activity_multiplier_vector(hour,dow,weekend,event,weather,is_ramadan,season,hcode,
                                             school_closed_today,college_closed_today,office_closed_today)

            friday_vec = np.ones(N_BINS,dtype=np.float32); friday_active = np.zeros(N_BINS,dtype=np.uint8)
            if prayer:
                friday_active = mosque_mask.astype(np.uint8)
                friday_vec[mosque_mask] = friday_prayer_multiplier[mosque_mask]

            event_vec = np.ones(N_BINS,dtype=np.float32)
            # Eid-ul-Adha is the strongest exceptional waste pulse; 2025 Dhaka city corporations
            # reported tens of thousands of tonnes of sacrificial waste over the three Eid days.
            if is_eid:
                event_vec = eid_day_multiplier.copy()
            elif is_eid_period:
                event_vec[residential_mask|slum_mask] = 1.48
                event_vec[market_mask] = 1.30
                event_vec[recreation_mask] = 1.12
            # Eid-ul-Fitr mainly shifts household food/packaging and recreation demand.
            if is_eid_fitr:
                event_vec[residential_mask|slum_mask] *= 1.34
                event_vec[recreation_mask] *= 1.28
                event_vec[subtype == 'Restaurant/Food Zone'] *= 1.24
            elif is_eid_fitr_period:
                event_vec[residential_mask|slum_mask] *= 1.12
                event_vec[market_mask] *= 1.08
                event_vec[recreation_mask] *= 1.14

            stochastic = RNG.lognormal(mean=-0.5*0.18**2,sigma=0.18,size=N_BINS).astype(np.float32)
            gross = baseline_kgph * act * friday_vec * event_vec * stochastic
            gross = np.clip(gross,0.01,None).astype(np.float32)

            # Dynamic composition around each bin's land-use profile.
            comp = base_comp + RNG.normal(0,0.012,size=(N_BINS,len(COMPOSITION_CATS))).astype(np.float32)
            comp = np.clip(comp,0.001,None)
            # Calendar-linked composition shifts. These are transparent scenario coefficients.
            if is_ramadan:
                comp[residential_mask|slum_mask,0] += 0.025
                rz = subtype == 'Restaurant/Food Zone'
                comp[rz,0] += 0.035; comp[rz,3] += 0.018
            if is_eid_fitr:
                comp[residential_mask|slum_mask,0] += 0.055
                comp[residential_mask|slum_mask,3] += 0.025
            # Eid-ul-Adha adds animal residue in residential and informal-settlement streams.
            if is_eid:
                comp[residential_mask,2] += 0.34
                comp[slum_mask,2] += 0.26
                comp[market_mask,1] += 0.05
            comp /= comp.sum(axis=1,keepdims=True)

            recyclable_share = comp[:,RECYCLABLE_IDX].sum(axis=1)
            recov_frac = np.clip(informal_recovery_rate * recyclable_share * RNG.uniform(0.85,1.15,N_BINS),0,0.55).astype(np.float32)
            recovered = (gross * recov_frac).astype(np.float32)
            entering = (gross - recovered).astype(np.float32)

            # Remove recyclable components proportionally, then renormalize residual composition.
            residual_comp = comp.copy()
            residual_comp[:,RECYCLABLE_IDX] *= (1.0 - informal_recovery_rate[:,None])
            residual_comp /= residual_comp.sum(axis=1,keepdims=True)
            bulk_density = (residual_comp * COMP_DENSITY).sum(axis=1).astype(np.float32)
            volume_l = (entering / bulk_density * 1000.0).astype(np.float32)

            raw_volume = current_volume_l + volume_l
            overflow_l = np.maximum(raw_volume - bin_volume_liter,0).astype(np.float32)
            true_fill = np.minimum(raw_volume/bin_volume_liter*100.0,100.0).astype(np.float32)
            # Convert overflow volume back to kg using current residual mixture density.
            overflow_kg = (overflow_l/1000.0*bulk_density).astype(np.float32)
            needs = (true_fill >= threshold).astype(np.uint8)

            hours_since_collect = (hours_since_collect + 1.0).astype(np.float32)
            due = needs.astype(bool) & (hours_since_collect >= collection_interval_hours.astype(np.float32))
            prob = service_prob.copy()
            if weather == 2: prob *= 0.90
            elif weather == 3: prob *= 0.72
            # Intensive Eid-ul-Adha cleanup partially offsets the exceptional waste pulse.
            if is_eid: prob = np.minimum(prob*1.10,0.995)
            collect = due & (RNG.random(N_BINS) < prob)
            emergency = (true_fill >= 100.0) & (~collect) & (RNG.random(N_BINS) < 0.35)
            collect = collect | emergency

            # Delay accumulates only after a collection becomes due, not simply
            # because many hours have elapsed since a previous collection.
            due_delay_hours = np.where(due, due_delay_hours + 1.0, 0.0).astype(np.float32)
            delay = np.where(due, np.maximum(due_delay_hours-1.0,0.0)*60.0, 0.0).astype(np.float32)
            # Add access/weather arrival delay when collection occurs.
            arrival = np.zeros(N_BINS,dtype=np.float32)
            cm = collect
            if cm.any():
                base_arr = RNG.uniform(5,28,cm.sum()).astype(np.float32)
                acc_mult = np.where(access_str[cm]=='Difficult',2.1,np.where(access_str[cm]=='Moderate',1.4,1.0))
                weather_m = 1.0 if weather < 2 else 1.35 if weather == 2 else 1.85
                arrival[cm] = base_arr*acc_mult*weather_m
            delay = np.where(collect,delay+arrival,delay).astype(np.float32)

            # Forecast four hours ahead using current local activity as an operational approximation.
            expected_4h_kg = baseline_kgph*act*friday_vec*event_vec*4.0*(1.0-informal_recovery_rate*recyclable_share)
            expected_4h_l = expected_4h_kg/np.maximum(bulk_density,1.0)*1000.0
            forecast_raw = (raw_volume + expected_4h_l)/bin_volume_liter*100.0
            pred_overflow_l = np.maximum(raw_volume + expected_4h_l - bin_volume_liter,0.0)
            pred_overflow_kg = (pred_overflow_l/1000.0*bulk_density).astype(np.float32)
            forecast = np.clip(forecast_raw + RNG.normal(0,2.0,N_BINS),0,100).astype(np.float32)

            # Sensor telemetry.
            observed_fill = np.clip(true_fill + RNG.normal(0,1.5,N_BINS),0,100).astype(np.float32)
            temp_obs = (temp_base + RNG.normal(0,0.45,N_BINS)).astype(np.float32)
            humid_obs = np.clip(humid_base + RNG.normal(0,1.5,N_BINS),40,100).astype(np.float32)
            extra_drain = 0.0 if weather < 2 else 0.003 if weather == 2 else 0.008
            battery_state = np.maximum(battery_state - battery_drain - extra_drain,0).astype(np.float32)
            # Maintenance/replacement prevents unrealistic year-long batteries from remaining at zero.
            maint = np.zeros(N_BINS,dtype=np.uint8)
            low_bat = battery_state < 15.0
            if 8 <= hour <= 17 and low_bat.any():
                repl = low_bat & (RNG.random(N_BINS) < 0.055)
                if repl.any():
                    battery_state[repl] = RNG.uniform(96,100,repl.sum()).astype(np.float32)
                    maint[repl] = 1

            packet_p = np.full(N_BINS,0.0047,dtype=np.float32)
            if weather == 3: packet_p += 0.0015
            packet_p += np.where(battery_state < 8.0,0.008,0.0).astype(np.float32)
            packet = RNG.random(N_BINS) < packet_p
            anomaly = (RNG.random(N_BINS) < 0.001) & (~packet)
            err_code = np.zeros(N_BINS,dtype=np.uint8)
            if anomaly.any():
                kinds = RNG.integers(1,4,size=anomaly.sum(),dtype=np.uint8)
                err_code[anomaly] = kinds
                idxs = np.flatnonzero(anomaly)
                for code in (1,2,3):
                    sel = idxs[kinds==code]
                    if code == 1: observed_fill[sel] = 0.0
                    elif code == 2: observed_fill[sel] = 100.0
                    else: observed_fill[sel] = np.clip(observed_fill[sel]+RNG.choice([-25.0,25.0],size=len(sel)),0,100)
            observed_fill[packet] = np.nan; temp_obs[packet] = np.nan; humid_obs[packet] = np.nan
            battery_obs = battery_state.copy(); battery_obs[packet] = np.nan

            # Percent composition stored as integers summing to exactly 100.
            pct = np.rint(residual_comp*100).astype(np.int16)
            diff = 100 - pct.sum(axis=1)
            dom = np.argmax(residual_comp,axis=1)
            pct[np.arange(N_BINS),dom] += diff
            pct = np.clip(pct,0,100).astype(np.uint8)
            dom_code = np.argmax(pct,axis=1).astype(np.uint8)

            # Institution status applies to Education and Office, with subtype-specific calendars.
            inst = np.zeros(N_BINS,dtype=np.uint8)
            school = subtype == 'School'; college = subtype == 'College/University'
            inst[school] = 2 if school_closed_today else 1
            inst[college] = 2 if college_closed_today else 1
            inst[office_mask] = 2 if office_closed_today else 1

            if hour < 6 or hour >= 21: tslot=0
            elif hour < 12: tslot=1
            elif hour < 17: tslot=2
            else: tslot=3

            B['bin_index'][hh]=bin_index; B['timestamp_unix'][hh]=ts_epoch; B['date_index'][hh]=day_idx
            B['day_of_week'][hh]=dow; B['hour'][hh]=hour; B['time_slot_code'][hh]=tslot; B['event_code'][hh]=event
            B['is_weekend'][hh]=np.uint8(weekend); B['is_public_holiday'][hh]=np.uint8(public_holiday); B['holiday_code'][hh]=np.uint8(hcode)
            B['season_code'][hh]=np.uint8(season); B['weather_code'][hh]=weather; B['rainfall_mm_hour'][hh]=np.float32(rainfall_mm)
            B['temperature_c'][hh]=temp_obs; B['humidity_percent'][hh]=humid_obs
            B['institution_status_code'][hh]=inst; B['school_calendar_closed'][hh]=np.uint8(school_closed_today)
            B['college_calendar_closed'][hh]=np.uint8(college_closed_today); B['office_calendar_closed'][hh]=np.uint8(office_closed_today)
            curdate=(START_DATE+timedelta(days=day_idx)).date(); B['is_special_working_day'][hh]=np.uint8(curdate in SPECIAL_WORKING_DAYS)
            B['activity_multiplier'][hh]=act
            B['gross_waste_generation_kg'][hh]=gross; B['informal_recovery_kg'][hh]=recovered
            B['waste_entering_bin_kg'][hh]=entering; B['waste_volume_liter'][hh]=volume_l; B['waste_bulk_density_kg_m3'][hh]=bulk_density
            for j,nm in enumerate(comp_names): B[nm][hh]=pct[:,j]
            B['dominant_waste_code'][hh]=dom_code
            B['true_fill_level_percent'][hh]=true_fill; B['fill_level_percent'][hh]=observed_fill; B['predicted_fill_level_percent'][hh]=forecast
            B['collection_threshold_percent'][hh]=threshold; B['needs_collection'][hh]=needs; B['is_collection_due'][hh]=due.astype(np.uint8)
            B['collection_event'][hh]=collect.astype(np.uint8); B['hours_since_last_collection'][hh]=hours_since_collect; B['collection_delay_minutes'][hh]=delay
            B['overflow_kg'][hh]=overflow_kg; B['predicted_overflow_kg_4h'][hh]=pred_overflow_kg
            B['battery_level_percent'][hh]=battery_obs; B['battery_maintenance_event'][hh]=maint
            B['is_packet_loss'][hh]=packet.astype(np.uint8); B['is_sensor_anomaly'][hh]=anomaly.astype(np.uint8)
            B['sensor_error_code'][hh]=err_code; B['is_friday_prayer_window'][hh]=np.uint8(prayer); B['friday_effect_active'][hh]=friday_active
            B['is_ramadan'][hh]=np.uint8(is_ramadan); B['is_eid_fitr_period'][hh]=np.uint8(is_eid_fitr_period); B['is_eid_fitr_day'][hh]=np.uint8(is_eid_fitr)
            B['is_eid_period'][hh]=np.uint8(is_eid_period); B['is_eid_day'][hh]=np.uint8(is_eid); B['is_durga_puja_school_break'][hh]=np.uint8(is_durga_break)

            # Update true state after collection. Residual 2-7% volume remains.
            residual_vol = bin_volume_liter*RNG.uniform(0.02,0.07,N_BINS).astype(np.float32)
            current_volume_l = np.where(collect,residual_vol,np.minimum(raw_volume,bin_volume_liter)).astype(np.float32)
            hours_since_collect = np.where(collect,0.0,hours_since_collect).astype(np.float32)
            due_delay_hours = np.where(collect,0.0,due_delay_hours).astype(np.float32)

        n=24*N_BINS; sl=slice(write_pos,write_pos+n)
        for name in dtypes: ds[name][sl]=B[name].reshape(-1)
        write_pos += n
        if (day_idx+1)%7==0 or day_idx==N_DAYS-1:
            print(f'Wrote day {day_idx+1:02d}/{N_DAYS} ({write_pos:,}/{N_ROWS:,} rows)',flush=True)

assert write_pos == N_ROWS
print(f'Created {OUT_H5} ({OUT_H5.stat().st_size/1024/1024:.1f} MiB)',flush=True)
