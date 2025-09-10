# Loomi

<div align="center">
  <h3>Build applications the way they should be built.</h3>
  <p><em>Loomi isn't another framework. It's a paradigm shift. A new way to build applications where state, control flow, and infrastructure become one seamless experience.</em></p>
</div>

---

## The Paradigm

### 🌳 **State** - Your Memory, Perfected

Every piece of data in your application lives in a unified, observable tree structure:

```python
# ACID transactions with automatic rollback
with tree.at("users").with_dict_view() as users:
    users.set("alice", {"email": "alice@example.com"})
    
    # Nested operations are natural
    alice = users.dict_view("alice")
    alice.set("preferences", {"theme": "dark"})
    
# Lists and queues work the same way
with tree.at("tasks").with_list_view() as tasks:
    tasks.append("Build something amazing")
# Transaction commits automatically - ACID guaranteed
```

**Features:**
- **ACID compliance** - transactions that just work
- **Reactive by design** - observe any path for changes
- **Multiple backends** - memory, file, LMDB persistence
- **Type-safe navigation** - structured paths with full IDE support

### ⚡ **Expression** - Computation, Reimagined

Forget callbacks. Forget promises. Think in Expressions. Build complex flows from simple, composable blocks:

```python
class NotificationDispatcher(Expression):
    """Multi-channel notification with sophisticated delivery logic"""
    
    def __init__(self, app, message_path: ExpressionPath, **kwargs):
        super().__init__(app, **kwargs)
        
        self.expression = Parallel(
            self,
            # ============================================
            # Email with provider fallback
            # ============================================
            If(
                self,
                condition=Path().message.channels.email_enabled,
                expression=Timeout(
                    self,
                    expression=Sequence(
                        self,
                        If(
                            self,
                            condition=Path().services.sendgrid.healthy,
                            expression=SendEmail(self, provider="sendgrid"),
                            otherwise=SendEmail(self, provider="backup_smtp")
                        ),
                        Set(self, Path().delivery.email.sent_at, "now"),
                    ),
                    timeout_seconds=30,
                    on_timeout=LogFailure(self, "Email timeout")
                )
            ),
            
            # ============================================
            # SMS with carrier optimization
            # ============================================
            If(
                self,
                condition=Path().message.channels.sms_enabled,
                expression=Timeout(
                    self,
                    expression=Sequence(
                        self,
                        If(
                            self,
                            condition=Path().message.priority.urgent,
                            expression=Parallel(
                                self,
                                SendSMS(self, carrier="primary"),
                                Delay(self, 1.0),
                                SendSMS(self, carrier="backup"),
                                max_concurrency=1
                            ),
                            otherwise=SendSMS(self, carrier="primary")
                        ),
                        IncrementInt(self, Path().stats.sms_sent),
                    ),
                    timeout_seconds=15
                )
            ),
            
            # ============================================
            # Push to all user devices
            # ============================================
            If(
                self,
                condition=Path().message.channels.push_enabled,
                expression=Parallel(
                    self,
                    SendAPNS(self, devices=Path().user.devices.ios),
                    SendFCM(self, devices=Path().user.devices.android),
                    SendWebPush(self, subscriptions=Path().user.devices.web),
                    max_concurrency=3
                )
            ),
            
            # ============================================
            # Slack for urgent work messages
            # ============================================
            If(
                self,
                condition=Path().message.priority.urgent,
                expression=If(
                    self,
                    condition=Path().user.workspace.online,
                    expression=SendSlack(self, channel="direct"),
                    otherwise=SendSlack(self, channel="urgent", mention=True)
                )
            ),
            
            max_concurrency=4,
            error_behavior="continue"  # Don't let one channel stop others
        )
    
    def do_evaluate(self, context: Context):
        self.expression.evaluate(
            self.derive_child_context(context, child_expression=self.expression)
        )
```

**Features:**
- **Resource integration** - seamless access to infrastructure
- **State integration** - unified interface to application state

### 🏗️ **Resource Topology** - Infrastructure as Application

Your infrastructure IS your application. No external orchestrators, no deployment complexity:

```python
# Attach dependencies automatically
class DataService(SyncResource):
    database: DatabaseClient = Attach()
    cache: RedisClient = Attach()
    
    def process_data(self, data):
        # Dependencies injected automatically
        pass

# Proxy remote resources transparently  
class DistributedProcessor(SyncResource):
    worker_pool: WorkerFleet = Attach()
    
    def distribute_work(self, jobs):
        # Transparent remote calls
        return self.worker_pool.submit(jobs)
```

**Vision:** Full infrastructure coordination - from load balancers and replicators to service meshes and beyond. Your entire system topology expressed as code.

## This is Microflow

When **State**, **Resource Topology**, and **Expression** converge, something magical happens. We call it **Microflow**.

A new programming paradigm where your entire application - its data, infrastructure, and logic - becomes one unified, composable system.

