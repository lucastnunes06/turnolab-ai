"""Direct horizon features. Rows are forecast origins, not target times."""
import numpy as np
import pandas as pd
FEATURES = ['restaurant_id', 'hour_sin', 'hour_cos', 'dow_sin', 'dow_cos', 'weekend', 'open', 'promotion_known', 'lag_0', 'lag_1', 'lag_2', 'lag_48', 'rolling_4', 'rolling_12', 'rolling_48', 'seasonal_day', 'seasonal_week', 'staff', 'capacity']
START = pd.Timestamp('2026-06-01')

def make_features(events, horizon=1):
    parts = []
    for _, g in events.groupby('restaurant_id', sort=True):
        g = g.sort_values('timestamp').copy()
        g['timestamp'] = pd.to_datetime(g.timestamp)
        origin = g.timestamp
        target = origin + pd.Timedelta(minutes=30 * horizon)
        hour = target.dt.hour + target.dt.minute / 60
        f = pd.DataFrame(index=g.index)
        f['restaurant_id'] = g.restaurant_id
        f['origin'] = origin
        f['target'] = target
        f['source_max'] = origin
        f['hour_sin'], f['hour_cos'] = (np.sin(hour * 2 * np.pi / 24), np.cos(hour * 2 * np.pi / 24))
        f['dow_sin'], f['dow_cos'] = (np.sin(target.dt.dayofweek * 2 * np.pi / 7), np.cos(target.dt.dayofweek * 2 * np.pi / 7))
        f['weekend'] = (target.dt.dayofweek >= 4).astype(int)
        f['open'] = ((hour >= 10) & (hour < 23.5)).astype(int)
        f['promotion_known'] = g.promotion.shift(-horizon)
        for lag in [0, 1, 2, 48]:
            f[f'lag_{lag}'] = g.orders.shift(lag)
        for w in [4, 12, 48]:
            f[f'rolling_{w}'] = g.orders.rolling(w, min_periods=w).mean()
        f['seasonal_day'] = g.orders.shift(48 - horizon)
        f['seasonal_week'] = (g.orders.shift(336 - horizon) + g.orders.shift(672 - horizon)) / 2
        f['staff'], f['capacity'] = (g.staff, g.capacity)
        f['y'] = g.orders.shift(-horizon)
        f['day'] = (origin - START).dt.total_seconds() / 86400
        f['peak'] = ((hour >= 18) & (hour <= 21.5)).astype(int)
        f['hour'] = hour
        parts.append(f)
    return pd.concat(parts).sort_values(['origin', 'restaurant_id']).reset_index(drop=True)

def partitions(f):
    train = f.target < START + pd.Timedelta(days=54)
    val = (f.origin >= START + pd.Timedelta(days=54)) & (f.target < START + pd.Timedelta(days=65))
    cal = (f.origin >= START + pd.Timedelta(days=65)) & (f.target < START + pd.Timedelta(days=72))
    test = f.origin >= START + pd.Timedelta(days=72)
    return {k: f.loc[m].dropna(subset=FEATURES + ['y']).copy() for k, m in [('train', train), ('validation', val), ('calibration', cal), ('test', test)]}
