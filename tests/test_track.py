

from sidrift.track import backtrack
from datetime import datetime

def test_backtrack():
    
    start_date = datetime(2020,1,1)
    lon_0 = -10.
    lat_0 = 85.
    
    expected = None
    
    result = backtrack(start_date,lon_0,lat_0)
    
    #import ipdb; ipdb.set_trace()
    
    assert len(result) > 0
