"""Conservation-based half-hour fluid model. All costs are hypothetical BRL."""
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, model_validator
Nonnegative = Annotated[float, Field(ge=0, le=100000, allow_inf_nan=False)]

class Scenario(BaseModel):
    model_config = ConfigDict(extra='forbid')
    staff: int = Field(ge=1, le=30)
    kitchen_capacity: float = Field(gt=0, le=1000, allow_inf_nan=False)
    demand: list[Nonnegative] = Field(min_length=1, max_length=12)
    promotion: float = Field(0, ge=0, le=1, allow_inf_nan=False)
    stock_orders: Nonnegative = 1000
    replenishment_orders: Nonnegative = 0
    replenishment_after: int = Field(2, ge=1, le=24)
    wage_per_hour: Nonnegative = 24
    backlog_cost: Nonnegative = 8
    stockout_cost: Nonnegative = 15
    initial_backlog: Nonnegative = 0

    @model_validator(mode='after')
    def valid_total(self):
        if sum(self.demand) > 100000:
            raise ValueError('Scenario too large')
        return self

def simulate(s: Scenario):
    capacity = min(s.kitchen_capacity, s.staff * 12.0)
    queue = s.initial_backlog
    stock = s.stock_orders
    backlog_area = 0.0
    stockouts = 0.0
    processed = 0.0
    timeline = []
    for i, expected in enumerate(s.demand):
        arrivals = expected * (1 + s.promotion * 1.6)
        if i >= s.replenishment_after and i == s.replenishment_after:
            stock += s.replenishment_orders
        queue += arrivals
        could_process = min(queue, capacity)
        completed = min(could_process, stock)
        unmet_stock = could_process - completed
        stockouts += unmet_stock
        queue -= completed
        stock -= completed
        processed += completed
        backlog_area += queue
        timeline.append(dict(interval=i + 1, arrivals=arrivals, processed=completed, backlog=queue, stock_remaining=stock))
    labor = s.staff * s.wage_per_hour * len(s.demand) * 0.5
    cost = labor + backlog_area * s.backlog_cost + stockouts * s.stockout_cost
    return dict(backlog=queue, processed=processed, capacity_per_interval=capacity, available_capacity=capacity * len(s.demand), stockout_order_intervals=stockouts, stock_insufficient=stockouts > 0, labor_cost=labor, total_cost=cost, backlog_area=backlog_area, timeline=timeline, assumptions=dict(productivity_orders_per_person=12, interval_minutes=30, queue_model='fluid, no abandonment', currency='BRL hypothetical', version='fluid-v1'))

def compare(current: Scenario, alternative: Scenario):
    a, b = (simulate(current), simulate(alternative))
    sensitivity = []
    for factor in [0.8, 1.0, 1.2]:
        s = alternative.model_copy(update={'demand': [x * factor for x in alternative.demand]})
        sensitivity.append(dict(demand_multiplier=factor, **{k: v for k, v in simulate(s).items() if k in ['backlog', 'total_cost']}))
    return dict(current=a, alternative=b, delta=dict(backlog=b['backlog'] - a['backlog'], cost=b['total_cost'] - a['total_cost'], processed=b['processed'] - a['processed']), sensitivity=sensitivity, warning='Operational hypothesis, not a causal estimate. Promotion response is an assumed coefficient.')
