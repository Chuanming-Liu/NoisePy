import ASDFDBase
import numpy as np
import timeit
dset=ASDFDBase.noiseASDF('../COR_WUS.h5')
# dset.read_stationtxt_ind('/work3/leon/ancc-1.0-0/Station.lst', chans=['LHZ'])
# dset.read_xcorr('/work3/leon/ancc-1.0-0', pfx='COR')
# dset.xcorr_prephp(outdir='/work3/leon/PRE_PHP', mapfile='./MAPS/smpkolya_phv')


# try:
#     del dset.auxiliary_data.DISPbasic1
# except:
#     pass
# try:
#     del dset.auxiliary_data.DISPbasic2
# except:
#     pass
# try:
#     del dset.auxiliary_data.DISPpmf1
# except:
#     pass
# try:
#     del dset.auxiliary_data.DISPpmf2
# except:
#     pass
# dset.xcorr_aftan_mp(outdir='/work3/leon/WUS_workingdir', prephdir='/work3/leon/PRE_PHP_R', f77=True, nprocess=10)
# 
# try:
#     del dset.auxiliary_data.DISPpmf2interp
# except:
#     pass
# dset.interp_disp()
# dset.xcorr_raytomoinput(outdir='./ray_tomo_data')
# try:
#     del dset.auxiliary_data.FieldDISPpmf2interp
# except:
#     pass

try:
    del dset.auxiliary_data.DISPbasic1
except:
    pass
try:
    del dset.auxiliary_data.DISPbasic2
except:
    pass
try:
    del dset.auxiliary_data.DISPpmf1
except:
    pass
try:
    del dset.auxiliary_data.DISPpmf2
except:
    pass
dset.xcorr_aftan_mp(outdir='/work3/leon/WUS_workingdir', prephdir='/work3/leon/PRE_PHP_R', f77=True, nprocess=10)

try:
    del dset.auxiliary_data.DISPpmf2interp
except:
    pass
dset.interp_disp()
# dset.xcorr_raytomoinput(outdir='./ray_tomo_data')

# dset.xcorr_get_field()



import raytomo
dset=raytomo.RayTomoDataSet('./ray_tomo_WUS.h5')
# dset.set_input_parameters(minlon=235., maxlon=255., minlat=31., maxlat=50., data_pfx='raytomo_in_', smoothpfx='N_INIT_', qcpfx='QC_')
# dset.run_smooth(datadir='./ray_tomo_data', outdir='./ray_tomo_working_dir')
# dset.run_qc(outdir='./ray_tomo_working_dir', isotropic=False, anipara=1, alphaAni4=1000)
dset.run_qc(outdir='./ray_tomo_working_dir', isotropic=True, anipara=1, alphaAni4=1000)
# # 
# dset.get_data4plot(dataid='qc_run_0', period=12.)
# dset.plot_vel_iso(vmin=2.9, vmax=3.5, fastaxis=False, projection='global')
# dset.plot_vel_iso(vmin=3.5, vmax=4.0)
# dset.plot_fast_axis()
# dset.generate_corrected_map(dataid='qc_run_0', glbdir='./MAPS', outdir='./REG_MAPS')
# dset.plot_global_map(period=50., inglbpfx='./MAPS/smpkolya_phv_R')


# 
# import eikonaltomo
# # # 
# dset=eikonaltomo.EikonalTomoDataSet('./eikonal_tomo_WUS_mp.h5')
# # dset=eikonaltomo.EikonalTomoDataSet('./eikonal_tomo_WUS.h5')
# # dset.set_input_parameters(minlon=235., maxlon=255., minlat=31., maxlat=50., pers=np.array([12.]))
# # dset.set_input_parameters(minlon=235., maxlon=255., minlat=31., maxlat=50.)
# # dset.xcorr_eikonal_mp(inasdffname='../COR_WUS.h5', workingdir='./eikonal_working_mp', fieldtype='Tph', channel='ZZ', data_type='FieldDISPpmf2interp', nprocess=10)
# # #
# # # t1=timeit.default_timer()
# # dset.eikonal_stack()
# # # t2=timeit.default_timer()
# # # print t2-t1
# # dset.eikonal_stack()
# # # dset._get_lon_lat_arr('Eikonal_run_0')
# dset.get_data4plot(period=60.)
# dset.np2ma()
# dset.plot_vel_iso(vmin=3.7, vmax=4.2)
# # dset.plot_vel_iso(vmin=2.9, vmax=3.5)


# import eikonaltomo
# # 
# dset=eikonaltomo.EikonalTomoDataSet('./eikonal_tomo_WUS.h5')
# # dset.set_input_parameters(minlon=235., maxlon=255., minlat=31., maxlat=50., pers=np.array([12.]))
# # dset.set_input_parameters(minlon=235., maxlon=255., minlat=31., maxlat=50.)
# # myfield=dset.xcorr_eikonal(inasdffname='../COR_WUS.h5', workingdir='./eikonal_working', fieldtype='Tph', channel='ZZ', data_type='FieldDISPpmf2interp')
# #
# # t1=timeit.default_timer()
# # dset.eikonal_stack()
# # t2=timeit.default_timer()
# # print t2-t1
# # dset.eikonal_stack()
# # dset._get_lon_lat_arr('Eikonal_run_0')
# dset.get_data4plot(period=24.)
# dset.np2ma()
# dset.plot_vel_iso(vmin=3.4, vmax=4.0)


