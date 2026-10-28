"""Fixed-seed synthetic data. No real restaurants, customers or iFood data."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from backend.app.config import DATA, REPORTS
from backend.app.db import migrate, session
SEED = 42
TABLES = ('restaurants', 'products', 'ingredients', 'recipes', 'order_events', 'inventory_snapshots')
COLUMNS = {'restaurants': {'id', 'name', 'cuisine', 'city', 'staff', 'kitchen_capacity'}, 'products': {'id', 'name', 'category', 'mix_weight'}, 'ingredients': {'id', 'name', 'unit', 'safety_stock'}, 'recipes': {'product_id', 'ingredient_id', 'quantity'}, 'order_events': {'id', 'restaurant_id', 'timestamp', 'orders', 'cancellations', 'prep_minutes', 'promotion', 'staff', 'capacity'}, 'inventory_snapshots': {'id', 'restaurant_id', 'ingredient_id', 'timestamp', 'on_hand', 'supply', 'lead_intervals', 'unit'}}

def generate(seed=SEED, days=90, restaurants=20):
    rng = np.random.default_rng(seed)
    names = ['Casa do Grão', 'Brasa & Alecrim', 'Miso da Vila', 'Verde Mesa', 'Forno do Bairro']
    cities = ['São Paulo', 'Recife', 'Belo Horizonte', 'Curitiba']
    rest = pd.DataFrame([dict(id=i, name=f"{names[(i - 1) % 5]}{('' if i <= 5 else f' · {i:02}')}", cuisine=['Brasileira', 'Grelhados', 'Asiática', 'Natural', 'Italiana'][(i - 1) % 5], city=cities[(i - 1) % 4], staff=int(rng.integers(3, 7)), kitchen_capacity=round(float(rng.uniform(48, 80)), 2)) for i in range(1, restaurants + 1)])
    products = pd.DataFrame([dict(id=1, name='Bowl da casa', category='Pratos', mix_weight=0.45), dict(id=2, name='Sanduíche de frango', category='Lanches', mix_weight=0.35), dict(id=3, name='Salada de grãos', category='Saladas', mix_weight=0.2)])
    ingredients = pd.DataFrame([dict(id=1, name='Frango', unit='kg', safety_stock=2.0), dict(id=2, name='Arroz', unit='kg', safety_stock=1.5), dict(id=3, name='Folhas', unit='kg', safety_stock=0.8), dict(id=4, name='Pão', unit='un', safety_stock=10.0)])
    recipes = pd.DataFrame([dict(product_id=1, ingredient_id=1, quantity=0.18), dict(product_id=1, ingredient_id=2, quantity=0.15), dict(product_id=2, ingredient_id=1, quantity=0.12), dict(product_id=2, ingredient_id=4, quantity=1.0), dict(product_id=3, ingredient_id=2, quantity=0.1), dict(product_id=3, ingredient_id=3, quantity=0.12)])
    times = pd.date_range('2026-06-01', periods=days * 48, freq='30min')
    frames, stocks = ([], [])
    rates = recipes.merge(products[['id', 'mix_weight']], left_on='product_id', right_on='id')
    rates['rate'] = rates.quantity * rates.mix_weight
    rates = rates.groupby('ingredient_id').rate.sum().to_dict()
    for row in rest.itertuples():
        n = len(times)
        hour = times.hour.to_numpy() + times.minute.to_numpy() / 60
        dow = times.dayofweek.to_numpy()
        day = np.arange(n) // 48
        promo_days = rng.random(days) < 0.22
        promo = promo_days[day] * ((hour >= 17) & (hour < 22)) * 0.3
        meal = 2 + 19 * np.exp(-((hour - 12.5) / 1.5) ** 2) + 30 * np.exp(-((hour - 19.5) / 1.8) ** 2)
        opened = (hour >= 10) & (hour < 23.5)
        daily_shock = rng.lognormal(-0.025, 0.22, days)[day]
        atypical = (rng.random(days) < 0.04)[day] * rng.uniform(1.4, 2.2, days)[day]
        behavior_shift = 1 + (day >= 64) * rng.uniform(-0.18, 0.22)
        mean = meal * (1 + 0.23 * (dow >= 4)) * (1 + promo * 1.6) * daily_shock * (1 + atypical) * behavior_shift * rng.uniform(0.75, 1.45) * opened
        orders = rng.poisson(rng.gamma(18, np.maximum(mean, 0.001) / 18)) * opened
        staffing = np.maximum(1, row.staff - (rng.random(n) < 0.06).astype(int))
        capacity = np.minimum(row.kitchen_capacity, staffing * 12) * rng.uniform(0.88, 1.03, n)
        cancel_p = np.clip(0.015 + np.maximum(0, orders - capacity) / np.maximum(orders, 1) * 0.3, 0, 0.5)
        frames.append(pd.DataFrame(dict(restaurant_id=row.id, timestamp=times, orders=orders, cancellations=rng.binomial(orders, cancel_p), prep_minutes=np.round((9 + orders / np.maximum(capacity, 1) * 12 + rng.uniform(0, 5, n)) * opened, 2), promotion=promo, staff=staffing, capacity=np.round(capacity, 2))))
        for pos in range(8, n, 4):
            trailing = float(orders[max(0, pos - 48):pos + 1].mean())
            for ing in ingredients.itertuples():
                lead = int(rng.choice([2, 4, 6]))
                expected = max(3.0, trailing) * lead * rates[ing.id]
                stocks.append(dict(restaurant_id=row.id, ingredient_id=ing.id, timestamp=times[pos], on_hand=round(max(0.01, expected * rng.uniform(0.25, 2.8) + ing.safety_stock), 3), supply=round(expected * rng.choice([0.0, 0.4, 0.8]), 3), lead_intervals=lead, unit=ing.unit))
    orders = pd.concat(frames, ignore_index=True)
    orders.insert(0, 'id', np.arange(1, len(orders) + 1))
    inventory = pd.DataFrame(stocks)
    inventory.insert(0, 'id', np.arange(1, len(inventory) + 1))
    return dict(restaurants=rest, products=products, ingredients=ingredients, recipes=recipes, order_events=orders, inventory_snapshots=inventory)

def validate(tables):
    errors = []
    if set(tables) != set(TABLES):
        return dict(valid=False, errors=['Invalid table contract'], rows={})
    for name, table in tables.items():
        if set(table.columns) != COLUMNS[name]:
            errors.append(f'{name}: invalid column contract')
    if errors:
        return dict(valid=False, errors=errors, rows={k: len(v) for k, v in tables.items()})
    for name, table in tables.items():
        for col in ['id', 'product_id', 'ingredient_id', 'restaurant_id']:
            if col in table:
                values = pd.to_numeric(table[col], errors='coerce')
                if values.isna().any() or (values <= 0).any() or (values % 1 != 0).any():
                    errors.append(f'{name}: invalid {col}')
        for col in ['orders', 'cancellations', 'staff', 'lead_intervals']:
            if col in table and (table[col].dropna() % 1 != 0).any():
                errors.append(f'{name}: nonintegral {col}')
        if table.isna().any().any():
            errors.append(f'{name}: missing values')
        if 'id' in table and table.id.duplicated().any():
            errors.append(f'{name}: duplicate id')
        for col in ['orders', 'cancellations', 'prep_minutes', 'on_hand', 'supply', 'quantity']:
            if col in table and ((table[col] < 0) | ~np.isfinite(table[col])).any():
                errors.append(f'{name}: invalid {col}')
        if 'restaurant_id' in table and (not table.restaurant_id.isin(tables['restaurants'].id).all()):
            errors.append(f'{name}: foreign restaurant id')
        if 'ingredient_id' in table and (not table.ingredient_id.isin(tables['ingredients'].id).all()):
            errors.append(f'{name}: foreign ingredient id')
        if 'product_id' in table and (not table.product_id.isin(tables['products'].id).all()):
            errors.append(f'{name}: foreign product id')
        if 'timestamp' in table:
            ts = pd.to_datetime(table.timestamp, errors='coerce')
            if ts.isna().any() or ((ts.dt.minute % 30 != 0) | (ts.dt.second != 0)).any():
                errors.append(f'{name}: inconsistent timestamps')
            keys = ['restaurant_id'] + (['ingredient_id'] if 'ingredient_id' in table else [])
            for _, group in table.groupby(keys):
                if not pd.to_datetime(group.timestamp, errors='coerce').is_monotonic_increasing:
                    errors.append(f'{name}: out of order')
                    break
            if table.duplicated(keys + ['timestamp']).any():
                errors.append(f'{name}: duplicate timestamp')
            if name == 'order_events':
                for _, group in table.groupby('restaurant_id'):
                    if not (pd.to_datetime(group.timestamp, errors='coerce').diff().dropna() == pd.Timedelta(minutes=30)).all():
                        errors.append('order_events: gap in timeline')
                        break
    inventory = tables['inventory_snapshots'].merge(tables['ingredients'][['id', 'unit']], left_on='ingredient_id', right_on='id', suffixes=('', '_expected'))
    if (inventory.unit != inventory.unit_expected).any():
        errors.append('inventory_snapshots: inconsistent units')
    if tables['recipes'].duplicated(['product_id', 'ingredient_id']).any():
        errors.append('recipes: duplicate key')
    if not np.isclose(tables['products'].mix_weight.sum(), 1.0):
        errors.append('products: mix does not sum to one')
    if (tables['ingredients'].safety_stock < 0).any():
        errors.append('ingredients: negative reserve')
    events = tables['order_events']
    if (events.cancellations > events.orders).any():
        errors.append('order_events: cancellations exceed orders')
    if not events.promotion.between(0, 1).all() or (events.staff <= 0).any() or (events.capacity <= 0).any():
        errors.append('order_events: invalid operating constraints')
    if (tables['inventory_snapshots'].lead_intervals <= 0).any():
        errors.append('inventory_snapshots: invalid lead time')
    return dict(valid=not errors, errors=errors, rows={k: len(v) for k, v in tables.items()}, seed=SEED, temporal_policy='Features must have source_timestamp <= origin; targets are separate.')

def save(tables, directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name, table in tables.items():
        path = directory / f'{name}.csv'
        table.to_csv(path, index=False)
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    report = validate(tables)
    report['sha256'] = hashes
    (REPORTS / 'data_quality.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report

def ingest(tables, session):
    report = validate(tables)
    if not report['valid']:
        raise ValueError(report['errors'])
    if session.execute('SELECT id FROM restaurants LIMIT 1').fetchone() is not None:
        raise ValueError('Database already populated; refusing to overwrite state')
    for name in TABLES:
        frame = tables[name].copy()
        if 'timestamp' in frame:
            frame['timestamp'] = pd.to_datetime(frame.timestamp).dt.strftime('%Y-%m-%dT%H:%M:%S')
        records = list(frame.itertuples(index=False, name=None))
        columns = ','.join(frame.columns)
        placeholders = ','.join(('?' for _ in frame.columns))
        for start in range(0, len(records), 2000):
            session.executemany(f'INSERT INTO {name} ({columns}) VALUES ({placeholders})', records[start:start + 2000])
    session.commit()
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=SEED)
    args = parser.parse_args()
    tables = generate(args.seed)
    report = save(tables, DATA / 'synthetic')
    migrate()
    with session() as db:
        ingest(tables, db)
    print(json.dumps(report, indent=2))
if __name__ == '__main__':
    main()
