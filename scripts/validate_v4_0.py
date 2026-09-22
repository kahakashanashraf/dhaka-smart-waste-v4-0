#!/usr/bin/env python3
from pathlib import Path
import json, math, sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
import h5py, numpy as np, pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
H5 = Path(sys.argv[1]).expanduser().resolve() if len(sys.argv) > 1 else REPO_ROOT / 'src' / 'dhaka_smart_waste_v4_0_2025.h5'
OUT = Path(sys.argv[2]).expanduser().resolve() if len(sys.argv) > 2 else REPO_ROOT / 'VALIDATION_REPORT.json'
if not H5.exists():
    raise SystemExit(f'Canonical HDF5 not found: {H5}. Run: python src/generate_v4_0.py')
comp_cols=['organic_food_pct','fish_meat_pct','animal_residue_pct','plastic_pct','paper_cardboard_pct','textile_pct','metal_glass_pct','green_other_pct']
with h5py.File(H5,'r') as f:
    b=f['bins']; o=f['observations']; n=int(f.attrs['n_rows']); nb=int(f.attrs['n_bins'])
    area=np.char.decode(b['area_type'][:]); subtype=np.char.decode(b['land_use_subtype'][:]); dens=np.char.decode(b['population_density'][:]); access=np.char.decode(b['road_accessibility'][:])
    report={'structure':{},'rates':{},'composition':{},'context_patterns':{},'climate':{},'checks':{},'metadata':{}}
    report['structure']={'rows':n,'bins':nb,'days':int(f.attrs['n_days']),'hours_per_bin':n//nb,'observation_columns':len(o.keys()),'bin_columns':len(b.keys()),'start_local':str(f.attrs['start_local']),'end_local':str(f.attrs['end_local'])}
    # hourly citywide context from bin 0
    ts=o['timestamp_unix'][::nb]; rain=o['rainfall_mm_hour'][::nb]; weather=o['weather_code'][::nb]
    dates=pd.to_datetime(ts,unit='s',utc=True).tz_convert('Asia/Dhaka')
    temp=o['temperature_c'][::nb]; hum=o['humidity_percent'][::nb]
    cdf=pd.DataFrame({'month':dates.month,'rain':rain,'temp':temp,'hum':hum,'weather':weather})
    clim={}
    for mo,g in cdf.groupby('month'):
        clim[str(int(mo))]={'rainfall_mm':float(g.rain.sum()),'mean_temperature_c_bin0':float(g.temp.mean()),'mean_humidity_percent_bin0':float(g.hum.mean()),'rainy_hours':int((g.weather==2).sum()),'storm_hours':int((g.weather==3).sum())}
    report['climate']['monthly']=clim
    report['climate']['rainfall_monthly_sums_match_targets']=all(abs(clim[str(m)]['rainfall_mm']-v)<0.02 for m,v in {1:7.5,2:23.7,3:48.2,4:148.5,5:299.5,6:311.8,7:362.5,8:296.0,9:235.4,10:165.4,11:14.2,12:16.0}.items())

    sums=defaultdict(float); cnt=defaultdict(int)
    bad_comp=0; bad_label=0
    grp_sum=defaultdict(float); grp_n=defaultdict(int)
    delay_sum=defaultdict(float); delay_n=defaultdict(int)
    mass_org=mass_total=recovered_total=gross_total=0.0
    chunk=1_200_000
    for st in range(0,n,chunk):
        en=min(st+chunk,n); bi=o['bin_index'][st:en]
        # global binary rates
        for k in ['is_packet_loss','is_sensor_anomaly','battery_maintenance_event','collection_event','needs_collection','is_public_holiday','is_ramadan','is_eid_fitr_day','is_eid_day','is_special_working_day']:
            sums[k]+=float(o[k][st:en].sum())
        # integrity
        pct=np.zeros(en-st,dtype=np.int16)
        for k in comp_cols: pct += o[k][st:en].astype(np.int16)
        bad_comp += int(np.count_nonzero(pct!=100))
        true=o['true_fill_level_percent'][st:en]; th=o['collection_threshold_percent'][st:en]; lab=o['needs_collection'][st:en]
        bad_label += int(np.count_nonzero(lab != (true>=th)))
        entering=o['waste_entering_bin_kg'][st:en].astype(np.float64); gross=o['gross_waste_generation_kg'][st:en].astype(np.float64); rec=o['informal_recovery_kg'][st:en].astype(np.float64)
        orgpct=(o['organic_food_pct'][st:en].astype(np.float64)+o['fish_meat_pct'][st:en].astype(np.float64)+o['animal_residue_pct'][st:en].astype(np.float64)+o['green_other_pct'][st:en].astype(np.float64))
        mass_org += float((entering*orgpct/100).sum()); mass_total += float(entering.sum()); recovered_total += float(rec.sum()); gross_total += float(gross.sum())
        # subtype composition means
        for label,static_mask,colset in [
            ('Fish Market',subtype=='Fish Market',['fish_meat_pct']),
            ('Vegetable Market',subtype=='Vegetable Market',['organic_food_pct','green_other_pct']),
            ('Garment Factory',subtype=='Garment Factory',['textile_pct'])]:
            m=static_mask[bi]
            if m.any():
                vals=np.zeros(m.sum(),dtype=np.float64)
                for c in colset: vals += o[c][st:en][m]
                grp_sum[label+'_comp'] += float(vals.sum()); grp_n[label+'_comp'] += int(m.sum())
        # school open vs closed generation
        sm=(subtype[bi]=='School'); closed=o['school_calendar_closed'][st:en].astype(bool)
        for labl,mask in [('school_closed',sm&closed),('school_open',sm&~closed)]:
            if mask.any(): grp_sum[labl]+=float(gross[mask].sum()); grp_n[labl]+=int(mask.sum())
        # recreation weekend vs weekday
        rm=area[bi]=='Recreation'; wk=o['is_weekend'][st:en].astype(bool)
        for labl,mask in [('recreation_weekend',rm&wk),('recreation_weekday',rm&~wk)]:
            if mask.any(): grp_sum[labl]+=float(gross[mask].sum()); grp_n[labl]+=int(mask.sum())
        # density generation
        for dlab in ['High','Medium','Low']:
            mask=(dens[bi]==dlab)
            if mask.any(): grp_sum['density_'+dlab]+=float(gross[mask].sum()); grp_n['density_'+dlab]+=int(mask.sum())
        # Eid / baseline residential
        res=(area[bi]=='Residential')
        ed=o['is_eid_day'][st:en].astype(bool); ef=o['is_eid_fitr_day'][st:en].astype(bool); ram=o['is_ramadan'][st:en].astype(bool)
        for labl,mask in [('res_eid_adha',res&ed),('res_eid_fitr',res&ef),('res_regular',res&~ed&~ef&~ram)]:
            if mask.any(): grp_sum[labl]+=float(gross[mask].sum()); grp_n[labl]+=int(mask.sum())
        # Eid animal residue composition
        mask=res&ed
        if mask.any(): grp_sum['eid_animal_pct']+=float(o['animal_residue_pct'][st:en][mask].sum()); grp_n['eid_animal_pct']+=int(mask.sum())
        mask=res&~ed
        if mask.any(): grp_sum['noneid_animal_pct']+=float(o['animal_residue_pct'][st:en][mask].sum()); grp_n['noneid_animal_pct']+=int(mask.sum())
        # Friday effect among mosque-adjacent bins
        poi=np.char.decode(b['nearby_poi_type'][:])
        mm=(poi[bi]=='Mosque'); fa=o['friday_effect_active'][st:en].astype(bool); prayer=o['is_friday_prayer_window'][st:en].astype(bool)
        mask=mm&fa
        if mask.any(): grp_sum['friday_active']+=float(gross[mask].sum()); grp_n['friday_active']+=int(mask.sum())
        # compare same prayer hours on non-Friday/no effect
        hour=o['hour'][st:en]; mask=mm&(~fa)&((hour>=12)&(hour<=14))&(~o['is_eid_day'][st:en].astype(bool))
        if mask.any(): grp_sum['friday_control']+=float(gross[mask].sum()); grp_n['friday_control']+=int(mask.sum())
        # collection delay by access only when collection occurs
        coll=o['collection_event'][st:en].astype(bool); delay=o['collection_delay_minutes'][st:en]
        for alab in ['Easy','Moderate','Difficult']:
            mask=coll&(access[bi]==alab)
            if mask.any(): delay_sum[alab]+=float(delay[mask].sum()); delay_n[alab]+=int(mask.sum())

    report['rates']={k:{'count':int(v),'percent_of_rows':float(v/n*100)} for k,v in sums.items()}
    report['composition']['rows_not_summing_to_100']=bad_comp
    report['composition']['organic_family_mass_share_percent']=mass_org/mass_total*100
    report['composition']['informal_recovery_share_of_gross_percent']=recovered_total/gross_total*100
    for k in ['Fish Market_comp','Vegetable Market_comp','Garment Factory_comp','eid_animal_pct','noneid_animal_pct']:
        report['composition'][k+'_mean_percent']=grp_sum[k]/grp_n[k]
    def mean(k): return grp_sum[k]/grp_n[k]
    report['context_patterns']={
        'school_closed_mean_gross_kg_h':mean('school_closed'),'school_open_mean_gross_kg_h':mean('school_open'),'school_closed_to_open_ratio':mean('school_closed')/mean('school_open'),
        'recreation_weekend_mean_gross_kg_h':mean('recreation_weekend'),'recreation_weekday_mean_gross_kg_h':mean('recreation_weekday'),'recreation_weekend_to_weekday_ratio':mean('recreation_weekend')/mean('recreation_weekday'),
        'density_mean_gross_kg_h':{d:mean('density_'+d) for d in ['High','Medium','Low']},
        'residential_eid_adha_mean_gross_kg_h':mean('res_eid_adha'),'residential_eid_fitr_mean_gross_kg_h':mean('res_eid_fitr'),'residential_regular_mean_gross_kg_h':mean('res_regular'),
        'eid_adha_to_regular_residential_ratio':mean('res_eid_adha')/mean('res_regular'),'eid_fitr_to_regular_residential_ratio':mean('res_eid_fitr')/mean('res_regular'),
        'friday_mosque_active_mean_gross_kg_h':mean('friday_active'),'mosque_control_12_14_mean_gross_kg_h':mean('friday_control'),'friday_effect_ratio':mean('friday_active')/mean('friday_control'),
        'collection_delay_minutes_by_road_access':{a:delay_sum[a]/delay_n[a] for a in ['Easy','Moderate','Difficult']}
    }
    report['checks']={
        'exact_row_count':n==43_800_000,'exact_bin_count':nb==5000,'exact_full_year_hours_per_bin':n//nb==8760,
        'composition_sum_100_all_rows':bad_comp==0,'needs_collection_rule_consistent_all_rows':bad_label==0,
        'packet_loss_near_half_percent':0.40 <= sums['is_packet_loss']/n*100 <= 0.60,
        'sensor_anomaly_near_tenth_percent':0.08 <= sums['is_sensor_anomaly']/n*100 <= 0.12,
        'battery_maintenance_present':sums['battery_maintenance_event']>0,
        'school_closure_reduces_generation':mean('school_closed') < mean('school_open')*0.6,
        'recreation_weekend_higher':mean('recreation_weekend') > mean('recreation_weekday'),
        'fish_market_fish_meat_dominant':report['composition']['Fish Market_comp_mean_percent']>50,
        'vegetable_market_organic_green_dominant':report['composition']['Vegetable Market_comp_mean_percent']>70,
        'garments_textile_dominant':report['composition']['Garment Factory_comp_mean_percent']>45,
        'eid_adha_animal_residue_signal':report['composition']['eid_animal_pct_mean_percent']>15,
        'difficult_access_delay_higher':(delay_sum['Difficult']/delay_n['Difficult']) > (delay_sum['Easy']/delay_n['Easy']),
        'monthly_rainfall_matches_normals':report['climate']['rainfall_monthly_sums_match_targets']
    }
    # Battery min/max and public dates sanity
    bat_min=math.inf; bat_max=-math.inf
    for st in range(0,n,2_000_000):
        a=o['battery_level_percent'][st:min(st+2_000_000,n)]
        if np.isfinite(a).any(): bat_min=min(bat_min,float(np.nanmin(a))); bat_max=max(bat_max,float(np.nanmax(a)))
    report['metadata']['battery_min_percent']=bat_min; report['metadata']['battery_max_percent']=bat_max
    report['metadata']['all_checks_pass']=all(report['checks'].values())
OUT.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
