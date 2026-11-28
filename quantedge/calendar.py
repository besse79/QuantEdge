"""Generate explicit exchange sessions using the free exchange_calendars library."""
from datetime import timedelta
from .mkd_backtest import Session

def exchange_sessions(calendar_name, start, end, *, publication_delay_minutes=120):
    if start > end or type(publication_delay_minutes) is not int or publication_delay_minutes < 0:
        raise ValueError("invalid calendar range or delay")
    import exchange_calendars as xc
    calendar = xc.get_calendar(calendar_name)
    sessions = []
    for label in calendar.sessions_in_range(start.isoformat(), end.isoformat()):
        opening = calendar.session_open(label).to_pydatetime().astimezone(calendar.tz)
        closing = calendar.session_close(label).to_pydatetime().astimezone(calendar.tz)
        cutoff = closing + timedelta(minutes=publication_delay_minutes)
        if opening.date() != closing.date() or cutoff.date() != opening.date():
            raise ValueError("overnight sessions unsupported")
        sessions.append(Session(opening.date(), opening, cutoff))
    if not sessions:
        raise ValueError("no exchange sessions")
    return sessions
