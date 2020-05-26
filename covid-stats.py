#!/usr/bin/env python3
import argparse
import csv
import datetime
import matplotlib.pyplot as plt
import os
import re
import sys

import population


def get_args():
    parser = argparse.ArgumentParser(description='get some COVID-19 stats')
    parser.add_argument('-c',
                        '--country',
                        help='get results for the specified country')
    parser.add_argument('-s',
                        '--state',
                        help='get results for the specified state or province')
    parser.add_argument(
        '-a',
        '--admin',
        help='get results for an admin (county or city, column admin2)')
    parser.add_argument('--list-countries',
                        action="store_true",
                        help='list countries available in the data')
    parser.add_argument(
        '--list-states',
        action="store_true",
        help='list states in the data, matching a country if specified')
    parser.add_argument(
        '--list-admin',
        action="store_true",
        help=
        'list administrative areas (e.g. counties) in the data, matching a country and state if specified'
    )
    parser.add_argument('-g',
                        '--graph',
                        action="store_true",
                        help='generate a plot of the data')
    parser.add_argument('-p',
                        '--print',
                        action="store_true",
                        help='print the data')

    return parser.parse_args()


def auto_int(x):
    if not x:
        return 0
    else:
        return int(x)


def process_header(row):
    indexes = {}

    for i, cname in enumerate(row):
        if re.match('country', cname, re.I):
            indexes['country'] = i
        elif re.match('death', cname, re.I):
            indexes['death'] = i
        elif re.match('confirmed', cname, re.I):
            indexes['confirmed'] = i
        elif re.match('recovered', cname, re.I):
            indexes['recovered'] = i
        elif re.match('state|province', cname, re.I):
            indexes['state'] = i
        elif re.match('admin', cname, re.I):
            indexes['admin'] = i

    return indexes


def get_column(indexes, col, row, default=''):
    return row[indexes[col]] if col in indexes else default


def process_row(indexes, stats, row):
    country = get_column(indexes, 'country', row)
    state = get_column(indexes, 'state', row)
    admin = get_column(indexes, 'admin', row)
    deaths = auto_int(get_column(indexes, 'death', row))
    recovered = auto_int(get_column(indexes, 'recovered', row))
    confirmed = auto_int(get_column(indexes, 'confirmed', row))

    if country not in stats:
        stats[country] = {}
    if state not in stats[country]:
        stats[country][state] = {}
    if admin not in stats[country][state]:
        stats[country][state][admin] = {
            'confirmed': 0,
            'recovered': 0,
            'deaths': 0
        }

    stats[country][state][admin]['confirmed'] += confirmed
    stats[country][state][admin]['deaths'] += deaths
    stats[country][state][admin]['recovered'] += recovered
    return stats


def get_stats(stats, country=None, state=None, admin=None):
    result = {'confirmed': 0, 'deaths': 0, 'recovered': 0}
    countries = [country] if country else list(stats.keys())

    for c in countries:
        states = [state] if state else list(stats[c].keys())

        for s in states:
            if s not in stats[c]:
                continue

            admins = [admin] if admin else list(stats[c][s].keys())

            for a in admins:
                result['confirmed'] += stats[c][s][a]['confirmed']
                result['deaths'] += stats[c][s][a]['deaths']
                result['recovered'] += stats[c][s][a]['recovered']

    return result


def list_countries(stats):
    return sorted(list(stats.keys()))


def list_states(stats, country=None):
    states = set()

    if country:
        countries = [country]
    else:
        countries = list_countries(stats)

    for c in countries:
        states.update(stats[c].keys())

    return sorted(list(states))


def list_admins(stats, country=None, state=None):
    admins = set()

    if country:
        countries = [country]
    else:
        countries = list_countries(stats)

    if state:
        states = [state]
    else:
        states = list_states(stats, country)

    for c in countries:
        for s in states:
            if s in stats[c]:
                admins.update(stats[c][s].keys())

    return sorted(list(admins))


