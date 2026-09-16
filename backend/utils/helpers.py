def get_month_start(date):
    return date.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )
    
def get_next_month(date):
    if date.month == 12:
        return date.replace(
            year=date.year +1,
            month=1,
            day=1
        )
        
    return date.replace(
        month = date.month +1,
        day =1
    )