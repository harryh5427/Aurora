'''
Script to demonstrate the creation of an animation of an Aurora run, purely for visualization purposes. 

It is recommended to run this in IPython.
Note that you might need to run %matplotlib qt in IPython in order to enable the animation to run. 
'''

import numpy as np
import matplotlib.pyplot as plt; plt.ion()
import omfit_eqdsk
import pickle as pkl
import scipy,sys,os
import time

# Make sure that package home is added to sys.path
import sys
sys.path.append('../')
import aurora

namelist = aurora.default_nml.load_default_namelist()

# test for C-Mod:
namelist['device'] = 'CMOD'
namelist['shot'] = 1101014030
namelist['time'] = 1250 # ms


gfile_name=f'g{namelist["shot"]}.{str(namelist["time"]).zfill(5)}'


if os.path.exists(gfile_name):
    # fetch local g-file if available
    geqdsk = omfit_eqdsk.OMFITgeqdsk(gfile_name)
    print('Fetched local g-file')
else:
    # attempt to construct it via omfit_eqdsk if not available locally
    geqdsk = omfit_eqdsk.OMFITgeqdsk('').from_mdsplus(
        device=namelist['device'],shot=namelist['shot'],
        time=namelist['time'], SNAPfile='EFIT01',
        fail_if_out_of_range=False,time_diff_warning_threshold=20
    )
    # save g-file locally:
    geqdsk.save(raw=True)
    print('Saved g-file locally')


# example kinetic profiles
kin_profs = namelist['kin_profs']

with open('./test_kin_profs.pkl','rb') as f:
    ne_profs,Te_profs = pkl.load(f)

kin_profs['ne']['vals'] = ne_profs['ne']*1e14  # 10^20 m^-3 --> cm^-3
kin_profs['ne']['times'] = ne_profs['t']
rhop = kin_profs['ne']['rhop'] = ne_profs['rhop']
kin_profs['Te']['vals'] = Te_profs['Te']*1e3  # keV --> eV
kin_profs['Te']['times'] = Te_profs['t']
kin_profs['Te']['rhop'] = Te_profs['rhop']
kin_profs['Te']['decay'] = np.ones(len(Te_profs['Te']))*1.0

# set no sources of impurities
namelist['source_type'] = 'const'
namelist['Phi0'] = 1e24 #1.0

# Set up for 1 ion:
imp = namelist['imp'] = 'Ca' #'Ar' #'Ca'
namelist['Z_imp'] = 20 #18. #20.
namelist['imp_a'] = 40.078 #39.948  # 40.078

# Now get aurora setup dictionary
aurora_dict = aurora.utils.aurora_setup(namelist, geqdsk=geqdsk)

# choose transport coefficients
D_eff = 1e4 #cm^2/s
v_eff = -2e2 #cm/s

# # set transport coefficients to the right format
D_z = np.ones((len(aurora_dict['radius_grid']),1)) * D_eff
V_z = np.ones((len(aurora_dict['radius_grid']),1)) * v_eff
times_DV = [1.0]  # dummy

# set initial charge state distributions to ionization equilibrium (no transport)
out = aurora.utils.run_aurora(aurora_dict, times_DV, D_z, V_z) #, nz_init=nz_init.T)
nz, N_wall, N_div, N_pump, N_ret, N_tsu, N_dsu, N_dsul, rcld_rate, rclw_rate = out
nz = nz.transpose(2,1,0)

# convenient dictionary
res = {'nz': nz, 'time': aurora_dict['time_out'], 'rV': aurora_dict['radius_grid'], 
       'rhop': aurora_dict['rhop_grid'], 'ne':aurora_dict['ne'], 'Te':aurora_dict['Te']}


# now create animation
aurora.animate.animate_aurora(res['rhop'], res['time'], nz.transpose(1,2,0), xlabel=r'$\rho_p$', ylabel='t={:.4f} [s]', zlabel=r'$n_z$ [A.U.]', labels=[str(i) for i in np.arange(0,nz.shape[1])], plot_sum=True, save_filename='aurora_anim')