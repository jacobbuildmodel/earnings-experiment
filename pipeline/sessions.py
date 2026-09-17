"""NYSE trading sessions and the D001 timing table.

Holidays and early closes copied from https://www.nyse.com/markets/hours-calendars on 2026-09-17.
"""
import datetime

HOLIDAYS = {datetime.date.fromisoformat(d) for d in [
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03", "2026-05-25", "2026-06-19",
    "2026-07-03", "2026-09-07", "2026-11-26", "2026-12-25",
    "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26", "2027-05-31", "2027-06-18",
    "2027-07-05", "2027-09-06", "2027-11-25", "2027-12-24",
]}
EARLY_CLOSE = {datetime.date.fromisoformat(d) for d in ["2026-11-27", "2026-12-24", "2027-11-26"]}
LAST_KNOWN = datetime.date(2027, 12, 31)


def is_session(d):
    if d > LAST_KNOWN:
        raise ValueError(f"{d} is past the holiday table - extend sessions.py from nyse.com")
    return d.weekday() < 5 and d not in HOLIDAYS


def shift(d, n):
    """The n-th session after (n > 0) or before (n < 0) date d. n = 0 returns d, which must be a session."""
    if n == 0:
        if not is_session(d):
            raise ValueError(f"{d} is not a trading session")
        return d
    step = 1 if n > 0 else -1
    count = 0
    while count != abs(n):
        d += datetime.timedelta(days=step)
        if is_session(d):
            count += 1
    return d


def timing(report_date, session, rule):
    """D001 §1: entry, exits and reaction day for a print; D003 §6: the S2 snapshot session."""
    t = rule["timing"][session]
    out = {}
    for key in ("entry", "exit_A", "exit_B", "exit_C"):
        kind, offset = t[key]
        out[key] = {"price": kind, "session": shift(report_date, offset).isoformat()}
    out["reaction_day"] = shift(report_date, 0 if session == "BMO" else 1).isoformat()
    return out
