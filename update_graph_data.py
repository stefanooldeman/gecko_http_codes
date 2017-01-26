import argparse
import sys
import json
import pickle
import os
import time

status_colors_hex = {
    '200': '#6FB665',
    '204': '#4FA29F',
    '400': '#D8C726',
    '404': '#F06A2A',
    '406': '#78CAEF',
    '414': '#86F6D2',
    '500': '#043E8A',
    '502': '#A81E03',
}


def fetch_input(stats_file):
    file_resource = file(stats_file, 'r')

    data = []
    for line in file_resource:
        keys = ['count', 'code']; vals = line.strip().split()
        data.append(dict(zip(keys, vals)))

    file_resource.close()
    return data



def unpack_data(rows):
    """
        Input:
            [('2014-12-10', [{'count': '7', 'code': '200'}, {'count': '3', 'code': '204'}]),
            ('2014-12-11', [{'count': '9', 'code': '200'}, {'count': '1', 'code': '204'}]),
            ('2014-12-13', [{'count': '3', 'code': '200'}, {'count': '2', 'code': '204'}])]
        Ouput Example:
            categories = ['200', '201', '204']
            series = [
                {"color": "#108ec5", "name": "NewYork", "data": [17.0,22.0,24.8,24.1,20.1,14.1,8.6,2.5]},
                {"color": "#52b238", "name": "Berlin", "data": [13.5,17.0,18.6,17.9,14.3,9.0,3.9,1.0]},
                {"color": "#ee5728", "name": "London", "data": [11.9,15.2,17.0,16.6,14.2,10.3,6.6,4.8]}
            ]
    """

    categories = []
    series = []
    status_codes = {}

    for date, codes in sorted(rows):  # stored data can be appended in any order..
        categories.append(date)
        for entry in codes:
            code = entry['code']
            count = int(entry['count'])

            if code in status_codes:
                status_codes[code].append(count)
            else:
                status_codes[code] = [count]

    for key, value in status_codes.items():
        color = status_colors_hex.get(key, '#fff')
        serie = {"color": color, "name": "http %s" % key, "data": value}
        series.append(serie)

    # limit output for graph to last 23 points.
    # this geckoboard stupidity..
    return {'categories': categories, 'series': series}


def update_graph_data(config, new_record):
    """
        Example dataformat that will be passed around. Including the json file on disk.

        Input example:
            ('2014-12-10', [{'code': 501, 'count': 1}, {'code': 200, 'count': 340132}])

        Will be stored as:
            [
                ('2014-12-10', [{'code': 501, 'count': 1}, {'code': 200, 'count': 340132}]),
                ('2014-12-10', [{'code': 501, 'count': 1}, {'code': 200, 'count': 340132}])
            ]
    """

    exists = os.path.isfile(config['history_file'])
    with file(config['history_file'], 'r' if exists else 'w') as dump:
        schema = {'index': [], 'data': []}
        all_entries =  pickle.load(dump) if exists else schema
        the_date = new_record[0]
        if the_date not in all_entries['index'] or config['force_update']:
            if the_date in all_entries['index']:
                sys.stderr.write('warning: writing duplicate entry\n')
            all_entries['data'].append(new_record)
            all_entries['index'].append(the_date)
        else:
            sys.stderr.write('warning: did not append, data found in index\n')

    with file(config['history_file'], 'w') as dump:
        pickle.dump(all_entries, dump)

    return unpack_data(all_entries['data'])


def chart_config(api_key, chart_data):

    # https://developer.geckoboard.com/#highcharts-example
    highcharts_data = {
        "chart": {
            "style": {"color": "#b9bbbb"},
            "renderTo": "container",
            "backgroundColor": "transparent",
            "lineColor": "rgba(35,37,38,100)",
            "plotShadow": False
        },
        "credits": {"enabled": False},
        "title": {
            "style": {"color": "#b9bbbb"},
            "text": "Daily HTTP Status Codes"
        },
        "xAxis": {
            "categories": chart_data['categories']
        },
        "yAxis": {"title": {"style": {"color": "#b9bbbb"}, "text": "HTTP Requests"}},
        "legend": {
            "itemStyle": {"color": "#b9bbbb"},
            "layout": "vertical",
            "align": "right",
            "verticalAlign": "middle",
            "borderWidth":0
        },
        "series": chart_data['series']
    }

    highcharts_js = json.dumps(highcharts_data).replace('"', '\\"')
    # http://wiki.bash-hackers.org/syntax/quoting
    # - weak quoting with double-quotes: "stuff"
    # - strong quoting with single-quotes: 'stuff'
    # note: inside a single-qouted string NOTHING(!!!) is interpreted.
    return "'{\"api_key\": \"%s\", \"data\": {\"highchart\": \"%s\"}}'" % (api_key, highcharts_js)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog='update_graph_data',
                                    description=("Appends given data to graph data in Javascript format."
                                                ". Which can be accepted by Highcharts (Geckoboard API)"),
                                    add_help=True)

    parser.add_argument('filepath', type=str, help='Path to the stats file. (output from uniq -c)')
    parser.add_argument('--history', dest='history_file', type=str, help='Path to the stats file. (output from uniq -c)', required=True)
    parser.add_argument('--force-update', action='store_true', help='Force to update the history file, if the date already exists on disk')
    parser.add_argument('--api-key', type=str, help='Date of this graph stats in YYYYmmdd', required=True)
    parser.add_argument('--date', type=str, help='Date of this graph stats in YYYYmmdd')


    args = parser.parse_args()
    config = args.__dict__

    if config['force_update']:
        sys.stderr.write('warning: using --force-update, this will append data and possibly duplicate \n')
        sys.stderr.write('warning: press ^C to cancel (program starts in 1 second..)\n')
        time.sleep(1)

        
    new_record = (config['date'], fetch_input(args.filepath))
    chart_data = update_graph_data(config, new_record)
    sys.stdout.write(chart_config(config['api_key'], chart_data))


    #test:
    #data = [('2014-12-10', [{'count': '7', 'code': '200'}, {'count': '3', 'code': '204'}]),
    #        ('2014-12-11', [{'count': '9', 'code': '200'}, {'count': '1', 'code': '204'}]),
    #        ('2014-12-13', [{'count': '3', 'code': '200'}, {'count': '2', 'code': '204'}])]
    #unpacked = unpack_data(data)
