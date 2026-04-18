from datetime import datetime, date, timedelta

def get_next_birthday(day, month, year=None):
    today = date.today()
    try:
        # Check if birthday already happened this year
        bday_this_year = date(today.year, month, day)
    except ValueError:
        # Handle Leap year issue (Feb 29)
        if month == 2 and day == 29:
            bday_this_year = date(today.year, 2, 28) # Or 3, 1
        else:
            raise
            
    if bday_this_year < today:
        try:
            return date(today.year + 1, month, day)
        except ValueError:
            return date(today.year + 1, 2, 28)
    return bday_this_year

def format_countdown(target_date):
    # We want a more precise countdown (dd, hh, mm, ss) 
    # Since reminders happen at specific times, let's assume the target is 00:00 of the birthday
    now = datetime.now()
    target_time = datetime.combine(target_date, datetime.min.time())
    
    diff = target_time - now
    
    if diff.total_seconds() < 0:
        return "00, 00, 00, 00"
        
    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return f"{days:02d}kun, {hours:02d}soat, {minutes:02d}min, {seconds:02d}sek"

def get_age(birth_year, current_year):
    if not birth_year:
        return None
    return current_year - birth_year

def days_until_birthday(day, month):
    next_bday = get_next_birthday(day, month)
    today = date.today()
    return (next_bday - today).days
