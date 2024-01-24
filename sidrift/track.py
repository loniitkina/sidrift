from datetime import datetime, timedelta
import numpy as np
import os

import xarray as xr
from pyproj import Proj, transform


def backtrack(
    start_date: datetime,
    lon_0: float,
    lat_0: float,
    min_ice_conc: float = 70,
    search_radius: float = 100,
    output: str = None,
    limit_days: int = 100,
):
    ##mooring position
    inProj = Proj(init="epsg:4326")
    # OSI-SAF proj: proj4_string = "+proj=stere +a=6378273 +b=6356889.44891 +lat_0=90 +lat_ts=70 +lon_0=-45"
    outProj = Proj(
        "+proj=stere +a=6378273 +b=6356889.44891 +lat_0=90 +lat_ts=70 +lon_0=-45 +units=km"
    )

    # Fram Strait moorings
    # [ -8, 78.83, 0, 79 ]   #approx bounding box
    moor_lat = [lat_0]
    moor_lon = [lon_0]
    xmoor_start, ymoor_start = transform(inProj, outProj, moor_lon, moor_lat)

    print(xmoor_start, ymoor_start)

    # OSI_SAF drift
    iceconc_url = (
        "https://thredds.met.no/thredds/dodsC/osisaf/met.no/ice/conc_nh_pol_agg"
    )
    drift_url = "https://thredds.met.no/thredds/dodsC/osisaf/met.no/ice/drift_lr_nh_agg"

    ds_drift = xr.open_dataset(drift_url)

    # OSI_SAF ice concentration
    ds_ic = xr.open_dataset(iceconc_url)

    yr = start_date.year

    start = start_date
    xmoor = xmoor_start.copy()
    ymoor = (
        ymoor_start.copy()
    )  # use .copy() or xmoor_start will become reference of xmoor

    # do backtrajectories for each mooring point
    print("#########################################################################")
    date = start
    bt_lon = [moor_lon[0]]
    bt_lat = [moor_lat[0]]
    bt_date = [start]
    print(date, moor_lon[0], moor_lat[0])

    ice = True
    cnt = 0  # counter for limiting the number of iterations

    while ice == True and cnt < limit_days:
        ic = ds_ic.ice_conc.sel(time=date, xc=xmoor[0], yc=ymoor[0], method="nearest")
        icm = np.mean(np.ma.masked_invalid(ic.values))

        print(icm)
        if icm < min_ice_conc:
            ice = False
            print(date)
            print("Ice concentration below treshold: " + str(icm))
            continue

        # find the corresponding OSI-SAF drift file/date
        # this will get only one value (if that value is nan, there is nothing to mask for average calculation)
        # dx = ds_drift.dX.sel(time=date,xc=xmoor[i],yc=ymoor[i],method='bfill')
        # this will get several inside the spatial slice
        # the interval at yc has to be turned around!!!
        dx = ds_drift.dX.sel(time=date, method="nearest").sel(
            xc=slice(xmoor[0] - search_radius, xmoor[0] + search_radius),
            yc=slice(ymoor[0] + search_radius, ymoor[0] - search_radius),
        )  # IS THIS INTERVAL FOR YC ONLY SUCH UNTIL 2016???
        dxm = (
            np.mean(np.ma.masked_invalid(dx.values)) / 2
        )  # this is displacement for 2 days

        dy = ds_drift.dY.sel(time=date, method="nearest").sel(
            xc=slice(xmoor[0] - search_radius, xmoor[0] + search_radius),
            yc=slice(ymoor[0] + search_radius, ymoor[0] - search_radius),
        )
        dym = (
            np.mean(np.ma.masked_invalid(dy.values)) / 2
        )  # this is displacement for 2 days

        # OSI-SAF data issue:
        # the early version had different sign, data was never reprocessed
        # sign changed already in November, December 2015???
        if yr < 2016:
            dym = dym * -1

        if abs(dxm) * abs(dym) > 0:
            # calculate position back in time
            xmoor[0] = xmoor[0] - dxm
            ymoor[0] = ymoor[0] - dym

            # transform back to latlon and to the OSI-SAF coordinates
            lon, lat = transform(outProj, inProj, xmoor[0], ymoor[0])
            # store back-trajectory
            bt_lon.append(lon)
            bt_lat.append(lat)
            bt_date.append(date)

            # walk back in time by 1 day
            date = date - timedelta(days=1)

        else:
            # if we start in December or November (same year) freeze-up will not be identified and the loop will end here
            ice = False
            print("No more ice!", date)

        print("COUNTER is   ", cnt)
        cnt += 1

    print(
        "trajectory of days: ",
        len(bt_lat),
        "and final location: ",
        bt_lat[-1],
        bt_lon[-1],
    )

    # write out text files with dates and coordinates
    tt = [bt_date, bt_lon, bt_lat]
    table = [(x[0].strftime("%Y-%m-%d"), x[1], x[2]) for x in list(zip(*tt))]

    if not output:
        return table
    else:
        try:
            os.remove(output)
        except:
            pass
        finally:
            with open(output, "ab") as f:
                np.savetxt(f, table, fmt="%s", delimiter=",")
