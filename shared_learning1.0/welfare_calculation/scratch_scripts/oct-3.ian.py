#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct  2 21:34:52 2022

@author: ianprado
"""


import numpy as np
from scipy.optimize import fsolve

delta=0.08
ti=[0,1,2,3,4,5,6,7,8,9,10]

#e_delta_t=[np.exp(delta*item) for item in t]

#L=sum(e_delta_t)
T=ti[-1]

vals=np.zeros(3)
m0=0.9997937369
c0=0.8002062631
lam=2.157668536

alpha=1/2
beta=1/alpha
b0=1 


def solve_y_at_t(inp,t):    
    k=m0+c0*np.exp(-lam*inp[0])
    y=(k/(1-alpha))**(-beta)*b0/delta*(np.exp(delta*t)-1)
    return inp[0]-y

#y_t=fsolve(solve_y_at_t,np.ones(1),(t,10))[0]
#cost=m0+c0*np.exp(-lam*y_t)

def y_t(f,ans,t):
    return fsolve(f,ans,t)[0]

yT = y_t(solve_y_at_t,np.ones(1),T)

def cost_at_y_t(yt):
    return m0+c0*np.exp(-lam*yt)

#Gam = m0*yT+c0/lam*(1-np.exp(-lam*yT))
    
#Gam = sum([cost_at_y_t(y_t(solve_y_at_t,np.ones(1),time)) for time in ti[1:]])
    
Gam = 35.286


num = 0
for time in range(1,11):
    num += np.exp(delta*time)/cost_at_y_t(y_t(solve_y_at_t,np.ones(1),time))
    
num = num - Gam
        
        
denom = (np.exp(delta*T)-1)/delta/4 - Gam
    
print(num/denom)