```python
from loomi import AppSpec, Context
from loomistd import SyncApp
from loomistd.expressions import Sequence, Print, Set, Delay, Parallel, If, Loop, Timeout, IncrementInt

class DataPipeline(SyncApp):
    # Resources injected automatically
    data_feed: MarketDataFeed = Attach(proxy=True)
    database: TimeSeriesDB = Attach()
    
    def processing_flow(self):
        return Sequence(
            self,
            # Initialize state using primitives
            Set(self, Path().system.status, "starting"),
            Set(self, Path().system.cycle_count, 0),
            Set(self, Path().data.processed_count, 0),
            Print(self, "Data pipeline starting..."),
            
            # Main processing loop built from primitives
            Loop(
                self,
                condition=Path().system.running,
                expression=Sequence(
                    self,
                    # Parallel data collection with timeout protection
                    Timeout(
                        self,
                        expression=Parallel(
                            self,
                            # Each stream uses only primitive operations
                            Sequence(
                                self,
                                Set(self, Path().feeds.equity.status, "fetching"),
                                Set(self, Path().feeds.equity.data, self.data_feed.get_equity_prices()),
                                Set(self, Path().feeds.equity.updated_at, "now"),
                                IncrementInt(self, Path().feeds.equity.fetch_count),
                            ),
                            Sequence(
                                self,
                                Set(self, Path().feeds.crypto.status, "fetching"), 
                                Set(self, Path().feeds.crypto.data, self.data_feed.get_crypto_prices()),
                                Set(self, Path().feeds.crypto.updated_at, "now"),
                                IncrementInt(self, Path().feeds.crypto.fetch_count),
                            ),
                            max_concurrency=2
                        ),
                        timeout_seconds=10,
                        on_timeout=Sequence(
                            self,
                            Print(self, "Data fetch timeout - using cached data"),
                            Set(self, Path().system.last_error, "fetch_timeout")
                        )
                    ),
                    
                    # Complex conditional processing using only primitives
                    If(
                        self,
                        condition=Path().feeds.equity.updated_at != Path().system.last_equity_update,
                        expression=Sequence(
                            self,
                            Print(self, Path().feeds.equity.data, message="Processing equity data: {value}"),
                            # Data validation using state comparisons
                            If(
                                self,
                                condition=Path().feeds.equity.data.length() > 0,
                                expression=Sequence(
                                    self,
                                    Set(self, Path().processing.equity.normalized, 
                                        Path().feeds.equity.data.transform("normalize")),
                                    Set(self, Path().processing.equity.moving_avg,
                                        Path().processing.equity.normalized.calculate_ma(20)),
                                    # Anomaly detection with primitive logic
                                    If(
                                        self,
                                        condition=(Path().processing.equity.moving_avg.std_dev() > 
                                                 Path().config.anomaly_threshold),
                                        expression=Sequence(
                                            self,
                                            Print(self, "Anomaly detected in equity data!"),
                                            Set(self, Path().alerts.equity.anomaly_detected, True),
                                            IncrementInt(self, Path().alerts.equity.anomaly_count)
                                        )
                                    ),
                                    IncrementInt(self, Path().data.processed_count)
                                ),
                                otherwise=Print(self, "Empty equity dataset - skipping")
                            ),
                            Set(self, Path().system.last_equity_update, Path().feeds.equity.updated_at)
                        )
                    ),
                    
                    # Parallel storage operations with error handling
                    If(
                        self,
                        condition=Path().data.processed_count > Path().system.last_saved_count,
                        expression=Parallel(
                            self,
                            # Database save with retry logic
                            Sequence(
                                self,
                                Set(self, Path().storage.db.status, "saving"),
                                If(
                                    self,
                                    condition=Path().database.is_healthy(),
                                    expression=Sequence(
                                        self,
                                        Set(self, Path().storage.db.result, 
                                            self.database.save(Path().processing.equity.normalized)),
                                        Set(self, Path().storage.db.last_save, "now"),
                                        Print(self, "Data saved to database")
                                    ),
                                    otherwise=Sequence(
                                        self,
                                        Print(self, "Database unhealthy - queuing for retry"),
                                        IncrementInt(self, Path().storage.db.retry_count)
                                    )
                                )
                            ),
                            # Cache update
                            Sequence(
                                self,
                                Set(self, Path().storage.cache.data, Path().processing.equity.moving_avg),
                                Set(self, Path().storage.cache.updated_at, "now"),
                                Print(self, "Cache updated")
                            ),
                            max_concurrency=2
                        )
                    ),
                    
                    # System maintenance using counters and conditionals
                    If(
                        self,
                        condition=Path().system.cycle_count % 100 == 0,
                        expression=Sequence(
                            self,
                            Print(self, Path().system.cycle_count, message="Maintenance cycle {value}"),
                            Set(self, Path().maintenance.cleanup_started, True),
                            Delay(self, 0.5),  # Primitive delay
                            Set(self, Path().maintenance.cleanup_completed, True),
                            IncrementInt(self, Path().system.maintenance_count)
                        )
                    ),
                    
                    IncrementInt(self, Path().system.cycle_count),
                    Delay(self, duration=Path().config.poll_interval)
                )
            ),
            
            Print(self, "Data pipeline completed")
        )

# Application topology as code  
app_spec = AppSpec(
    name="data_pipeline",
    data_feed=MarketDataFeedSpec(proxy=True, replicas=3),
    database=TimeSeriesDBSpec(pool_size=20)
)

# Deploy and run
with DataPipeline(app_spec) as app:
    app.processing_flow().evaluate()
```

**Microflow Vision:**
- **Unified Development** - Write your entire system as one cohesive program
- **Composable at Scale** - From simple expressions to distributed architectures  
- **Infrastructure as Code** - Your topology IS your application
- **State-Driven Logic** - Reactive, observable, transactional by design
- **Production Ready** - From prototype to planet-scale with the same paradigm

---

<div align="center">
  <p><b>Loomi</b></p>
  <p>MIT License | Built with ❤️ by developers, for developers</p>
</div>
