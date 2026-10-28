CREATE TABLE restaurants (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, cuisine TEXT NOT NULL, city TEXT NOT NULL,
 staff INTEGER NOT NULL CHECK(staff>0), kitchen_capacity REAL NOT NULL CHECK(kitchen_capacity>0)
);
CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
 mix_weight REAL NOT NULL CHECK(mix_weight>0 AND mix_weight<=1));
CREATE TABLE ingredients (id INTEGER PRIMARY KEY, name TEXT NOT NULL,
 unit TEXT NOT NULL CHECK(unit IN ('kg','un')), safety_stock REAL NOT NULL CHECK(safety_stock>=0));
CREATE TABLE recipes (product_id INTEGER REFERENCES products(id), ingredient_id INTEGER REFERENCES ingredients(id),
 quantity REAL NOT NULL CHECK(quantity>0), PRIMARY KEY(product_id,ingredient_id));
CREATE TABLE order_events (
 id INTEGER PRIMARY KEY, restaurant_id INTEGER NOT NULL REFERENCES restaurants(id), timestamp TEXT NOT NULL,
 orders INTEGER NOT NULL CHECK(orders>=0), cancellations INTEGER NOT NULL CHECK(cancellations>=0 AND cancellations<=orders),
 prep_minutes REAL NOT NULL CHECK(prep_minutes>=0), promotion REAL NOT NULL CHECK(promotion BETWEEN 0 AND 1),
 staff INTEGER NOT NULL CHECK(staff>0), capacity REAL NOT NULL CHECK(capacity>0), UNIQUE(restaurant_id,timestamp)
);
CREATE TABLE inventory_snapshots (
 id INTEGER PRIMARY KEY, restaurant_id INTEGER NOT NULL REFERENCES restaurants(id),
 ingredient_id INTEGER NOT NULL REFERENCES ingredients(id), timestamp TEXT NOT NULL,
 on_hand REAL NOT NULL CHECK(on_hand>=0), supply REAL NOT NULL CHECK(supply>=0),
 lead_intervals INTEGER NOT NULL CHECK(lead_intervals>0), unit TEXT NOT NULL CHECK(unit IN ('kg','un')),
 UNIQUE(restaurant_id,ingredient_id,timestamp)
);
CREATE TABLE model_versions (id TEXT PRIMARY KEY, kind TEXT NOT NULL, status TEXT NOT NULL,
 metrics TEXT NOT NULL, artifact_hash TEXT NOT NULL);
CREATE TABLE demand_forecasts (
 id INTEGER PRIMARY KEY, restaurant_id INTEGER NOT NULL REFERENCES restaurants(id), origin TEXT NOT NULL,
 target TEXT NOT NULL, model_id TEXT NOT NULL REFERENCES model_versions(id), point REAL NOT NULL CHECK(point>=0),
 lower REAL NOT NULL CHECK(lower>=0), upper REAL NOT NULL CHECK(upper>=lower), CHECK(target>origin),
 UNIQUE(restaurant_id,origin,target,model_id)
);
CREATE TABLE simulation_runs (id TEXT PRIMARY KEY, restaurant_id INTEGER NOT NULL REFERENCES restaurants(id),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, model_id TEXT NOT NULL REFERENCES model_versions(id),
 origin TEXT NOT NULL, inputs TEXT NOT NULL, results TEXT NOT NULL);
CREATE TABLE agent_conversations (id TEXT PRIMARY KEY, restaurant_id INTEGER NOT NULL REFERENCES restaurants(id),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, question TEXT NOT NULL, response TEXT NOT NULL);
CREATE TABLE action_proposals (id TEXT PRIMARY KEY, restaurant_id INTEGER NOT NULL REFERENCES restaurants(id),
 simulation_id TEXT NOT NULL REFERENCES simulation_runs(id), title TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
 created_by TEXT NOT NULL, decided_by TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, restaurant_id INTEGER NOT NULL REFERENCES restaurants(id),
 actor TEXT NOT NULL, event TEXT NOT NULL, entity_id TEXT NOT NULL, details TEXT NOT NULL,
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TRIGGER audit_no_update BEFORE UPDATE ON audit_logs BEGIN SELECT RAISE(ABORT,'append-only audit'); END;
CREATE TRIGGER audit_no_delete BEFORE DELETE ON audit_logs BEGIN SELECT RAISE(ABORT,'append-only audit'); END;
CREATE TABLE inference_aggregates (id INTEGER PRIMARY KEY, restaurant_id INTEGER NOT NULL REFERENCES restaurants(id),
 model_id TEXT NOT NULL, count INTEGER NOT NULL, total_ms REAL NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE experiment_runs (id TEXT PRIMARY KEY, kind TEXT NOT NULL, params TEXT NOT NULL, metrics TEXT NOT NULL,
 artifact TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE operational_alerts (id TEXT PRIMARY KEY, restaurant_id INTEGER NOT NULL REFERENCES restaurants(id),
 payload TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX events_rest_time ON order_events(restaurant_id,timestamp);
CREATE INDEX inventory_rest_time ON inventory_snapshots(restaurant_id,timestamp);
CREATE INDEX actions_rest ON action_proposals(restaurant_id);
CREATE INDEX audit_rest ON audit_logs(restaurant_id);
