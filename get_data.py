from datetime import timedelta, date
import csv
import re
from lxml import html
from lxml.etree import tostring
import requests
import requests_cache
import collections
from progress.bar import Bar

#requests_cache.install_cache('cache')

header = ['date',
          'lat',
          'lon',
          'station',
          'temp_max',
          'temp_min',
          'temp_med',
          'td_med',
          'hr_med',
          'wind_dir',
          'wind_int',
          'wind_gust',
          'pres',
          'prec_mm',
          'tot_cl_oct',
          'low_ci_oct',
          'sun_d_1',
          'vis_km']

Row = collections.namedtuple('Row', header)

def process_url(url):
    page = html.fromstring(requests.get(url).content)
    page.xpath("//table[caption[contains(text(), 'OGIMET')]]")
    for row in page.xpath("//table[caption/b[contains(text(), 'OGIMET')]]//tr")[3:]:
        cols = row.xpath('td')
        place = tostring(cols[0]).decode('ascii')
        lat, lon = coord_to_decimal(place)
        cols = [None, lat, lon] + ["".join(col.itertext()).replace("-", "") for col in cols][:15]
        yield Row(*cols)


def extract_dd(coord):
    direction = coord[-1]
    parts = [float(x) for x in coord[:-1].split('-')]
    if len(parts) == 3:
        degrees, minutes, seconds = parts
    else:
        degrees, minutes = parts
        seconds = 0

    minutes = minutes / 60
    seconds = seconds / 60 / 60
    dd = degrees + minutes + seconds
    if direction == 'W':
        dd *= -1
    return round(dd, 3)


def coord_to_decimal(coord):
    match = re.search(r"Lat=(.*?N) Lon=(.*?(?:E|W))", coord)
    if match:
        lat, lon = match.groups()
        return (extract_dd(lat), extract_dd(lon))
    else:
        return (None, None)


def generate_urls(start_date, end_date):
    url = ("https://www.ogimet.com/cgi-bin/gsynres?lang=en&state=United+K"
           "&osum=no&fmt=html&ord=REV&"
           "ano={year}&mes={month}&day={day}"
           "&hora=18&ndays=1&Send=send")
    for n in range(int((end_date - start_date).days)):
        date = start_date + timedelta(n)
        yield url.format(year=date.year, month=date.month, day=date.day), date


if __name__ == '__main__':
    with open("data2.csv", "w") as f:
        w = csv.writer(f)
        w.writerow(header)
        start_date = date(1999, 10, 1)  # data doesn't start till just before this
        end_date = date(2008, 7, 31)
        urls = list(generate_urls(start_date, end_date))
        bar = Bar("Downloading", max=len(urls), suffix='%(eta_td)s')
        for url, day in urls:
            for row in process_url(url):
                row = row._replace(date=day.strftime("%Y-%m-%d"))
                w.writerow(row)
            bar.next()
        bar.finish()
