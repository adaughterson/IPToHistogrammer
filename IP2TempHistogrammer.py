import numpy as np
import csv
from WeatherHelpers import WeatherHelpers

# @class IP2TempHistogrammer
# @author J. Adam Daughterson
# Conveniently generate histograms of forecasted temperatures of geographical locations inferred from logged data
#       containing IP addresses.
# @prop set ips The set of unique IP addresses to work with.
# @prop list temps The list of temperatures to work with.
class IP2TempHistogrammer(object):
    def __init__(self):
        self.ips = set()
        self.temps = []
        self.edges = []
        self.whelpers = WeatherHelpers()


    # @brief Generates tuple of histogram buckets and edge data.
    # @param int buckets The number of buckets to apply to the histogram.
    # @returns dict hist_data Histogram data.
    def createHistogramData(self,infile,buckets):
        # Create IP Set
        try:
            self.ips = self.whelpers.createIPSetFromFile(infile)
        except Exception as e:
            print "Could not create IP Set from infile {}\n{}".format(infile,e)
        # Get locales, then determine their forecasted max temperatures
        # More of this functionality could be moved out of this method into something specific to getting IPs, temps, etc
        for ip in self.ips:
            # Get region tuple
            try:
                lat, lon = self.whelpers.getLocale(ip)
                if ((lat,lon) == (0,0)):
                    self.whelpers.log("GeoIP returned the North Pole; skipping IP {}".format(ip),'ERROR')
                    continue
            except Exception as e:
                msg = "Exception getting latitude and longitude for {}\n{}".format(ip,e)
                self.whelpers.log(msg,'ERROR')
                raise Exception(msg)
            # Get temp of region
            try:
                self.temps.append(self.whelpers.getTomorrowsHighTemps((lat, lon)))
            except Exception as e:
                msg = ("Exception getting high temperatures for coordinates: {} and {}\n{}".format(lat,lon,e))
                self.whelpers.log(msg,'ERROR')
                raise Exception(msg)
        # Feed NumPy
        try:
            hist,edges = np.histogram(self.temps, int(buckets))
        except Exception as e:
            msg = "Exception creating numpy histogram from data provided\n{}".format(e)
            self.whelpers.log(msg,'ERROR')
            raise Exception(msg)
        # Return histogram data
        return hist,edges

    # @brief Create a TSV file with temps in the correct buckets displayed in the following format:
    # | Minimum | Maximum | Count |
    # | 0       | 10      | 2     |
    # | 11.1234 | 24      | 9     |
    # ...
    def createTSV(self,infile,outfile,buckets):
        # Get the histogram data
        tsv_data = []
        try:
            self.hist,self.edges = self.createHistogramData(infile,buckets)
        except Exception as e:
            msg = ("Exception creating histogram data:\n{}".format(e))
            raise Exception(msg)
        self.hist.tolist()
        self.edges.tolist()
        i = 0
        last_edge = len(self.edges)-1
        minimum = 0
        maximum = 0
        count = 0
        while i < last_edge:
            count = self.hist[i]
            minimum = "{0:.2f}".format(self.edges[i])
            maximum = "{0:.2f}".format(self.edges[i+1])
            tsv_data.append((minimum,maximum,count))
            i += 1
        # Write that file
        with open(outfile, 'wb') as tsv_file:
            tmpdata = []
            fieldnames = ['Minimum','Maximum','Count']
            for values in tsv_data[0:]:
                inner_dict = dict(zip(fieldnames,values))
                tmpdata.append(inner_dict)
            writer = csv.DictWriter(tsv_file,delimiter="\t",fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(tmpdata)
        # Now print the summary of issues encountered
        # Ideally, I would put this into its own useful class, but for the sake of brevity I am leaving it here.
        summ_dict = self.whelpers.getLogs('ERROR')
        if summ_dict.get('ERROR'):
            for err in summ_dict.get('ERROR'):
                print "\nThe following issues were found:\n"
                print err