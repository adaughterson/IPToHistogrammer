from IP2TempHistogrammer import IP2TempHistogrammer
import argparse

# @brief Easily check whether bucket number is a positive integer
def check_negative(i):
    ivalue = int(i)
    if ivalue < 0:
         raise argparse.ArgumentTypeError("%s is an invalid positive int value" % i)
    return ivalue

parser = argparse.ArgumentParser()
parser.add_argument('infile', help='Input file for parsing out IP addresses.')
parser.add_argument('outfile', help='Output TSV file.')
parser.add_argument('buckets', help='The number of buckets to apply to the histogram.', type=check_negative)
args = parser.parse_args()
# Make new Histogrammer
ipth = IP2TempHistogrammer()
# Ask for Histogrammer to create TSV
try:
    ipth.createTSV(args.infile,args.outfile,int(args.buckets))
except Exception as e:
    print e.message
    exit(1)