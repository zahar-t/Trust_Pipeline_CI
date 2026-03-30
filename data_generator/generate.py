"""Synthetic EU E-Commerce Data Generator.

Generates realistic e-commerce data with:
- EU-specific consent flags (GDPR compliance dimension)
- Multi-currency transactions (EUR, GBP, SEK, PLN)
- Realistic seasonal patterns and conversion funnels
- Intentional data quality issues (for testing pipeline robustness)
- Configurable scale (default: 12 months, ~500K events)

Usage:
    python generate.py --target duckdb --output output/
    python generate.py --target bigquery --project my-gcp-project --dataset raw_ecommerce
"""

import argparse
import csv
import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_CONFIG: dict[str, Any] = {
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "n_customers": 12_000,
    "n_products": 250,
    "avg_orders_per_customer": 3.2,
    "consent_rates": {
        "full": 0.42,
        "analytics_only": 0.28,
        "minimal": 0.30,
    },
    "countries": {
        "PT": {"weight": 0.25, "currency": "EUR", "vat_rate": 0.23},
        "DE": {"weight": 0.20, "currency": "EUR", "vat_rate": 0.19},
        "FR": {"weight": 0.18, "currency": "EUR", "vat_rate": 0.20},
        "NL": {"weight": 0.12, "currency": "EUR", "vat_rate": 0.21},
        "GB": {"weight": 0.10, "currency": "GBP", "vat_rate": 0.20},
        "SE": {"weight": 0.08, "currency": "SEK", "vat_rate": 0.25},
        "PL": {"weight": 0.07, "currency": "PLN", "vat_rate": 0.23},
    },
    "product_categories": [
        "Electronics",
        "Clothing",
        "Home & Garden",
        "Sports",
        "Books",
        "Beauty",
        "Food & Drink",
    ],
    "data_quality_issues": {
        "null_email_rate": 0.03,
        "duplicate_order_rate": 0.008,
        "future_date_rate": 0.002,
        "negative_amount_rate": 0.001,
        "currency_mismatch_rate": 0.005,
    },
}

# FX rates to EUR (approximate, for realism)
FX_TO_EUR: dict[str, float] = {
    "EUR": 1.0,
    "GBP": 1.17,
    "SEK": 0.088,
    "PLN": 0.23,
}

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class Customer:
    """A synthetic e-commerce customer with GDPR consent metadata."""

    customer_id: str
    email: str | None
    country_code: str
    currency: str
    consent_level: str  # full | analytics_only | minimal
    created_at: datetime
    is_active: bool = True


@dataclass
class Product:
    """A product in the catalogue with a base EUR price."""

    product_id: str
    name: str
    category: str
    base_price_eur: float
    created_at: datetime


@dataclass
class Order:
    """A customer order with multi-currency amounts."""

    order_id: str
    customer_id: str
    order_date: datetime
    status: str  # completed | refunded | cancelled
    currency: str
    total_amount: float
    total_amount_eur: float
    consent_level_at_order: str
    country_code: str


@dataclass
class OrderItem:
    """A line item within an order."""

    order_item_id: str
    order_id: str
    product_id: str
    quantity: int
    unit_price: float
    unit_price_eur: float


@dataclass
class Event:
    """A behavioural event in the conversion funnel."""

    event_id: str
    customer_id: str
    event_type: str  # page_view | add_to_cart | checkout_start | purchase | refund
    event_timestamp: datetime
    session_id: str
    consent_level: str
    properties: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


