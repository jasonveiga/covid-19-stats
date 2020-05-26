import csv

data = {}


def _pop_csv_rows():
    with open('./nst-est2019-alldata.csv') as pop_f:
        for row in list(csv.reader(pop_f))[1:]:
            s = int(row[3])
            n = row[4]

            if s > 0 or n == 'United States':
                p = int(row[5])
                data[n] = p


_pop_csv_rows()
