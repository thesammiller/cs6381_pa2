import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
import pandas as pd
from pandas import DataFrame
from pprint import pprint

#CPU_BASE = ['whole', 'half', 'quarter']
#CPU_DICT = {'whole': 1, 'half': 0.5, 'quarter': 0.25}
#DIMENSIONS = [1000, 1500, 2000, 2500, 3000]
#FILENAMES = ['{cpu}/{cpu}_{dim}'.format(cpu=x, dim=y) for x in CPU_BASE for y in DIMENSIONS]

basename = 'map{map}_reduce{reduce}_rack{rack}'
basefile = 'metrics/metrics_{file}.csv'

FILENAMES = [basename.format(map=map, reduce=reduce, rack=rack)
             for map in [10, 20]
             for reduce in [2, 3]
             for rack in [1, 2, 3]]

#FILENAMES = [basename.format(map=10, reduce=2, rack=3),
#                basename.format(map=10, reduce=3, rack=1),
#             basename.format(map=10, reduce=3, rack=2),
#             basename.format(map=10, reduce=3, rack=3),
#             basename.format(map=20, reduce=3, rack=3)]

def build_data(filenames):
    filedata = {}
    for file in filenames:
        dfcolumns = pd.read_csv(basefile.format(file=file), nrows=1, delim_whitespace=True)
        df = pd.read_csv(basefile.format(file=file), header=None, skiprows=1, usecols = list(range(len(dfcolumns.columns))),
                            names=dfcolumns.columns)
        filedata[file] = df
    return filedata

def main():
    data = build_data(FILENAMES)

    dataSet = sorted(data.keys(), key=lambda x: str([n for n in x if n.isdigit()]))


    #fig = plt.figure()
    #ax = fig.add_subplot(111, projection="3d")

    #plt.plot(xaxis, yaxis) where xaxis and yaxis are lists
    plt.plot(dataSet, [data[f]['Total'].quantile(0.99) for f in dataSet])
    plt.xticks(rotation=30)

    fig = plt.figure()
    fig.savefig("average.png")
    plt.close(fig)

if __name__ == '__main__':
    main()


