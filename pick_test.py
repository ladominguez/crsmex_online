from obspy.core import read
from obspy.signal.trigger import ar_pick
from matplotlib import pyplot as plt

plt.rcParams["figure.figsize"] = (20, 3)


st = read('2022*sac')
st.detrend()
tr1 = st.select(channel='HHZ')[0]
tr2 = st.select(channel='HHE')[0]
tr3 = st.select(channel='HHN')[0]

df = tr1.stats.sampling_rate
f1 = 2.0       # Frequency of the lower bandpass window
f2 = 20      # Frequency of the lower bandpass window
lta_p = 1    # Length of LTA for the P arrival in seconds.
sta_p = 0.1  # Length of STA for the P arrival in seconds.
lta_s = 4    # Length of LTA for the S arrival in seconds.
sta_s = 1.0  # Length of STA for the S arrival in seconds.
m_p = 2      # Number of AR coefficients for the P arrival.
m_s = 8      # Number of AR coefficients for the S arrival.
l_p = 0.1    # Length of variance window for the P arrival in seconds.
l_s = 0.2   # Length of variance window for the S arrival in seconds.
s_pick = True  # If True, also pick the S phase, otherwise only the P phase.

p_pick, s_pick = ar_pick(tr1.data, tr2.data, tr3.data, df, f1, f2, lta_p,
                         sta_p, lta_s, sta_p, m_p, m_s, l_p, l_s, s_pick)

print('P: ', p_pick)
print('S: ', s_pick)
tr1.filter("highpass", freq=2.0)
plt.plot(tr1.times(), tr1.data, linewidth=0.2)
plt.plot([p_pick, p_pick], [-150, 150], color='red')
plt.plot([s_pick, s_pick], [-150, 150], color='blue')
plt.show()
