import re
import requests
import os.path
#########################################
# @class WeatherHelpers
# @author J. Adam Daughterson
# Helper class with useful things for creating histograms.
class WeatherHelpers(object):
    def __init__(self):
        ip_reg = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
        # This could be much prettier, but it gets the job done for now...
        non_routable = r"\b(127\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})|(10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})|(172\.1[6-9]{1}[0-9]{0,1}\.[0-9]{1,3}\.[0-9]{1,3})|(172\.2[0-9]{1}[0-9]{0,1}\.[0-9]{1,3}\.[0-9]{1,3})|(172\.3[0-1]{1}[0-9]{0,1}\.[0-9]{1,3}\.[0-9]{1,3})|(192\.168\.[0-9]{1,3}\.[0-9]{1,3})\b"
        self.ip_reg = re.compile(ip_reg)
        self.non_routable_reg = re.compile(non_routable)
        self.log_dict = {}
    # @brief Find IP addresses in the file provided.
    # @param string infile The absolute path to the input file.
    # @returns set ips A set of unique IP addresses.
    def createIPSetFromFile(self, infile):
        # Search line-by-line for IP addresses
        # Add IP addresses to set.
        ips = set()
        try:
            if os.path.isfile(infile):
                lf = open(infile, 'r')
                for line in lf:
                    matched = self.ip_reg.findall(line)
                    # A match means an IP address was found, now try to obtain the geographical locale
                    #   based on the IP found in the line.
                    try:
                        ip = matched[0]
                        non_routable = self.non_routable_reg.findall(ip)
                        if non_routable:
                            self.log("Found a non-routable IP {}; skipping".format(ip),"ERROR")
                            continue
                        else:
                            ips.add(ip)
                    except IndexError as e:
                        fields = line.split()
                        # Empirically determined to be the correct field in this case.
                        # A better way to do this would be to infer the column using a matching group in the compiled regex.
                        thevalue = fields[22]
                        msg = "Found {} in log instead of IP address\n{}".format(thevalue,e)
                        self.log(msg,"ERROR")
                lf.close()
            else:
                raise Exception("File {} does not exist".format(infile))
        except Exception() as e:
            msg = "Exception when attempting to open infile {}\n{}".format(infile,e)
            raise Exception(msg)
        return ips

    # @brief Determine the latitude and longitute associated with an IP address.
    # @param string ip The IP address to look up.
    # @returns tuple lat,long The latitude and longitude of the IP address.
    def getLocale(self, ip):
        try:
            rq = requests.get('http://freegeoip.net/json/' + ip)
            rq_json = rq.json()
            lat, lon = rq_json['latitude'], rq_json['longitude']
            self.log("Found coordinates {} by {} for {}".format(lat,lon,ip),"Info")
        except Exception as e:
            msg = "Exception obtaining freegeoip JSON payload. {}".format(e)
            raise Exception(msg)
        return lat, lon

    # @brief Get the forecasted high temperature for the next calendar day.
    # @param tuple lat,long The latitude and longitude for the forecast.
    # @returns float ret_temp_f The max temperature in Fahrenheit.
    def getTomorrowsHighTemps(self, (lat, lon)):
        fcast_req = ''
        ret_temp = 0
        fcast_dict = {}
        # This call is using my own APPID for openweathermap
        # TODO: Use valid other license to openweathermap.org
        try:
            fcast_req = requests.get(
                'http://api.openweathermap.org/data/2.5/forecast/daily?lat={0}lat&lon={1}&APPID={2}&cnt=2'.format
                (lat, lon, '0e10b01037a08cb2b001e4b1340e3fda'))
            fcast_dict = fcast_req.json()
        except Exception as e:
            msg = "Unable to receive forecast from openweathermap\n{}\{}".format(e, fcast_req)
            self.log(msg, "ERROR")
            raise Exception(msg)
        if ('list' in fcast_dict):
            if (len(fcast_dict['list']) > 0):
                # By now we should have a nice list of timestamps to look through.
                dt_list = fcast_dict.get('list')[1]
                ret_temp = dt_list.get('temp')['max']

        ret_temp_f = self.k2f(ret_temp)
        return ret_temp_f

    # @brief Log/Print stuff
    def log(self, msg, facility):
        print(msg)
        if (None != self.log_dict.get(facility)):
            self.log_dict[facility].append(msg)
        else:
            self.log_dict[facility] = []
            self.log_dict[facility].append(msg)

    # @brief Getter for logged info.
    def getLogs(self,facility):
        return self.log_dict

    # @brief Convenience method to convert Kelvin to Fahrenheit.
    def k2f(self,t):
        return (t * 9 / 5.0) - 459.67
