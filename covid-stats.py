#!/usr/bin/env python3
import os
import csv
import re
import datetime
import matplotlib.pyplot as plt


def auto_int(x):
    if not x:
        return 0
    else:
        return int(x)


def process_file(df):
    stats_by_country = {}

    rows = list(csv.reader(df))
    confirmed_index = 0
    recovered_index = 0
    country_index = 0
    deaths_index = 0

    for i, cname in enumerate(rows[0]):
        if re.match('country', cname, re.I):
            country_index = i
        elif re.match('death', cname, re.I):
            deaths_index = i
        elif re.match('confirmed', cname, re.I):
            confirmed_index = i
        elif re.match('recovered', cname, re.I):
            recovered_index = i

    for row in rows[1:]:
        country = row[country_index]
        deaths = auto_int(row[deaths_index])
        confirmed = auto_int(row[confirmed_index])
        recovered = auto_int(row[recovered_index])

        if country not in stats_by_country:
            stats_by_country[country] = {
                "confirmed": 0,
                "recovered": 0,
                "deaths": 0
            }

        stats_by_country[country]["deaths"] += deaths
        stats_by_country[country]["confirmed"] += confirmed
        stats_by_country[country]["recovered"] += recovered

    return stats_by_country


data_dir = "COVID-19/csse_covid_19_data/csse_covid_19_daily_reports"
all_files = sorted(fn for fn in os.listdir(data_dir) if fn.endswith("csv"))
stats = [(f[0:-4], process_file(open(data_dir + "/" + f))) for f in all_files]

for f, stat in stats[-15:]:
    print("US confirmed/deaths/recovered for {}: {}/{}/{}".format(
        f, stat['US']['confirmed'], stat['US']['deaths'],
        stat['US']['recovered']))

y1 = [stat['US']['deaths'] for f, stat in stats[-20:]]
y2 = [stat['US']['confirmed'] for f, stat in stats[-20:]]
x = [datetime.datetime.strptime(f, "%m-%d-%Y") for f, stat in stats[-20:]]
fig, axs = plt.subplots(2)
axs[0].plot(x, y1)
axs[0].set_title('Deaths')
axs[1].plot(x, y2)
axs[1].set_title('Confirmed cases')

for ax in axs:
    for tick in ax.get_xticklabels():
        tick.set_rotation(45)

plt.tight_layout()
plt.show()