class ECommerceGenerator:
    """Generate a full synthetic e-commerce dataset."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize generator with the given configuration."""
        self.config = config
        self.start = datetime.fromisoformat(config["start_date"])
        self.end = datetime.fromisoformat(config["end_date"])
        self.customers: list[Customer] = []
        self.products: list[Product] = []
        self.orders: list[Order] = []
        self.order_items: list[OrderItem] = []
        self.events: list[Event] = []
        random.seed(42)  # reproducible

    # --- helpers ---
    def _pick_country(self) -> tuple[str, str]:
        """Pick a country code and its currency using configured weights."""
        countries = self.config["countries"]
        codes = list(countries.keys())
        weights = [countries[c]["weight"] for c in codes]
        code = random.choices(codes, weights=weights, k=1)[0]
        return code, countries[code]["currency"]

    def _pick_consent(self) -> str:
        """Pick a GDPR consent level using configured rates."""
        rates = self.config["consent_rates"]
        result: str = random.choices(list(rates.keys()), weights=list(rates.values()), k=1)[0]
        return result

    def _random_dt(self, after: datetime | None = None) -> datetime:
        """Return a random datetime within the generation window."""
        start = after or self.start
        delta = (self.end - start).total_seconds()
        offset = random.random() * delta
        return start + timedelta(seconds=offset)

    def _seasonal_weight(self, dt: datetime) -> float:
        """Boost Q4 (Black Friday / Christmas) and suppress Jan-Feb."""
        month = dt.month
        if month in (11, 12):
            return 1.6
        elif month in (1, 2):
            return 0.7
        elif month in (6, 7):
            return 1.15  # summer sales
        return 1.0

    # --- generators ---
    def generate_products(self) -> None:
        """Generate the product catalogue."""
        categories = self.config["product_categories"]
        for i in range(self.config["n_products"]):
            cat = random.choice(categories)
            price = round(random.uniform(5, 500), 2)
            self.products.append(
                Product(
                    product_id=f"PROD-{i + 1:04d}",
                    name=f"{cat} Item {i + 1}",
                    category=cat,
                    base_price_eur=price,
                    created_at=self._random_dt(),
                )
            )

    def generate_customers(self) -> None:
        """Generate customers with optional data-quality issues."""
        dq = self.config["data_quality_issues"]
        for i in range(self.config["n_customers"]):
            country, currency = self._pick_country()
            email: str | None = f"customer_{i + 1}@example.com"
            if random.random() < dq["null_email_rate"]:
                email = None  # intentional data quality issue
            self.customers.append(
                Customer(
                    customer_id=f"CUST-{i + 1:06d}",
                    email=email,
                    country_code=country,
                    currency=currency,
                    consent_level=self._pick_consent(),
                    created_at=self._random_dt(),
                )
            )

    @staticmethod
    def _pick_order_status() -> str:
        """Pick an order status using weighted probabilities."""
        status_roll = random.random()
        if status_roll < 0.85:
            return "completed"
        if status_roll < 0.93:
            return "refunded"
        return "cancelled"

    def _build_order_items(
        self, order_id: str, currency: str, products: list[Product]
    ) -> tuple[list[OrderItem], float]:
        """Build line items for an order and return them with the total."""
        items: list[OrderItem] = []
        total = 0.0
        fx = FX_TO_EUR.get(currency, 1.0)
        for prod in products:
            qty = random.choices([1, 2, 3], weights=[0.7, 0.22, 0.08])[0]
            unit_price_local = round(prod.base_price_eur / fx, 2)
            items.append(
                OrderItem(
                    order_item_id=f"ITEM-{uuid.uuid4().hex[:10].upper()}",
                    order_id=order_id,
                    product_id=prod.product_id,
                    quantity=qty,
                    unit_price=unit_price_local,
                    unit_price_eur=prod.base_price_eur,
                )
            )
            total += unit_price_local * qty
        return items, total

    def generate_orders(self) -> None:
        """Generate orders with seasonal weighting and data-quality issues."""
        dq = self.config["data_quality_issues"]
        avg_orders = self.config["avg_orders_per_customer"]

        for customer in self.customers:
            n_orders = max(0, int(random.gauss(avg_orders, avg_orders * 0.6)))
            for _ in range(n_orders):
                order_date = self._random_dt(after=customer.created_at)

                if random.random() > self._seasonal_weight(order_date):
                    continue

                status = self._pick_order_status()
                n_items = random.choices([1, 2, 3, 4], weights=[0.55, 0.28, 0.12, 0.05])[0]
                selected_products = random.sample(self.products, min(n_items, len(self.products)))
                order_id = f"ORD-{uuid.uuid4().hex[:10].upper()}"

                items, total = self._build_order_items(order_id, customer.currency, selected_products)

                # --- Intentional data quality issues ---
                currency = customer.currency
                if random.random() < dq["currency_mismatch_rate"]:
                    currency = random.choice(["EUR", "GBP", "SEK", "PLN"])
                if random.random() < dq["negative_amount_rate"]:
                    total = -abs(total)
                if random.random() < dq["future_date_rate"]:
                    order_date = self.end + timedelta(days=random.randint(1, 60))

                total_eur = round(total * FX_TO_EUR.get(currency, 1.0), 2)

                order = Order(
                    order_id=order_id,
                    customer_id=customer.customer_id,
                    order_date=order_date,
                    status=status,
                    currency=currency,
                    total_amount=round(total, 2),
                    total_amount_eur=total_eur,
                    consent_level_at_order=customer.consent_level,
                    country_code=customer.country_code,
                )

                if random.random() < dq["duplicate_order_rate"]:
                    self.orders.append(order)
                    self.order_items.extend(items)

                self.orders.append(order)
                self.order_items.extend(items)

    @staticmethod
    def _is_suppressed_by_consent(consent: str, event_type: str) -> bool:
        """Check if a minimal-consent user's event should be suppressed."""
        if consent != "minimal":
            return False
        if event_type not in ("page_view", "add_to_cart"):
            return False
        return random.random() < 0.70

    def _build_funnel_events(self, order: Order, customer: Customer, session_id: str) -> list[Event]:
        """Build funnel events for a single order."""
        consent = order.consent_level_at_order
        base_ts = order.order_date - timedelta(minutes=random.randint(5, 120))
        funnel_steps: list[tuple[str, float]] = [
            ("page_view", 1.0),
            ("add_to_cart", 0.65),
            ("checkout_start", 0.45),
            ("purchase", 0.35 if order.status == "completed" else 0.0),
        ]
        events: list[Event] = []
        for i, (event_type, prob) in enumerate(funnel_steps):
            if random.random() > prob:
                break
            if self._is_suppressed_by_consent(consent, event_type):
                continue
            ts = base_ts + timedelta(minutes=i * random.randint(1, 15))
            events.append(
                Event(
                    event_id=f"EVT-{uuid.uuid4().hex[:12]}",
                    customer_id=customer.customer_id,
                    event_type=event_type,
                    event_timestamp=ts,
                    session_id=session_id,
                    consent_level=consent,
                )
            )
        return events

    def generate_events(self) -> None:
        """Generate funnel events. Only tracked if consent allows."""
        customer_map = {c.customer_id: c for c in self.customers}
        for order in self.orders:
            customer = customer_map.get(order.customer_id)
            if not customer:
                continue

            session_id = f"SESS-{uuid.uuid4().hex[:12]}"
            self.events.extend(self._build_funnel_events(order, customer, session_id))

            # Refund event
            if order.status == "refunded":
                refund_ts = order.order_date + timedelta(days=random.randint(1, 30))
                self.events.append(
                    Event(
                        event_id=f"EVT-{uuid.uuid4().hex[:12]}",
                        customer_id=customer.customer_id,
                        event_type="refund",
                        event_timestamp=refund_ts,
                        session_id=session_id,
                        consent_level=order.consent_level_at_order,
                    )
                )

    def generate_all(self) -> None:
        """Run all generators in sequence and print progress."""
        print("Generating products...")
        self.generate_products()
        print(f"  -> {len(self.products)} products")

        print("Generating customers...")
        self.generate_customers()
        print(f"  -> {len(self.customers)} customers")

        print("Generating orders...")
        self.generate_orders()
        print(f"  -> {len(self.orders)} orders, {len(self.order_items)} line items")

        print("Generating events...")
        self.generate_events()
        print(f"  -> {len(self.events)} events")

    # --- output ---
    def _write_csv(self, path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
        """Write a list of row dicts to a CSV file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

    def write_to_csv(self, output_dir: str) -> None:
        """Write all generated data to CSV files in the given directory."""
        out = Path(output_dir)
        print(f"\nWriting CSV files to {out}/")

        self._write_csv(
            out / "raw_customers.csv",
            [
                {
                    "customer_id": c.customer_id,
                    "email": c.email or "",
                    "country_code": c.country_code,
                    "currency": c.currency,
                    "consent_level": c.consent_level,
                    "created_at": c.created_at.isoformat(),
                    "is_active": c.is_active,
                }
                for c in self.customers
            ],
            [
                "customer_id",
                "email",
                "country_code",
                "currency",
                "consent_level",
                "created_at",
                "is_active",
            ],
        )

        self._write_csv(
            out / "raw_products.csv",
            [
                {
                    "product_id": p.product_id,
                    "name": p.name,
                    "category": p.category,
                    "base_price_eur": p.base_price_eur,
                    "created_at": p.created_at.isoformat(),
                }
                for p in self.products
            ],
            ["product_id", "name", "category", "base_price_eur", "created_at"],
        )

        self._write_csv(
            out / "raw_orders.csv",
            [
                {
                    "order_id": o.order_id,
                    "customer_id": o.customer_id,
                    "order_date": o.order_date.isoformat(),
                    "status": o.status,
                    "currency": o.currency,
                    "total_amount": o.total_amount,
                    "total_amount_eur": o.total_amount_eur,
                    "consent_level_at_order": o.consent_level_at_order,
                    "country_code": o.country_code,
                }
                for o in self.orders
            ],
            [
                "order_id",
                "customer_id",
                "order_date",
                "status",
                "currency",
                "total_amount",
                "total_amount_eur",
                "consent_level_at_order",
                "country_code",
            ],
        )

        self._write_csv(
            out / "raw_order_items.csv",
            [
                {
                    "order_item_id": i.order_item_id,
                    "order_id": i.order_id,
                    "product_id": i.product_id,
                    "quantity": i.quantity,
                    "unit_price": i.unit_price,
                    "unit_price_eur": i.unit_price_eur,
                }
                for i in self.order_items
            ],
            [
                "order_item_id",
                "order_id",
                "product_id",
                "quantity",
                "unit_price",
                "unit_price_eur",
            ],
        )

        self._write_csv(
            out / "raw_events.csv",
            [
                {
                    "event_id": e.event_id,
                    "customer_id": e.customer_id,
                    "event_type": e.event_type,
                    "event_timestamp": e.event_timestamp.isoformat(),
                    "session_id": e.session_id,
                    "consent_level": e.consent_level,
                }
                for e in self.events
            ],
            [
                "event_id",
                "customer_id",
                "event_type",
                "event_timestamp",
                "session_id",
                "consent_level",
            ],
        )

        # Summary
        print(f"  raw_customers.csv ({len(self.customers)} rows)")
        print(f"  raw_products.csv ({len(self.products)} rows)")
        print(f"  raw_orders.csv ({len(self.orders)} rows)")
        print(f"  raw_order_items.csv ({len(self.order_items)} rows)")
        print(f"  raw_events.csv ({len(self.events)} rows)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point: parse CLI args and generate synthetic data."""
    parser = argparse.ArgumentParser(description="Generate synthetic EU e-commerce data")
    parser.add_argument("--target", choices=["duckdb", "bigquery"], default="duckdb")
    parser.add_argument("--output", default="output/", help="Output directory for CSV files")
    parser.add_argument("--config", default=None, help="Path to custom config YAML")
    parser.add_argument("--project", default=None, help="GCP project (BigQuery target)")
    parser.add_argument("--dataset", default=None, help="BigQuery dataset name")
    args = parser.parse_args()

    # Load config
    config = DEFAULT_CONFIG.copy()
    if args.config:
        with open(args.config) as f:
            overrides = yaml.safe_load(f)
            config.update(overrides)

    gen = ECommerceGenerator(config)
    gen.generate_all()

    if args.target == "duckdb":
        gen.write_to_csv(args.output)
        print("\nDone! Load these CSVs as dbt seeds or use dbt-duckdb's external sources.")
    elif args.target == "bigquery":
        gen.write_to_csv(args.output)
        print("\nCSV files written. Load to BigQuery with:")
        print(
            f"  bq load --source_format=CSV --autodetect "
            f"{args.project}:{args.dataset}.raw_customers "
            f"{args.output}/raw_customers.csv"
        )
        print("  (repeat for each table)")


if __name__ == "__main__":
    main()
