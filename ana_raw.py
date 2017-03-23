import sys
import os
import argparse
import re
import numpy as np
#from ROOT import TGraph, TCanvas
import matplotlib.pyplot as plt
import active_reset_preamp as preamp


def get_args():
    parser = argparse.ArgumentParser('active reset analysis')
    parser.add_argument('file',nargs=1, help='Data file.')
    parser.add_argument('--savename','-s', help='Save output including this name.')
    args = parser.parse_args()
    print( args )
    return args



    

def main():

    print('Reading file: ' + str(args.file))

    # read data into array
    #data_arr = np.loadtxt(args.file[0], skiprows=5)

    AI5 = []
    AI0 = []
    ts = []
    with open(args.file[0],'r') as f:
        for line in f:
            s = line.split(':')
            if len(s) != 5:
                print('line format is wrong "' + str(line) + '" \n -> skip')
                continue
            m = re.match('(.*)\s\{',s[0])
            if m != None:
                ts.append(float(m.group(1)))
            else:
                print('time format is wrong: ' + str(line) + ' s ' + str(s) + ' s[0] ' + str(s[0]))
                print(s[0])
                sys.exit(1)
            AI5.append(float(s[1].split()[0].rstrip(',')))
            AI0.append(float(s[3].split()[0].rstrip(',')))

    print('Got ' + str(len(ts)))

    qgset = preamp.qgset(np.array(AI5))
    
    
    fig1 = plt.figure(1, figsize=(12,12))
    ax1_221 = plt.subplot(311)
    plt.plot(AI5)
    #plt.scatter(data_arr[ind,3], data_arr[ind,4])
    #plt.xlabel('QGSET+/Switch source voltage (V)')
    plt.ylabel('AI5 (V)')
    #plt.text(0.1,0.85,'QRST_T+ = +0.47V', transform = ax1_221.transAxes)

    ax1_222 = plt.subplot(312)
    plt.plot(qgset)
    #plt.scatter(data_arr[ind,3], data_arr[ind,4])
    #plt.xlabel('QGSET+/Switch source voltage (V)')
    plt.ylabel('QGSET (V)')
    #plt.text(0.1,0.85,'QRST_T+ = +0.47V', transform = ax1_221.transAxes)

    ax1_222 = plt.subplot(313)
    plt.plot(AI0)
    #plt.scatter(data_arr[ind,3], data_arr[ind,4])
    #plt.xlabel('QGSET+/Switch source voltage (V)')
    plt.ylabel('OUT (V)')
    #plt.text(0.1,0.85,'QRST_T+ = +0.47V', transform = ax1_221.transAxes)

    if args.savename != None:
        plt.savefig('out_' + args.savename + '_' +  os.path.basename(os.path.splitext(args.file[0])[0]) + '.png')



    fig2 = plt.figure(2, figsize=(12,12))
    #ax2_221 = plt.subplot(111)
    n, bins, patches = plt.hist(AI0)
    #plt.xlabel('QGSET+/Switch source voltage (V)')
    plt.xlabel('OUT (V)')
    #plt.text(0.1,0.85,'QRST_T+ = +0.47V', transform = ax1_221.transAxes)


    if args.savename != None:
        plt.savefig('out_hist_' + args.savename + '_' +  os.path.basename(os.path.splitext(args.file[0])[0]) + '.png')

    
    plt.show()



if __name__ == '__main__':
    args = get_args()
    main()
