import sys
import os
import argparse
import numpy as np
#from ROOT import TGraph, TCanvas
import matplotlib.pyplot as plt


Vss = 2.74
R_load = 1.6e3


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
    data_arr = np.loadtxt(args.file[0], skiprows=5)

    # read titles into array
    data_titles = None
    with open(args.file[0],'r') as f:
        for line in f:
            if 'AO_0' in line:
                data_titles = line.split()
    
    print(data_titles)
    print(data_arr)

    # calculate drain current
    Id_arr = (Vss - data_arr[:,6])/R_load


    #plot for fixed QRST_T+/AO_0
    #ind = np.where(data_arr[:,0] == 5.)
    ind = range(len(data_arr))
    
    fig1 = plt.figure(1, figsize=(12,12))
    ax1_221 = plt.subplot(221)
    plt.scatter(data_arr[ind,3], data_arr[ind,4])
    plt.xlabel('QGSET+/Switch source voltage (V)')
    plt.ylabel('OUT (V)')
    plt.text(0.1,0.85,'QRST_T+ = +0.47V', transform = ax1_221.transAxes)

    ax1_222 = plt.subplot(222)
    plt.scatter(data_arr[ind,3], data_arr[ind,6])
    plt.xlabel('QGSET+/Switch source voltage (V)')
    plt.ylabel('R31 (V)')
    plt.text(0.1,0.85,'QRST_T+ = +0.47V', transform = ax1_222.transAxes)

    ax1_223 = plt.subplot(223)
    plt.scatter(data_arr[ind,3], data_arr[ind,5])
    plt.xlabel('QGSET+/Switch source voltage (V)')
    plt.ylabel('HEMT Drain Voltage (V)')
    plt.text(0.1,0.85,'QRST_T+ = +0.47V', transform = ax1_223.transAxes)

    ax1_224 = plt.subplot(224)
    plt.scatter(data_arr[ind,3], Id_arr[ind]*1e3)
    plt.xlabel('QGSET+/Switch source voltage (V)')
    plt.ylabel('HEMT Drain Current (Vss-R31)/Rload (mA)')
    plt.text(0.1,0.85,'QRST_T+ = +0.47V', transform = ax1_224.transAxes)

    if args.savename != None:
        plt.savefig('fixed_qrst_' + args.savename + '_' +  os.path.splitext(args.file[0])[0] + '.png')


    fig2 = plt.figure(2,figsize=(12,12))
    ax2_221 = plt.subplot(111)
    plt.scatter(data_arr[ind,5], Id_arr[ind]*1e3)
    plt.xlabel('HEMT Drain Voltage (V)')
    plt.ylabel('HEMT Drain Current (Vss-R31)/Rload (mA)')
    plt.text(0.1,0.85,'QRST_T+ = +0.47V', transform = ax2_221.transAxes)

    if args.savename != None:
        plt.savefig('fixed_qrst_IV_' + args.savename + '_' +  os.path.splitext(args.file[0])[0] + '.png')

    plt.show()



    
    


if __name__ == "__main__":

    args = get_args()

    main()
