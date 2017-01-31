


def unit(x):
    return x

def qrst_tm(x):
    """ Linear fit to 
v(qrst_t-)
-0.668514
-0.445676
-0.222838
-4.34E-07
0.222837
0.445675

v(in)
0
1
2
3
4
5

"""
    return 0.2228*x - 0.6685


def qrst_tm_ao(y):
    """ Linear fit to 
v(qrst_t-)
-0.668514
-0.445676
-0.222838
-4.34E-07
0.222837
0.445675

v(in)
0
1
2
3
4
5

"""
    return (y - (-0.6685))/0.2228



def qgset(x):
    """ Linear fit to 
AVG(v(qgset))
-0.856534
-0.571023
-0.285511
-4.27E-07
0.285511
0.571022

v(in)
0
1
2
3
4
5

"""
    return 0.2855*x - 0.8565


def qgset_ao(y):
    """ Linear fit to 
AVG(v(qgset))
-0.856534
-0.571023
-0.285511
-4.27E-07
0.285511
0.571022

v(in)
0
1
2
3
4
5

"""
    return (y - (- 0.8565))/0.2855

