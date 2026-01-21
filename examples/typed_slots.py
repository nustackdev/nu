"""Typed Slots Example - Event Tracker.

Demonstrates rich typed slots with convenience methods.

The magic: Call domain methods directly on slots without importing Value types!

    # Old verbose pattern:
    year = DatetimeValue.from_iso(EventLog.created_at.get()).year()

    # New clean pattern - call methods directly on the slot:
    year = EventLog.created_at.year()
"""

import asyncio
from datetime import datetime, timedelta

import everybase as e


# =============================================================================
# SHAPES - Domain Models with Typed Slots
# =============================================================================


class Event(e.Shape):
    """Single event with typed fields."""

    id = e.type.UUIDSlot()
    timestamp = e.type.DatetimeSlot()
    name = e.s.StrSlot()
    duration = e.type.TimedeltaSlot()


class EventLog(e.Shape):
    """Event log with typed slots."""

    created_at = e.type.DatetimeSlot()
    last_event_at = e.type.DatetimeSlot()
    session_duration = e.type.TimedeltaSlot()
    event_count = e.s.IntSlot()
    last_event = e.s.ShapeSlot(Event)


# =============================================================================
# FLOWS - Pure Declarative Logic
# =============================================================================


# Initialize
init = e.f.Seq(
    e.f.Print("=== Event Tracker with Typed Slots ==={}", ""),
    EventLog.created_at.set(datetime.now()),
    EventLog.last_event_at.set(datetime.now()),
    EventLog.session_duration.set(timedelta(hours=2, minutes=30, seconds=45)),
    EventLog.event_count.set(0),
    e.f.Print("Initialized event tracker{}", ""),
)

# Record an event
record_event = e.f.Seq(
    EventLog.last_event.id.set(e.type.UUIDValue.uuid4()),
    EventLog.last_event.timestamp.set(datetime.now()),
    EventLog.last_event.name.set("user_login"),
    EventLog.last_event.duration.set(timedelta(seconds=150)),
    EventLog.last_event_at.set(datetime.now()),
    EventLog.event_count.set(EventLog.event_count.get() + 1),
    e.f.Print("Recorded event: user_login{}", ""),
)

# Show stats using CONVENIENCE METHODS - the wow moment!
show_stats = e.f.Seq(
    e.f.Print("{}", ""),
    e.f.Print("=== EVENT LOG DASHBOARD ==={}", ""),
    e.f.Print("{}", ""),
    e.f.Print("--- DatetimeSlot Methods ---{}", ""),
    e.f.Print("  .isoformat()    {}", EventLog.created_at.isoformat()),
    e.f.Print("  .year()         {}", EventLog.created_at.year()),
    e.f.Print("  .month()        {}", EventLog.created_at.month()),
    e.f.Print("  .day()          {}", EventLog.created_at.day()),
    e.f.Print("  .hour()         {}", EventLog.created_at.hour()),
    e.f.Print("  .minute()       {}", EventLog.created_at.minute()),
    e.f.Print("  .second()       {}", EventLog.created_at.second()),
    e.f.Print("  .weekday()      {}", EventLog.created_at.weekday()),
    e.f.Print("  .timestamp()    {}", EventLog.created_at.timestamp()),
    e.f.Print("{}", ""),
    e.f.Print("--- TimedeltaSlot Methods ---{}", ""),
    e.f.Print("  .total_seconds(){}", EventLog.session_duration.total_seconds()),
    e.f.Print("  .total_minutes(){}", EventLog.session_duration.total_minutes()),
    e.f.Print("  .total_hours()  {}", EventLog.session_duration.total_hours()),
    e.f.Print("  .total_days()   {}", EventLog.session_duration.total_days()),
    e.f.Print("  .days()         {}", EventLog.session_duration.days()),
    e.f.Print("{}", ""),
    e.f.Print("--- UUIDSlot Methods ---{}", ""),
    e.f.Print("  .hex()          {}", EventLog.last_event.id.hex()),
    e.f.Print("  .urn()          {}", EventLog.last_event.id.urn()),
    e.f.Print("  .version()      {}", EventLog.last_event.id.version()),
    e.f.Print("{}", ""),
    e.f.Print("--- Nested Shape Access ---{}", ""),
    e.f.Print("  last_event.timestamp.isoformat()  {}", EventLog.last_event.timestamp.isoformat()),
    e.f.Print(
        "  last_event.duration.total_seconds()  {}", EventLog.last_event.duration.total_seconds()
    ),
    e.f.Print("{}", ""),
    e.f.Print("Event Count: {}", EventLog.event_count.get()),
    e.f.Print("{}", ""),
    e.f.Print("=== No Value imports needed! ==={}", ""),
)

# Main flow
main_flow = e.f.Seq(init, record_event, show_stats)


# =============================================================================
# EXECUTION
# =============================================================================


async def main():
    from everybase.top import regular_provider, text_storage

    with text_storage(".db_events") as storage:
        await main_flow.start_flow(regular_provider(storage))


if __name__ == "__main__":
    asyncio.run(main())
