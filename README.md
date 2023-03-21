# ice-back-track

Compute backwards trajectory of sea ice parcel using OSI-SAF sea ice drift and ice concentration products

## Usage
Execute the CLI app like this:
```
➜  ice-back-track git:(main) ✗ PYTHONPATH=. python3 bin/track --help
```

## Options and arguments

```
 Usage: track [OPTIONS] START_DATE:[%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d
              %H:%M:%S] LON_0 LAT_0 OUTPUT

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────────────╮
│ *    start_date      START_DATE:[%Y-%m-%d|%Y-%m-%dT%H:%M:%  Start date for backtracking             │
│                      S|%Y-%m-%d %H:%M:%S]                   [default: None]                         │
│                                                             [required]                              │
│ *    lon_0           FLOAT                                  Longitude of mooring/end position       │
│                                                             [default: None]                         │
│                                                             [required]                              │
│ *    lat_0           FLOAT                                  Latitude of mooring/end position        │
│                                                             [default: None]                         │
│                                                             [required]                              │
│ *    output          PATH                                   Destination path for results            │
│                                                             [default: None]                         │
│                                                             [required]                              │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────╮
│ --min-ice-conc              INTEGER  Minimum ice concentration [default: 70]                        │
│ --search-radius             INTEGER  Search radius for OSI-SAF drift (in km) [default: 100]         │
│ --install-completion                 Install completion for the current shell.                      │
│ --show-completion                    Show completion for the current shell, to copy it or customize │
│                                      the installation.                                              │
│ --help                               Show this message and exit.                                    │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
