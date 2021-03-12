import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
import pandas as pd
from pandas import DataFrame
from pprint import pprint
import os
import time



FILENAMES = [x for x in os.listdir('logs') if 'seconds' in x]


def build_data(filenames):
    filedata = {}
    for file in filenames:
        df = pd.read_csv('logs/' + file, header=None, skiprows=1)
        filedata[file] = df
    return filedata

def parse_ip(seconds_log):
    pieces = seconds_log.split('.')
    # seconds10, 0, 0, x, log --> we want x
    # print(pieces)
    host = pieces[3]
    return int(host)

def main():
    data = build_data(FILENAMES)
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")

    for enum, file in enumerate(data):
        zaxis = data[file].quantile(0.90)
        ax.plot([enum]*len(data), range(len(data)), zaxis)

        #zaxis = [dataPoints[x].quantile(0.95) for x in range(1000, 3500, 500)]
        #ax.plot(xaxis, DIMENSIONS, [x[0] for x in zaxis[0:5]])

        #zaxis = [dataPoints[x].quantile(0.99) for x in range(1000, 3500, 500)]
        #ax.plot(xaxis, DIMENSIONS, [x[0] for x in zaxis[0:5]])

    dataSet = sorted(data.keys(), key=lambda x: parse_ip(x))



    timestamp = str(round(time.time()))[-5:]

    fig.savefig('quantile_{}.png'.format(timestamp))


if __name__ == '__main__':
    main()


