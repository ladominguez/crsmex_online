from scipy import fftpack, signal
import numpy as np
import math
import cmath

def get_correlation_coefficient(S1, S2, dt):
    ''' signal mut be centered at p-wave arrival minus two seconds'''
    N = len(S1)
    Power_S1 = max(np.correlate(S1,S1))/N
    Power_S2 = max(np.correlate(S2,S2))/N

    if (Power_S1 == 0) or (Power_S2 == 0):
        CorrelationCoefficient = 0
        tshift                 = 0
    else:
        A = np.correlate(S1,S2,'full')/(N*np.sqrt(Power_S1*Power_S2))
        time2 = np.arange(-(N-1)*dt, N*dt, dt)
        CorrelationCoefficient = A.max()
        index = np.argmax(A)
        tshift = time2[index]
    
    return CorrelationCoefficient, tshift

def FFTshift(signal, delay):
    x = signal
    N = len(x)
    R = range(1,N+1)

    X = fftpack.fft(x)
    k = np.concatenate((range(0,int(math.floor(N/2))),range(int(math.floor(-N/2)),0)))
    W = np.exp(-cmath.sqrt(-1) * 2 * np.pi * delay * k / N)
    if N%2 == 0:
        W[int(N/2)] = W[int(N/2)].real

    Y = X*W
    y = fftpack.ifft(Y)
    y = y.real
    return y