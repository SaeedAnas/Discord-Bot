from datetime import datetime
import arrow


def to_date(time):
    return arrow.get(time, 'YYYY-MM-DDTHH:mm:ss[.000Z]').replace(tzinfo='utc')
    # return datetime.strptime(time, "%Y-%m-%dT%H:%M:%S.000Z").astimezone(
    #     tz=utc)  # - timedelta(hours=7)


def get_utc_time():
    return arrow.utcnow()


def get_pst():
    return arrow.now('US/Pacific')


def to_pst(time):
    return to_date(time).to('US/Pacific')


def format_pst(time):
    present = get_pst()
    return to_pst(time).humanize(present)


def from_day(time):
    today = arrow.get(get_pst().format('dddd'), 'dddd').replace(hour=0,
                                                                minute=0,
                                                                second=0,
                                                                microsecond=0)
    time_formats = [
        'dddd h:mmA', 'ddd h:mmA', 'dddd [at] h:mmA', 'ddd [at] h:mmA',
        'dddd h:mm A', 'ddd h:mm A', 'dddd [at] h:mm A', 'ddd [at] h:mm A'
    ]
    for format in time_formats:
        try:
            t = arrow.get(
                time,
                format,
            ).replace(tzinfo='US/Pacific')
            diff = (t - today).days
            if diff <= 0:
                diff += 7

            t = get_pst().shift(days=diff).replace(hour=t.hour,
                                                   minute=t.minute,
                                                   second=t.second)

            return t
        except Exception:
            continue

    raise Exception('No day found')


def dehumanize(t):
    present = get_pst()
    t = t.split('at')
    date = t[0].strip()
    if len(t) > 1:
        time = t[1].strip()
        if date.lower() == 'today':
            date = get_pst()
        elif date.lower() == 'tommorow':
            date = get_pst().shift(days=1)
        else:
            date = present.dehumanize(date)
        time = arrow.get(time, 'h:mmA')
        date = date.replace(hour=time.hour,
                            minute=time.minute,
                            second=0,
                            microsecond=0)
        return date
    else:
        return present.dehumanize(date)


def parse_time(time):
    time_formats = [
        'M-D-YY h:mmA [*]',
        'M/D/YY h:mmA [*]',
        'M-D h:mmA [*]',
        'M/D h:mmA [*]',
        'M-D-YYYY h:mmA [*]',
        'M/D/YYYY h:mmA [*]',
        'M-D h:mmA [*]',
        'M/D h:mmA [*]',
        'M-D-YY h:mm A [*]',
        'M/D/YY h:mm A [*]',
        'M-D h:mm A [*]',
        'M/D h:mm A [*]',
        'M-D-YYYY h:mm A [*]',
        'M/D/YYYY h:mm A [*]',
        'M-D h:mm A [*]',
        'M/D h:mm A [*]',
    ]
    try:
        return from_day(time)
    except Exception:
        try:
            return dehumanize(time)
        except Exception:
            for format in time_formats:
                try:
                    t = arrow.get(
                        time,
                        format,
                    ).replace(tzinfo='US/Pacific')

                    if t.year == 1:
                        t = t.replace(year=2021)
                    return t
                except Exception:
                    continue

            return None


def format_meeting_time(time):
    return time.format("M-DD-YYYY h:mmA")


def has_passed(time):
    now = get_pst()
    return time < now


def strip(time):
    return time.replace(second=0, microsecond=0)


def check(time, compare):
    c = strip(time.dehumanize(compare))
    present = strip(get_pst())
    return c == present


def isNow(time):
    present = strip(get_pst())
    time = strip(time)
    return present == time


def format_dates(dates, branch=''):
    if len(dates) <= 0:
        return 'No meetings scheduled'
    if branch != '':
        branch += ':'
    formatted = ''
    for date in dates:
        if date.place is None:
            formatted += f'● {branch} {date.time.humanize()} at {format_meeting_time(date.time)}\n'
        else:
            formatted += f'● {branch} {date.time.humanize()} at {format_meeting_time(date.time)}\n@ {date.place}\n'
    return formatted
