# -*- coding: utf-8 -*-
"""
Created on Thu Sep 22 21:54:58 2022

@author: b9801
"""

import numpy as np
from scipy.optimize import fsolve

delta=0.08
t=[0,1,2,3,4,5,6,7,8,9,10]

e_delta_t=[np.exp(delta*item) for item in t]

L=sum(e_delta_t)
T=t[-1]

CDRphi=1.8
CDR1phi=1.7

def solve_simult(inp):
    
    m0=inp[0]
    c0=inp[1]
    lam=inp[2]
    
    out=np.zeros(3)
    out[0]=1-m0-c0*np.exp(-lam*L)
    out[1]=CDRphi-m0-c0
    out[2]=CDR1phi-m0-c0*np.exp(-lam*L*0.1)
    return out

vals=fsolve(solve_simult,np.ones(3))
m0=vals[0]
c0=vals[1]
lam=vals[2]

alpha=1/1.5
beta=1/alpha
b0=1 

def solve_monop(inp):    
    k=m0+c0*np.exp(-lam*inp[0])
    y=(k/(1-alpha))**(-beta)*b0/delta*(np.exp(delta*T)-1)
    return inp[0]-y

y=fsolve(solve_monop,np.ones(1))[0]
cost=m0+c0*np.exp(-lam*y)