def process_file(path, stats=None):
    (d, t) = os.path.split(path)

    if stats is None:
        stats = {}

    with open(path) as df:
        rows = list(csv.reader(df))
        indexes = process_header(rows[0])

        for row in rows[1:]:
            stats = process_row(indexes, stats, row)

    return t[0:-4], stats


def get_suffix(country=None, state=None, admin=None):
    if admin:
        if state:
            if country:
                return "in {}, {}, {}".format(admin, state, country)
            else:
                return "in {}, {}".format(admin, state)
        else:
            return "in {}".format(admin)
    elif state:
        if country:
            return "in {}, {}".format(state, country)
        else:
            return "in {}".format(state)
    elif country:
        return "in {}".format(country)
    else:
        return "(World)"


def graphit(data, country=None, state=None, admin=None):
    y1 = [get_stats(stat, country, state, admin)['deaths'] for f, stat in data]
    y2 = [
        get_stats(stat, country, state, admin)['confirmed'] for f, stat in data
    ]

    if state and country == 'US':
        y3 = [d * 100000 / population.data[state] for d in y1]
        y4 = [c * 100000 / population.data[state] for c in y2]
    elif country == 'US':
        y3 = [d * 100000 / population.data['United States'] for d in y1]
        y4 = [c * 100000 / population.data['United States'] for c in y2]
    else:
        y3 = None
        y4 = None

    x = [datetime.datetime.strptime(f, "%m-%d-%Y") for f, stat in data]

    suffix = get_suffix(country, state, admin)

    if y3:
        fig, axs = plt.subplots(nrows=2, ncols=2)

        suffix = get_suffix(country, state, admin)

        axs[0][0].plot(x, y1)
        axs[0][0].set_title('Deaths {}'.format(suffix))
        axs[0][0].grid(True)
        axs[1][0].plot(x, y2)
        axs[1][0].set_title('Confirmed cases {}'.format(suffix))
        axs[1][0].grid(True)

        axs[0][1].plot(x, y3)
        axs[0][1].set_title('Per 100k deaths {}'.format(suffix))
        axs[0][1].grid(True)
        axs[1][1].plot(x, y4)
        axs[1][1].set_title('Per 100k cases {}'.format(suffix))
        axs[1][1].grid(True)

        for a in axs:
            for b in a:
                for tick in b.get_xticklabels():
                    tick.set_rotation(45)

    else:
        fig, axs = plt.subplots(2)

        axs[0].plot(x, y1)
        axs[0].set_title('Deaths {}'.format(suffix))
        axs[0].grid(True)
        axs[1].plot(x, y2)
        axs[1].set_title('Confirmed cases {}'.format(suffix))
        axs[1].grid(True)

        for a in axs:
            for tick in a.get_xticklabels():
                tick.set_rotation(45)

    plt.tight_layout()
    plt.show()


def printit(data, country=None, state=None, admin=None):
    suffix = get_suffix(country, state, admin)

    for t, stats in data:
        x = get_stats(stats, country, state, admin)
        print("{}, {}, confirmed/deaths/recovered: {}/{}/{}".format(
            t, suffix, x['confirmed'], x['deaths'], x['recovered']))


def main():
    args = get_args()
    kw = {'country': args.country, 'state': args.state, 'admin': args.admin}
    data_dir = "COVID-19/csse_covid_19_data/csse_covid_19_daily_reports"
    all_files = sorted(fn for fn in os.listdir(data_dir) if fn.endswith("csv"))
    data = [process_file(os.path.join(data_dir, p)) for p in all_files]

    if args.list_countries:
        countries = set()

        for _, stats in data:
            countries.update(list_countries(stats))

        for c in sorted(list(countries)):
            print(c)
    elif args.list_states:
        states = set()

        for _, stats in data:
            states.update(list_states(stats, country=args.country))

        for c in sorted(list(states)):
            print(c)
    elif args.list_admin:
        admins = set()

        for _, stats in data:
            admins.update(
                list_admins(stats, country=args.country, state=args.state))

        for a in sorted(list(admins)):
            print(a)
    else:
        if args.print:
            printit(data, **kw)
        if args.graph:
            graphit(data, **kw)


if __name__ == "__main__":
    main()
