# -*- coding: utf-8 -*-
"""
A python wrapper to run Misha Barmin's straight ray surface wave tomography
The code creates a datadbase based on hdf5 data format

:Dependencies:
    numpy >=1.9.1
    matplotlib >=1.4.3
    h5py 
    
:Copyright:
    Author: Lili Feng
    Graduate Research Assistant
    CIEI, Department of Physics, University of Colorado Boulder
    email: lili.feng@colorado.edu
    
:References:
    Barmin, M. P., M. H. Ritzwoller, and A. L. Levshin. "A fast and reliable method for surface wave tomography."
            Monitoring the Comprehensive Nuclear-Test-Ban Treaty: Surface Waves. Birkh?user Basel, 2001. 1351-1375.
"""
import numpy as np
import numpy.ma as ma
import h5py
import os, shutil
from subprocess import call
from mpl_toolkits.basemap import Basemap, shiftgrid, cm
import matplotlib.pyplot as plt
from matplotlib.mlab import griddata
import colormaps
import obspy
import field2d_earth


# def _get_z(inz, inlat, inlon, outlat, outlon):
#     outz    = np.zeros(outlat.shape)
#     for ilat in xrange()
def discrete_cmap(N, base_cmap=None):
    """Create an N-bin discrete colormap from the specified input map"""
    # Note that if base_cmap is a string or None, you can simply do
    #    return plt.cm.get_cmap(base_cmap, N)
    # The following works for string, None, or a colormap instance:
    base = plt.cm.get_cmap(base_cmap)
    color_list = base(np.linspace(0, 1, N))
    cmap_name = base.name + str(N)
    return base.from_list(cmap_name, color_list, N)

class RayTomoDataSet(h5py.File):
    """
    =================================================================================================================
    version history:
        Dec 9th, 2016   - first version
    =================================================================================================================
    """
    def print_info(self):
        """
        Print information of the dataset.
        """
        outstr          = '================================= Surface wave ray tomography Database ==================================\n'
        try:
            outstr      += 'Input data prefix       - '+self.attrs['data_pfx']+'\n'
            outstr      += 'Smooth run prefix       - '+self.attrs['smoothpfx']+'\n'
            outstr      += 'QC run prefix           - '+self.attrs['qcpfx']+'\n'
            outstr      += 'Period(s):              - '+str(self.attrs['period_array'])+'\n'
            outstr      += 'Longitude range         - '+str(self.attrs['minlon'])+' ~ '+str(self.attrs['maxlon'])+'\n'
            outstr      += 'Latitude range          - '+str(self.attrs['minlat'])+' ~ '+str(self.attrs['maxlat'])+'\n'
            per_arr     = self.attrs['period_array']
        except:
            print 'Empty Database!'
            return
        outstr          += '----------------------------------------- Smooth run data -----------------------------------------------\n'
        nid             = 0
        while True:
            key         =  'smooth_run_%d' %nid
            if not key in self.keys():
                break
            nid         += 1
            subgroup    = self[key]
            outstr      += '$$$$$$$$$$$$$$$$$$$$$$$$$$$ Run id: '+key+' $$$$$$$$$$$$$$$$$$$$$$$$$$$\n'
            # check data of different periods
            for per in per_arr:
                per_key ='%g_sec' %per
                if not per_key in subgroup.keys():
                    outstr  += '%g sec NOT in the database !\n' %per
            outstr          += 'Channel                             - '+str(subgroup.attrs['channel'])+'\n'
            outstr          += 'datatype(ph: phase; gr: group)      - '+str(subgroup.attrs['datatype'])+'\n'
            outstr          += 'dlon, dlat                          - '+str(subgroup.attrs['dlon'])+', '+str(subgroup.attrs['dlat'])+'\n'
            outstr          += 'Step of integration                 - '+str(subgroup.attrs['step_of_integration'])+'\n'
            outstr          += 'Smoothing coefficient (alpha1)      - '+str(subgroup.attrs['alpha1'])+'\n'
            outstr          += 'Path density damping (alpha2)       - '+str(subgroup.attrs['alpha2'])+'\n'
            outstr          += 'radius of correlation (sigma)       - '+str(subgroup.attrs['sigma'])+'\n'
            outstr          += 'Comments                            - '+str(subgroup.attrs['comments'])+'\n'
        outstr  += '------------------------------------ Quality controlled run data ----------------------------------------\n'
        nid     = 0
        while True:
            key =  'qc_run_%d' %nid
            if not key in self.keys():
                break
            nid +=1
            subgroup=self[key]
            outstr      += '$$$$$$$$$$$$$$$$$$$$$$$$$$$ Run id: '+key+' $$$$$$$$$$$$$$$$$$$$$$$$$$$\n'
            # check data of different periods
            for per in per_arr:
                per_key = '%g_sec' %per
                if not per_key in subgroup.keys():
                    outstr  += '%g sec NOT in the database !\n' %per
            if subgroup.attrs['isotropic']:
                tempstr = 'isotropic'
            else:
                tempstr = 'anisotropic'
            outstr      += 'Smooth run id                       - '+str(subgroup.attrs['smoothid'])+'\n'
            outstr      += 'isotropic/anisotropic               - '+tempstr+'\n'
            outstr      += 'datatype(ph: phase; gr: group)      - '+str(subgroup.attrs['datatype'])+'\n'
            outstr      += 'wavetype(R: Rayleigh; L: Love)      - '+str(subgroup.attrs['wavetype'])+'\n'
            outstr      += 'Criteria factor/limit               - '+str(subgroup.attrs['crifactor'])+'/'+str(subgroup.attrs['crilimit'])+'\n'
            outstr      += 'dlon, dlat                          - '+str(subgroup.attrs['dlon'])+', '+str(subgroup.attrs['dlat'])+'\n'
            outstr      += 'Step of integration                 - '+str(subgroup.attrs['step_of_integration'])+'\n'
            outstr      += 'Size of main cell (degree)          - '+str(subgroup.attrs['lengthcell'])+'\n'
            if subgroup.attrs['isotropic']:
                outstr      += 'Smoothing coefficient (alpha)       - '+str(subgroup.attrs['alpha'])+'\n'
                outstr      += 'Path density damping (beta)         - '+str(subgroup.attrs['beta'])+'\n'
                outstr      += 'Gaussian damping (sigma)            - '+str(subgroup.attrs['sigma'])+'\n'
            if not subgroup.attrs['isotropic']:
                outstr      += 'Size of anisotropic cell (degree)   - '+str(subgroup.attrs['lengthcellAni'])+'\n'
                outstr      += 'Anisotropic paramter                - '+str(subgroup.attrs['anipara'])+'\n'
                outstr      += '0: isotropic'+'\n'
                outstr      += '1: 2 psi anisotropic'+'\n'
                outstr      += '2: 2&4 psi anisotropic '+'\n'
                outstr      += 'xZone                               - '+str(subgroup.attrs['xZone'])+'\n'
                outstr      += '0th smoothing coefficient(alphaAni0)- '+str(subgroup.attrs['alphaAni0'])+'\n'
                outstr      += '0th path density damping (betaAni0) - '+str(subgroup.attrs['betaAni0'])+'\n'
                outstr      += '0th Gaussian damping (sigmaAni0)    - '+str(subgroup.attrs['sigmaAni0'])+'\n'
                outstr      += '2rd smoothing coefficient(alphaAni2)- '+str(subgroup.attrs['alphaAni2'])+'\n'
                outstr      += '2rd Gaussian damping (sigmaAni2)    - '+str(subgroup.attrs['sigmaAni2'])+'\n'
                outstr      += '4th smoothing coefficient(alphaAni4)- '+str(subgroup.attrs['alphaAni4'])+'\n'
                outstr      += '4th Gaussian damping (sigmaAni4)    - '+str(subgroup.attrs['sigmaAni4'])+'\n'
            outstr      += 'Comments                            - '+str(subgroup.attrs['comments'])+'\n'
        outstr += '=========================================================================================================\n'
        print outstr
        return
    
    
    def set_input_parameters(self, minlon, maxlon, minlat, maxlat, pers=np.array([]), data_pfx='raytomo_in_', smoothpfx='N_INIT_', qcpfx='QC_'):
        """
        Set input parameters for tomographic inversion.
        =================================================================================================================
        ::: input parameters :::
        minlon, maxlon  - minimum/maximum longitude
        minlat, maxlat  - minimum/maximum latitude
        pers            - period array, default = np.append( np.arange(18.)*2.+6., np.arange(4.)*5.+45.)
        data_pfx        - input data file prefix
        smoothpfx       - prefix for smooth run files
        smoothpfx       - prefix for qc(quanlity controlled) run files
        =================================================================================================================
        """
        if pers.size==0:
            pers    = np.append( np.arange(18.)*2.+6., np.arange(4.)*5.+45.)
        self.attrs.create(name = 'period_array', data=pers, dtype='f')
        self.attrs.create(name = 'minlon', data=minlon, dtype='f')
        self.attrs.create(name = 'maxlon', data=maxlon, dtype='f')
        self.attrs.create(name = 'minlat', data=minlat, dtype='f')
        self.attrs.create(name = 'maxlat', data=maxlat, dtype='f')
        self.attrs.create(name = 'data_pfx', data=data_pfx)
        self.attrs.create(name = 'smoothpfx', data=smoothpfx)
        self.attrs.create(name = 'qcpfx', data=qcpfx)
        return
        
    def run_smooth(self, datadir, outdir, datatype='ph', channel='ZZ', dlon=0.5, dlat=0.5, stepinte=0.2, lengthcell=1.0, alpha1=3000, alpha2=100, sigma=500,
            runid=0, comments='', deletetxt=False, contourfname='./contour.ctr', IsoMishaexe='./TOMO_MISHA/itomo_sp_cu_shn', reshape=True):
        """
        run Misha's tomography code with large regularization parameters.
        This function is designed to do an inital test run, the output can be used to discard outliers in aftan results.
        =================================================================================================================
        ::: input parameters :::
        datadir/outdir      - data/output directory
        datatype            - ph: phase velocity inversion, gr: group velocity inversion
        channel             - channel for analysis (default: ZZ, xcorr ZZ component)
        dlon/dlat           - longitude/latitude interval
        stepinte            - step of integration (degree), works only for Gaussian method
        lengthcell          - size of main cell (degree)
        alpha1,alpha2,sigma - regularization parameters for isotropic tomography
                                alpha1  : smoothing coefficient
                                alpha2  : path density damping
                                sigma   : Gaussian smoothing (radius of correlation)
        runid               - id number for the run
        comments            - comments for the run
        deletetxt           - delete txt output or not
        contourfname        - path to contour file (see the manual for detailed description)
        IsoMishaexe         - path to Misha's Tomography code executable (isotropic version)
        ------------------------------------------------------------------------------------------------------------------
        input format:
        datadir/data_pfx+'%g'%( per ) +'_'+channel+'_'+datatype+'.lst' (e.g. datadir/raytomo_10_ZZ_ph.lst)
        e.g. datadir/MISHA_in_20.0_BHZ_BHZ_ph.lst
        
        output format:
        e.g. 
        prefix: outdir/10_ph/N_INIT_3000_500_100
        output file: outdir/10.0_ph/N_INIT_3000_500_100_10.0.1 etc. 
        =================================================================================================================
        """
        if not os.path.isfile(IsoMishaexe):
            raise AttributeError('IsoMishaexe does not exist!')
        if not os.path.isfile(contourfname):
            raise AttributeError('Contour file does not exist!')
        pers            = self.attrs['period_array']
        minlon          = self.attrs['minlon']
        maxlon          = self.attrs['maxlon']
        minlat          = self.attrs['minlat']
        maxlat          = self.attrs['maxlat']
        data_pfx        = self.attrs['data_pfx']
        smoothpfx       = self.attrs['smoothpfx']
        if not os.path.isdir(outdir):
            deleteall   = True
        #-----------------------------------------
        # run the tomography code for each period
        #-----------------------------------------
        print('================================= Smooth run of surface wave tomography ==================================')
        for per in pers:
            print('----------------------------------------------------------------------------------------------------------')
            print('----------------------------------------- T = '+str(per)+' sec ---------------------------------------------------')
            print('----------------------------------------------------------------------------------------------------------')
            infname     = datadir+'/'+data_pfx+'%g'%( per ) +'_'+channel+'_'+datatype+'.lst'
            outper      = outdir+'/'+'%g'%( per ) +'_'+datatype
            if not os.path.isdir(outper):
                os.makedirs(outper)
            outpfx      = outper+'/'+smoothpfx+str(alpha1)+'_'+str(sigma)+'_'+str(alpha2)
            temprunsh   = 'temp_'+'%g_Smooth.sh' %(per)
            with open(temprunsh,'wb') as f:
                f.writelines('%s %s %s %g <<-EOF\n' %(IsoMishaexe, infname, outpfx, per ))
                # if paraFlag==False:
                #     f.writelines('me \n' );
                f.writelines('me \n4 \n5 \n%g \n6 \n%g \n%g \n%g \n' %( alpha2, alpha1, sigma, sigma) )
                f.writelines('7 \n%g %g %g \n8 \n%g %g %g \n12 \n%g \n%g \n16 \n' %(minlat, maxlat, dlat, minlon, maxlon, dlon, stepinte, lengthcell) )
                # if paraFlag==False:
                #     f.writelines('v \n' );
                f.writelines('v \nq \ngo \nEOF \n' )
            call(['bash', temprunsh])
            os.remove(temprunsh)
        #-----------------------------------------
        # save results to hdf5 dataset
        #-----------------------------------------
        create_group        = False
        while (not create_group):
            try:
                group       = self.create_group( name = 'smooth_run_'+str(runid) )
                create_group= True
            except:
                runid       += 1
                continue
        group.attrs.create(name = 'comments', data=comments)
        group.attrs.create(name = 'dlon', data=dlon)
        group.attrs.create(name = 'dlat', data=dlat)
        group.attrs.create(name = 'step_of_integration', data=stepinte)
        group.attrs.create(name = 'datatype', data=datatype)
        group.attrs.create(name = 'channel', data=channel)
        group.attrs.create(name = 'alpha1', data=alpha1)
        group.attrs.create(name = 'alpha2', data=alpha2)
        group.attrs.create(name = 'sigma', data=sigma)
        for per in pers:
            subgroup    = group.create_group(name='%g_sec'%( per ))
            outper      = outdir+'/'+'%g'%( per ) +'_'+datatype
            outpfx      = outper+'/'+smoothpfx+str(alpha1)+'_'+str(sigma)+'_'+str(alpha2)
            # absolute velocity
            v0fname     = outpfx+'_%g.1' %(per)
            inArr       = np.loadtxt(v0fname)
            v0Arr       = inArr[:,2]
            v0dset      = subgroup.create_dataset(name='velocity', data=v0Arr)
            # relative velocity perturbation
            dvfname     = outpfx+'_%g.1' %(per)+'_%_'
            inArr       = np.loadtxt(dvfname)
            dvArr       = inArr[:,2]
            dvdset      = subgroup.create_dataset(name='Dvelocity', data=dvArr)
            # azimuthal coverage
            azifname    = outpfx+'_%g.azi' %(per)
            inArr       = np.loadtxt(azifname)
            aziArr      = inArr[:,2:4]
            azidset     = subgroup.create_dataset(name='azi_coverage', data=aziArr)
            # residual file
            # id fi0 lam0 f1 lam1 vel_obs weight res_tomo res_mod delta
            residfname  = outpfx+'_%g.resid' %(per)
            inArr       = np.loadtxt(residfname)
            residdset   = subgroup.create_dataset(name='residual', data=inArr)
            # path density file
            resfname    = outpfx+'_%g.res' %(per)
            inArr       = np.loadtxt(resfname)
            resArr      = inArr[:,2:]
            resdset     = subgroup.create_dataset(name='path_density', data=resArr)
            if deletetxt:
                shutil.rmtree(outper)
        if deletetxt and deleteall:
            shutil.rmtree(outdir)
        if reshape:
            self.creat_reshape_data(runtype=0, runid=runid)
        print('================================= End mooth run of surface wave tomography ===============================')
        return
    
    def run_qc(self, outdir, runid=0, smoothid=0, datatype='ph', wavetype='R', crifactor=0.5, crilimit=10.,
               dlon=0.5, dlat=0.5, stepinte=0.1, lengthcell=0.5,  isotropic=False, alpha=850, beta=1, sigma=175, \
                lengthcellAni=1.0, anipara=0, xZone=2, alphaAni0=1200, betaAni0=1, sigmaAni0=200, alphaAni2=1000, sigmaAni2=100, alphaAni4=1200, sigmaAni4=500,\
                comments='', deletetxt=False, contourfname='./contour.ctr',  IsoMishaexe='./TOMO_MISHA/itomo_sp_cu_shn', \
                AniMishaexe='./TOMO_MISHA_AZI/tomo_sp_cu_s_shn_.1', reshape=True):
        """
        run Misha's tomography code with quality control based on preliminary run of run_smooth.
        This function is designed to discard outliers in aftan results (quality control), and then do tomography.
        =================================================================================================================
        ::: input parameters :::
        outdir              - output directory
        smoothid            - smooth run id number
        datatype            - data type
                                ph      : phase velocity inversion
                                gr      : group velocity inversion
        wavetype            - wave type
                                R       : Rayleigh
                                L       : Love
        crifactor/crilimit  - criteria for quality control
                                largest residual is min( crifactor*period, crilimit)
        isotropic           - use isotropic or anisotropic version
        -----------------------------------------------------------------------------------------------------------------
        :   shared input parameters :
        dlon/dlat           - longitude/latitude interval
        stepinte            - step of integration, works only for Gaussian method
        lengthcell          - size of isotropic cell (degree)
        -----------------------------------------------------------------------------------------------------------------
        :   isotropic input parameters :
        alpha,beta,sigma    - regularization parameters for isotropic tomography (isotropic==True)
                                alpha   : smoothing coefficient
                                beta    : path density damping
                                sigma   : Gaussian smoothing (radius of correlation)
        -----------------------------------------------------------------------------------------------------------------
        :   anisotropic input parameters :
        lengthcellAni       - size of anisotropic cell (degree)
        anipara             - anisotropic paramter
                                0   - isotropic
                                1   - 2 psi anisotropic
                                2   - 2&4 psi anisotropic
        xZone               - Fresnel zone parameter, works only for Fresnel method
        alphaAni0,betaAni0,sigmaAni0 
                            - regularization parameters for isotropic term in anisotropic tomography  (isotropic==False)
                                alphaAni0   : smoothing coefficient
                                betaAni0    : path density damping
                                sigmaAni0   : Gaussian smoothing
        alphaAni2,sigmaAni2 - regularization parameters for 2 psi term in anisotropic tomography  (isotropic==False)
                                alphaAni2   : smoothing coefficient
                                sigmaAni2   : Gaussian smoothing
        alphaAni4,sigmaAni4 - regularization parameters for 4 psi term in anisotropic tomography  (isotropic==False)
                                alphaAni4   : smoothing coefficient
                                sigmaAni4   : Gaussian smoothing                
        -----------------------------------------------------------------------------------------------------------------
        comments            - comments for the run
        deletetxt           - delete txt output or not
        contourfname        - path to contour file (see the manual for detailed description)
        IsoMishaexe         - path to Misha's Tomography code executable (isotropic version)
        AniMishaexe         - path to Misha's Tomography code executable (anisotropic version)
        ------------------------------------------------------------------------------------------------------------------
        intermediate output format:
        outdir+'/'+per+'_'+datatype+'/QC_'+per+'_'+wavetype+'_'+datatype+'.lst'
        e.g. outdir/10_ph/QC_10_R_ph.lst
        
        Output format:
        e.g. 
        prefix: outdir/10_ph/QC_850_175_1  OR outdir/10_ph/QC_AZI_R_1200_200_1000_100_1
        
        Output file:
        outdir/10_ph/QC_850_175_1_10.1 etc. 
        OR
        outdir/10_ph/QC_AZI_R_1200_200_1000_100_1_10.1 etc. (see the manual for detailed description of output suffix)
        =================================================================================================================
        """
        pers            = self.attrs['period_array']
        minlon          = self.attrs['minlon']
        maxlon          = self.attrs['maxlon']
        minlat          = self.attrs['minlat']
        maxlat          = self.attrs['maxlat']
        smoothpfx       = self.attrs['smoothpfx']
        qcpfx           = self.attrs['qcpfx']
        if isotropic:
            mishaexe    = IsoMishaexe
        else:
            mishaexe    = AniMishaexe
            qcpfx       = qcpfx+'AZI_'
        contourfname    = './contour.ctr'
        if not os.path.isfile(mishaexe):
            raise AttributeError('mishaexe does not exist!')
        if not os.path.isfile(contourfname):
            raise AttributeError('Contour file does not exist!')
        smoothgroup     = self['smooth_run_'+str(smoothid)]
        for per in pers:
            #------------------------------------------------
            # quality control based on smooth run results
            #------------------------------------------------
            try:
                residdset   = smoothgroup['%g_sec'%( per )+'/residual']
                # id fi0 lam0 f1 lam1 vel_obs weight res_tomo res_mod delta
                inArr       = residdset.value
            except:
                raise AttributeError('Residual data: '+ str(per)+ ' sec does not exist!')
            res_tomo        = inArr[:,7]
            cri_res         = min(crifactor*per, crilimit)
            QC_arr          = inArr[np.abs(res_tomo)<cri_res, :]
            outArr          = QC_arr[:,:8]
            outper          = outdir+'/'+'%g'%( per ) +'_'+datatype
            if not os.path.isdir(outper):
                os.makedirs(outper)
            # old format in defined in the manual
            QCfname         = outper+'/QC_'+'%g'%( per ) +'_'+wavetype+'_'+datatype+'.lst'
            np.savetxt(QCfname, outArr, fmt='%g')
            #------------------------------------------------
            # start to run tomography code
            #------------------------------------------------
            if isotropic:
                outpfx      = outper+'/'+qcpfx+str(alpha)+'_'+str(sigma)+'_'+str(beta)
            else:
                outpfx      = outper+'/'+qcpfx+wavetype+'_'+str(alphaAni0)+'_'+str(sigmaAni0)+'_'+str(alphaAni2)+'_'+str(sigmaAni2)+'_'+str(betaAni0)
            temprunsh       = 'temp_'+'%g_QC.sh' %(per)
            with open(temprunsh,'wb') as f:
                f.writelines('%s %s %s %g << EOF \n' %(mishaexe, QCfname, outpfx, per ))
                if isotropic:
                    f.writelines('me \n4 \n5 \n%g \n6 \n%g \n%g \n%g \n' %( beta, alpha, sigma, sigma) ) # 100 --> 1., 3000. --> 850., 500. --> 175.
                    f.writelines('7 \n%g %g %g \n8 \n%g %g %g \n12 \n%g \n%g \n16 \n' %(minlat, maxlat, dlat, minlon, maxlon, dlon, stepinte, lengthcell) )
                    f.writelines('v \nq \ngo \nEOF \n' )
                else:
                    if datatype=='ph':
                        Dtype   = 'P'
                    else:
                        Dtype   = 'G'
                    f.writelines('me \n4 \n5 \n%g %g %g \n6 \n%g %g %g \n' %( minlat, maxlat, dlat, minlon, maxlon, dlon) )
                    f.writelines('10 \n%g \n%g \n%s \n%s \n%g \n%g \n11 \n%d \n' %(stepinte, xZone, wavetype, Dtype, lengthcell, lengthcellAni, anipara) )
                    f.writelines('12 \n%g \n%g \n%g \n%g \n' %(alphaAni0, betaAni0, sigmaAni0, sigmaAni0) ) # 100 --> 1., 3000. --> 1200., 500. --> 200.
                    f.writelines('13 \n%g \n%g \n%g \n' %(alphaAni2, sigmaAni2, sigmaAni2) )
                    if anipara==2:
                        f.writelines('14 \n%g \n%g \n%g \n' %(alphaAni4, sigmaAni4, sigmaAni4) )
                    f.writelines('19 \n25 \n' )
                    f.writelines('v \nq \ngo \nEOF \n' )
            call(['bash', temprunsh])
            os.remove(temprunsh)
        #------------------------------------------------
        # save to hdf5 dataset
        #------------------------------------------------
        create_group        = False
        while (not create_group):
            try:
                group       = self.create_group( name = 'qc_run_'+str(runid) )
                create_group= True
            except:
                runid       += 1
                continue
        group.attrs.create(name = 'isotropic', data=isotropic)
        group.attrs.create(name = 'datatype', data=datatype)
        group.attrs.create(name = 'wavetype', data=wavetype)
        group.attrs.create(name = 'crifactor', data=crifactor)
        group.attrs.create(name = 'crilimit', data=crilimit)
        group.attrs.create(name = 'dlon', data=dlon)
        group.attrs.create(name = 'dlat', data=dlat)
        group.attrs.create(name = 'step_of_integration', data=stepinte)
        group.attrs.create(name = 'lengthcell', data=lengthcell)
        group.attrs.create(name = 'alpha', data=alpha)
        group.attrs.create(name = 'beta', data=beta)
        group.attrs.create(name = 'sigma', data=sigma)
        group.attrs.create(name = 'lengthcellAni', data=lengthcellAni)
        group.attrs.create(name = 'anipara', data=anipara)
        group.attrs.create(name = 'xZone', data=xZone)
        group.attrs.create(name = 'alphaAni0', data=alphaAni0)
        group.attrs.create(name = 'betaAni0', data=betaAni0)
        group.attrs.create(name = 'sigmaAni0', data=sigmaAni0)
        group.attrs.create(name = 'alphaAni2', data=alphaAni2)
        group.attrs.create(name = 'sigmaAni2', data=sigmaAni2)
        group.attrs.create(name = 'alphaAni4', data=alphaAni4)
        group.attrs.create(name = 'sigmaAni4', data=sigmaAni4)
        group.attrs.create(name = 'comments', data=comments)
        group.attrs.create(name = 'smoothid', data='smooth_run_'+str(smoothid))
        for per in pers:
            subgroup    = group.create_group(name='%g_sec'%( per ))
            outper      = outdir+'/'+'%g'%( per ) +'_'+datatype
            if isotropic:
                outpfx  = outper+'/'+qcpfx+str(alpha)+'_'+str(sigma)+'_'+str(beta)
            else:
                outpfx  = outper+'/'+qcpfx+wavetype+'_'+str(alphaAni0)+'_'+str(sigmaAni0)+'_'+str(alphaAni2)+'_'+str(sigmaAni2)+'_'+str(betaAni0)
            # absolute velocity
            v0fname     = outpfx+'_%g.1' %(per)
            inArr       = np.loadtxt(v0fname)
            v0Arr       = inArr[:,2:]
            v0dset      = subgroup.create_dataset(name='velocity', data=v0Arr)
            # longitude-latitude array
            if not isotropic:
                lonlatArr   = inArr[:,:2]
                lonlatdset  = subgroup.create_dataset(name='lons_lats', data=lonlatArr)
            # relative velocity perturbation
            dvfname     = outpfx+'_%g.1' %(per)+'_%_'
            inArr       = np.loadtxt(dvfname)
            dvArr       = inArr[:,2]
            dvdset      = subgroup.create_dataset(name='Dvelocity', data=dvArr)
            # azimuthal coverage
            # lon, lat, meth1, meth2
            azifname    = outpfx+'_%g.azi' %(per)
            inArr       = np.loadtxt(azifname)
            aziArr      = inArr[:,2:]
            azidset     = subgroup.create_dataset(name='azi_coverage', data=aziArr)
            # residual file
            # isotropic     : id fi0 lam0 f1 lam1 vel_obs weight res_tomo res_mod delta
            # anisotropic   : id fi0 lam0 f1 lam1 vel_obs weight orb res_tomo res_mod delta
            residfname  = outpfx+'_%g.resid' %(per)
            inArr       = np.loadtxt(residfname)
            residdset   = subgroup.create_dataset(name='residual', data=inArr)
            # resoluation analysis results
            reafname        = outpfx+'_%g.rea' %(per)
            if not isotropic:
                inArr           = np.loadtxt(reafname)
                reaArr          = inArr[:,2:]
                readset         = subgroup.create_dataset(name='resolution', data=reaArr)
                lonlatArr       = inArr[:,:2]
                lonlatdset_rea  = subgroup.create_dataset(name='lons_lats_rea', data=lonlatArr)
            # path density file
            # lon lat dens (dens1 dens2)
            resfname    = outpfx+'_%g.res' %(per)
            inArr       = np.loadtxt(resfname)
            resArr      = inArr[:,2:]
            resdset     = subgroup.create_dataset(name='path_density', data=resArr)
            if deletetxt:
                shutil.rmtree(outper)
        if deletetxt and deleteall:
            shutil.rmtree(outdir)
        if reshape:
            self.creat_reshape_data(runtype=1, runid=runid)
        return
    
    def creat_reshape_data(self, runtype=0, runid=0):
        """
        convert data to Nlat * Nlon shape and store the mask
        =================================================================================================================
        ::: input parameters :::
        runtype         - type of run (0 - smooth run, 1 - quality controlled run)
        runid           - id of run
        =================================================================================================================
        """
        rundict     = {0: 'smooth_run', 1: 'qc_run'}
        dataid      = rundict[runtype]+'_'+str(runid)
        ingroup     = self[dataid]
        pers        = self.attrs['period_array']
        self._get_lon_lat_arr(dataid=dataid)
        ingrp       = self[dataid]
        outgrp      = self.create_group( name = 'reshaped_'+dataid)
        if runtype == 1:
            isotropic   = ingrp.attrs['isotropic']
            outgrp.attrs.create(name = 'isotropic', data=isotropic)
        else:
            isotropic   = True
        #-----------------
        # mask array
        #-----------------
        if not isotropic:
            mask1       = np.ones((self.Nlat, self.Nlon), dtype=np.bool)
            mask2       = np.ones((self.Nlat, self.Nlon), dtype=np.bool)
            tempgrp     = ingrp['%g_sec'%( pers[0] )]
            # get value for mask1 array
            lonlat_arr1 = tempgrp['lons_lats'].value
            inlon       = lonlat_arr1[:,0]
            inlat       = lonlat_arr1[:,1]
            for i in range(inlon.size):
                lon                         = inlon[i]
                lat                         = inlat[i]
                # index                       = np.where((self.lonArr==lon)*(self.latArr==lat))
                index                       = np.where((abs(self.lonArr-lon)<0.001)*(abs(self.latArr-lat)<0.001))
                mask1[index[0], index[1]]   = False
            # get value for mask2 array
            lonlat_arr2 = tempgrp['lons_lats_rea'].value
            inlon       = lonlat_arr2[:,0]
            inlat       = lonlat_arr2[:,1]
            for i in range(inlon.size):
                lon                         = inlon[i]
                lat                         = inlat[i]
                # index                       = np.where((self.lonArr==lon)*(self.latArr==lat))
                index                       = np.where((abs(self.lonArr-lon)<0.001)*(abs(self.latArr-lat)<0.001))
                mask2[index[0], index[1]]   = False
            outgrp.create_dataset(name='mask1', data=mask1)
            outgrp.create_dataset(name='mask2', data=mask2)
            index1      = np.logical_not(mask1)
            index2      = np.logical_not(mask2)
            anipara     = ingroup.attrs['anipara']
        # loop over periods
        for per in pers:
            # get data
            pergrp  = ingrp['%g_sec'%( per )]
            try:
                velocity        = pergrp['velocity'].value
                dv              = pergrp['Dvelocity'].value
                azicov          = pergrp['azi_coverage'].value
                pathden         = pergrp['path_density'].value
                if not isotropic:
                    resol       = pergrp['resolution'].value
            except:
                raise AttributeError(str(per)+ ' sec data does not exist!')
            # save data
            opergrp         = outgrp.create_group(name='%g_sec'%( per ))
            if isotropic:
                # velocity
                outv        = velocity.reshape(self.Nlat, self.Nlon)
                v0dset      = opergrp.create_dataset(name='velocity', data=outv)
                v0dset.attrs.create(name='Nlat', data=self.Nlat)
                v0dset.attrs.create(name='Nlon', data=self.Nlon)
                # relative velocity perturbation
                outdv       = dv.reshape(self.Nlat, self.Nlon)
                dvdset      = opergrp.create_dataset(name='Dvelocity', data=outdv)
                dvdset.attrs.create(name='Nlat', data=self.Nlat)
                dvdset.attrs.create(name='Nlon', data=self.Nlon)
                # azimuthal coverage, squared sum
                outazicov   = (azicov[:, 0]).reshape(self.Nlat, self.Nlon)
                azidset     = opergrp.create_dataset(name='azi_coverage1', data=outazicov)
                azidset.attrs.create(name='Nlat', data=self.Nlat)
                azidset.attrs.create(name='Nlon', data=self.Nlon)
                # azimuthal coverage, max value
                outazicov   = (azicov[:, 1]).reshape(self.Nlat, self.Nlon)
                azidset     = opergrp.create_dataset(name='azi_coverage2', data=outazicov)
                azidset.attrs.create(name='Nlat', data=self.Nlat)
                azidset.attrs.create(name='Nlon', data=self.Nlon)
                # path density
                outpathden  = pathden.reshape(self.Nlat, self.Nlon)
                pddset      = opergrp.create_dataset(name='path_density', data=outpathden)
                pddset.attrs.create(name='Nlat', data=self.Nlat)
                pddset.attrs.create(name='Nlon', data=self.Nlon)
            else:
                # isotropic velocity
                outv_iso        = np.zeros((self.Nlat, self.Nlon), dtype=np.float64)
                outv_iso[index1]= velocity[:, 0]
                v0dset          = opergrp.create_dataset(name='vel_iso', data=outv_iso)
                v0dset.attrs.create(name='Nlat', data=self.Nlat)
                v0dset.attrs.create(name='Nlon', data=self.Nlon)
                # relative velocity perturbation
                outdv           = np.zeros((self.Nlat, self.Nlon), dtype=np.float64)
                outdv[index1]   = dv
                dvdset          = opergrp.create_dataset(name='dv', data=outdv)
                dvdset.attrs.create(name='Nlat', data=self.Nlat)
                dvdset.attrs.create(name='Nlon', data=self.Nlon)
                if anipara != 0:
                    # azimuthal amplitude for 2psi
                    outamp2         = np.zeros((self.Nlat, self.Nlon), dtype=np.float64)
                    outamp2[index1] = velocity[:, 3]
                    amp2dset        = opergrp.create_dataset(name='amp2', data=outamp2)
                    amp2dset.attrs.create(name='Nlat', data=self.Nlat)
                    amp2dset.attrs.create(name='Nlon', data=self.Nlon)
                    # psi2
                    outpsi2         = np.zeros((self.Nlat, self.Nlon), dtype=np.float64)
                    outpsi2[index1] = velocity[:, 4]
                    psi2dset        = opergrp.create_dataset(name='psi2', data=outpsi2)
                    psi2dset.attrs.create(name='Nlat', data=self.Nlat)
                    psi2dset.attrs.create(name='Nlon', data=self.Nlon)
                if anipara == 2:
                    # azimuthal amplitude for 4psi
                    outamp4         = np.zeros((self.Nlat, self.Nlon), dtype=np.float64)
                    outamp4[index1] = velocity[:, 7]
                    amp4dset        = opergrp.create_dataset(name='amp4', data=outamp4)
                    amp4dset.attrs.create(name='Nlat', data=self.Nlat)
                    amp4dset.attrs.create(name='Nlon', data=self.Nlon)
                    # psi4
                    outpsi4         = np.zeros((self.Nlat, self.Nlon), dtype=np.float64)
                    outpsi4[index1] = velocity[:, 8]
                    psi4dset        = opergrp.create_dataset(name='psi4', data=outpsi4)
                    psi4dset.attrs.create(name='Nlat', data=self.Nlat)
                    psi4dset.attrs.create(name='Nlon', data=self.Nlon)
                # azimuthal coverage, squared sum
                outazicov           = np.zeros((self.Nlat, self.Nlon), dtype=np.float64)
                outazicov[index1]   = azicov[:, 0]
                azidset             = opergrp.create_dataset(name='azi_coverage1', data=outazicov)
                azidset.attrs.create(name='Nlat', data=self.Nlat)
                azidset.attrs.create(name='Nlon', data=self.Nlon)
                # azimuthal coverage, max value
                outazicov           = np.zeros((self.Nlat, self.Nlon), dtype=np.float64)
                outazicov[index1]   = azicov[:, 1]
                azidset             = opergrp.create_dataset(name='azi_coverage2', data=outazicov)
                azidset.attrs.create(name='Nlat', data=self.Nlat)
                azidset.attrs.create(name='Nlon', data=self.Nlon)
                # path density, all orbits
                outpathden          = np.zeros((self.Nlat, self.Nlon), dtype=np.float64)
                outpathden[index1]  = pathden[:, 0]
                pddset              = opergrp.create_dataset(name='path_density', data=outpathden)
                pddset.attrs.create(name='Nlat', data=self.Nlat)
                pddset.attrs.create(name='Nlon', data=self.Nlon)
                # path density, first orbit
                outpathden          = np.zeros((self.Nlat, self.Nlon), dtype=np.float64)
                outpathden[index1]  = pathden[:, 1]
                pddset              = opergrp.create_dataset(name='path_density1', data=outpathden)
                pddset.attrs.create(name='Nlat', data=self.Nlat)
                pddset.attrs.create(name='Nlon', data=self.Nlon)
                # path density, second orbit
                outpathden          = np.zeros((self.Nlat, self.Nlon), dtype=np.float64)
                outpathden[index1]  = pathden[:, 2]
                pddset              = opergrp.create_dataset(name='path_density2', data=outpathden)
                pddset.attrs.create(name='Nlat', data=self.Nlat)
                pddset.attrs.create(name='Nlon', data=self.Nlon)
                # resolution analysis, cone radius
                outrea              = np.zeros((self.Nlat, self.Nlon), dtype=np.float64)
                outrea[index2]      = resol[:, 0]
                readset             = opergrp.create_dataset(name='cone_radius', data=outrea)
                readset.attrs.create(name='Nlat', data=self.Nlat)
                readset.attrs.create(name='Nlon', data=self.Nlon)
                # resolution analysis, Gaussian std
                outrea              = np.zeros((self.Nlat, self.Nlon), dtype=np.float64)
                outrea[index2]      = resol[:, 1]
                readset             = opergrp.create_dataset(name='gauss_std', data=outrea)
                readset.attrs.create(name='Nlat', data=self.Nlat)
                readset.attrs.create(name='Nlon', data=self.Nlon)
                # resolution analysis, maximum response value
                outrea              = np.zeros((self.Nlat, self.Nlon), dtype=np.float64)
                outrea[index2]      = resol[:, 2]
                readset             = opergrp.create_dataset(name='max_resp', data=outrea)
                readset.attrs.create(name='Nlat', data=self.Nlat)
                readset.attrs.create(name='Nlon', data=self.Nlon)
                # resolution analysis, number of cells involvec in cone base
                outrea              = np.zeros((self.Nlat, self.Nlon), dtype=np.float64)
                outrea[index2]      = resol[:, 3]
                readset             = opergrp.create_dataset(name='ncone', data=outrea)
                readset.attrs.create(name='Nlat', data=self.Nlat)
                readset.attrs.create(name='Nlon', data=self.Nlon)
                # resolution analysis, number of cells involvec in Gaussian construction
                outrea              = np.zeros((self.Nlat, self.Nlon), dtype=np.float64)
                outrea[index2]      = resol[:, 4]
                readset             = opergrp.create_dataset(name='ngauss', data=outrea)
                readset.attrs.create(name='Nlat', data=self.Nlat)
                readset.attrs.create(name='Nlon', data=self.Nlon)
        return
    
    def get_uncertainty(self, ineikfname, runid=0, percentage=None, num_thresh=None, inrunid=0, gausspercent=1.):
        dataid      = 'reshaped_qc_run_'+str(runid)
        pers        = self.attrs['period_array']
        grp         = self[dataid]
        isotropic   = grp.attrs['isotropic']
        org_grp     = self['qc_run_'+str(runid)]
        if isotropic:
            print 'isotropic inversion results do not output gaussian std!'
            return
        indset      = h5py.File(ineikfname)
        inpers      = indset.attrs['period_array']
        indataid    = 'Eikonal_stack_'+str(inrunid)
        ingrp       = indset[indataid]
        if self.attrs['minlon'] != indset.attrs['minlon'] or \
            self.attrs['maxlon'] != indset.attrs['maxlon'] or \
                self.attrs['minlat'] != indset.attrs['minlat'] or \
                    self.attrs['maxlat'] != indset.attrs['maxlat'] or \
                        org_grp.attrs['dlon'] != indset.attrs['dlon'] or \
                            org_grp.attrs['dlat'] != indset.attrs['dlat']:
            raise ValueError('Incompatible input eikonal datasets!')
        mask        = grp['mask2']
        for per in pers:
            #-------------------------------
            # get data
            #-------------------------------
            pergrp      = grp['%g_sec'%( per )]
            mgauss      = pergrp['gauss_std'].value
            index       = np.logical_not(mask)
            mgauss2     = mgauss[index]
            gstdmin     = mgauss2.min()
            ind_gstdmin = (mgauss==gstdmin*gausspercent)*index
            #-------------------------------
            # get data from eikonal dataset
            #-------------------------------
            inpergrp    = ingrp['%g_sec'%( per )]
            inmask      = inpergrp['mask'].value
            invel_sem   = inpergrp['vel_sem'].value
            Nmeasure    = np.zeros(inmask.shape)
            Nmeasure[1:-1, 1:-1]\
                        = inpergrp['NmeasureQC'].value
            index_in    = np.logical_not(inmask)
            Nmeasure2   = Nmeasure[index_in]
            if Nmeasure2.size==0:
                print '--- T = '+str(per)+' sec ---'
                print 'No uncertainty, step 1'
                print '----------------------------'
                continue
            NMmax       = Nmeasure2.max()
            if percentage is not None and num_thresh is None:
                NMthresh    = NMmax*percentage
            elif percentage is None and num_thresh is not None:
                NMthresh    = num_thresh
            elif percentage is not None and num_thresh is not None:
                NMthresh    = min(NMmax*percentage, num_thresh)
            else:
                raise ValueError('at least one of percentage/num_thresh should be specified')
            indstd      = (Nmeasure>=NMthresh)*index_in
            #----------------------
            #estimate uncertainties
            #----------------------
            index_all   = ind_gstdmin*indstd
            temp_sem    = invel_sem[index_all]
            if temp_sem.size == 0:
                print '--- T = '+str(per)+' sec ---'
                print 'No uncertainty, step 2'
                print '----------------------------'
                continue
            sem_min     = temp_sem.mean()
            print '--- T = '+str(per)+' sec ---'
            print 'min uncertainty: '+str(sem_min*1000.)+' m/s, number of grids: '+str(temp_sem.size)
            print '----------------------------'
            est_sem     = (mgauss/gstdmin)*sem_min
            undset      = pergrp.create_dataset(name='vel_sem', data=est_sem)
            # print mgauss.shape, invel_sem.shape, inmask.shape
            # 
            # index   = np.logical_not(mask)
            # mgauss2 = mgauss[index]
            # gstdmin = mgauss2.min()
            # gstdmax = mgauss2.max()
            # if gaussstd is None:
            #     Nmin    = mgauss2[mgauss2==gstdmin].size
            #     print 'T = '+str(per)+' sec; min gauss_std: '+str(gstdmin)+' km, number of mins: '+str(Nmin)+'; max gauss_std: '+str(gstdmax)+' km'
            # else:
            #     Nmin    = mgauss2[mgauss2<=gaussstd].size    
            #     print 'T = '+str(per)+' sec; min gauss_std: '+str(gstdmin)+' km, number of grids less than threhhold: '+str(Nmin)+'; max gauss_std: '+str(gstdmax)+' km'
        return

    
    def _get_basemap(self, projection='lambert', geopolygons=None, resolution='i'):
        """Get basemap for plotting results
        """
        # fig=plt.figure(num=None, figsize=(12, 12), dpi=80, facecolor='w', edgecolor='k')
        plt.figure()
        minlon      = self.attrs['minlon']
        maxlon      = self.attrs['maxlon']
        minlat      = self.attrs['minlat']
        maxlat      = self.attrs['maxlat']
        lat_centre  = (maxlat+minlat)/2.0
        lon_centre  = (maxlon+minlon)/2.0
        if projection=='merc':
            m       = Basemap(projection='merc', llcrnrlat=minlat-5., urcrnrlat=maxlat+5., llcrnrlon=minlon-5.,
                      urcrnrlon=maxlon+5., lat_ts=20, resolution=resolution, epsg = 4269)
            # m.drawparallels(np.arange(minlat,maxlat,dlat), labels=[1,0,0,1])
            # m.drawmeridians(np.arange(minlon,maxlon,dlon), labels=[1,0,0,1])
            m.drawparallels(np.arange(-80.0,80.0,5.0), labels=[1,0,0,1])
            m.drawmeridians(np.arange(-170.0,170.0,5.0), labels=[1,0,0,1])
            m.drawstates(color='g', linewidth=2.)
        elif projection=='global':
            m       = Basemap(projection='ortho',lon_0=lon_centre, lat_0=lat_centre, resolution=resolution)
            # m.drawparallels(np.arange(-80.0,80.0,10.0), labels=[1,0,0,1])
            # m.drawmeridians(np.arange(-170.0,170.0,10.0), labels=[1,0,0,1])
        elif projection=='regional_ortho':
            m1      = Basemap(projection='ortho', lon_0=minlon, lat_0=minlat, resolution='l')
            m       = Basemap(projection='ortho', lon_0=minlon, lat_0=minlat, resolution=resolution,\
                        llcrnrx=0., llcrnry=0., urcrnrx=m1.urcrnrx/mapfactor, urcrnry=m1.urcrnry/3.5)
            m.drawparallels(np.arange(-80.0,80.0,10.0), labels=[1,0,0,0],  linewidth=2,  fontsize=20)
            # m.drawparallels(np.arange(-90.0,90.0,30.0),labels=[1,0,0,0], dashes=[10, 5], linewidth=2,  fontsize=20)
            # m.drawmeridians(np.arange(10,180.0,30.0), dashes=[10, 5], linewidth=2)
            m.drawmeridians(np.arange(-170.0,170.0,10.0),  linewidth=2)
        elif projection=='lambert':
            distEW, az, baz = obspy.geodetics.gps2dist_azimuth(minlat, minlon, minlat, maxlon) # distance is in m
            distNS, az, baz = obspy.geodetics.gps2dist_azimuth(minlat, minlon, maxlat+2., minlon) # distance is in m
            m       = Basemap(width=distEW, height=distNS, rsphere=(6378137.00,6356752.3142), resolution='h', projection='lcc',\
                        lat_1=minlat, lat_2=maxlat, lon_0=lon_centre, lat_0=lat_centre+1)
            m.drawparallels(np.arange(-80.0,80.0,10.0), linewidth=1, dashes=[2,2], labels=[1,1,0,0], fontsize=20)
            m.drawmeridians(np.arange(-170.0,170.0,10.0), linewidth=1, dashes=[2,2], labels=[0,0,1,0], fontsize=20)
            # m.drawparallels(np.arange(-80.0,80.0,10.0), linewidth=0.5, dashes=[2,2], labels=[1,0,0,0], fontsize=5)
            # m.drawmeridians(np.arange(-170.0,170.0,10.0), linewidth=0.5, dashes=[2,2], labels=[0,0,0,1], fontsize=5)
        m.drawcoastlines(linewidth=1.0)
        m.drawcountries(linewidth=1.)
        # # m.drawmapboundary(fill_color=[1.0,1.0,1.0])
        # m.fillcontinents(lake_color='#99ffff',zorder=0.2)
        # # m.drawlsmask(land_color='0.8', ocean_color='#99ffff')
        # m.drawmapboundary(fill_color="white")
        # m.shadedrelief(scale=1., origin='lower')
        try:
            geopolygons.PlotPolygon(inbasemap=m)
        except:
            pass
        return m
    
    def _get_lon_lat_arr(self, dataid, sfx=''):
        """Get longitude/latitude array
        """
        minlon                  = self.attrs['minlon']
        maxlon                  = self.attrs['maxlon']
        minlat                  = self.attrs['minlat']
        maxlat                  = self.attrs['maxlat']
        if sfx == '':
            dlon                = self[dataid].attrs['dlon']
            dlat                = self[dataid].attrs['dlat']
        else:
            dlon                = self[dataid].attrs['dlon_'+sfx]
            dlat                = self[dataid].attrs['dlat_'+sfx]
        self.lons               = np.arange(int((maxlon-minlon)/dlon)+1)*dlon+minlon
        self.lats               = np.arange(int((maxlat-minlat)/dlat)+1)*dlat+minlat
        self.Nlon               = self.lons.size
        self.Nlat               = self.lats.size
        self.lonArr, self.latArr= np.meshgrid(self.lons, self.lats)
        return
    
    def plot(self, runtype, runid, datatype, period, shpfx=None, clabel='', cmap='cv', projection='lambert', hillshade=False,\
             geopolygons=None, vmin=None, vmax=None, showfig=True):
        """plot maps from the tomographic inversion
        =================================================================================================================
        ::: input parameters :::
        runtype         - type of run (0 - smooth run, 1 - quality controlled run)
        runid           - id of run
        datatype        - datatype for plotting
        period          - period of data
        clabel          - label of colorbar
        cmap            - colormap
        projection      - projection type
        geopolygons     - geological polygons for plotting
        vmin, vmax      - min/max value of plotting
        showfig         - show figure or not
        =================================================================================================================
        """
        # vdict       = {'ph': 'C', 'gr': 'U'}
        # datatype    = datatype.lower()
        rundict     = {0: 'smooth_run', 1: 'qc_run'}
        dataid      = rundict[runtype]+'_'+str(runid)
        self._get_lon_lat_arr(dataid)
        try:
            ingroup     = self['reshaped_'+dataid]
        except KeyError:
            try:
                self.creat_reshape_data(runtype=runtype, runid=runid)
                ingroup = self['reshaped_'+dataid]
            except KeyError:
                raise KeyError(dataid+ ' not exists!')
        pers        = self.attrs['period_array']
        if not period in pers:
            raise KeyError('period = '+str(period)+' not included in the database')
        pergrp  = ingroup['%g_sec'%( period )]
        if runtype == 1:
            isotropic   = ingroup.attrs['isotropic']
        else:
            isotropic   = True
        if datatype == 'vel' or datatype=='velocity' or datatype == 'v':
            if isotropic:
                datatype    = 'velocity'
            else:
                datatype    = 'vel_iso'
        if datatype == 'un' or datatype=='sem' or datatype == 'vel_sem':
            datatype        = 'vel_sem'
        try:
            data    = pergrp[datatype].value
        except:
            outstr      = ''
            for key in pergrp.keys():
                outstr  +=key
                outstr  +=', '
            outstr      = outstr[:-1]
            raise KeyError('Unexpected datatype: '+datatype+\
                           ', available datatypes are: '+outstr)
        if datatype == 'amp2':
            data    = data*100.
        if datatype == 'vel_sem':
            data    = data*1000.
        if not isotropic:
            if datatype == 'cone_radius' or datatype == 'gauss_std' or datatype == 'max_resp' or datatype == 'ncone' or \
                         datatype == 'ngauss' or datatype == 'vel_sem':
                mask    = ingroup['mask2']
            else:
                mask    = ingroup['mask1']
            mdata       = ma.masked_array(data, mask=mask )
        else:
            mdata       = data.copy()
        #-----------
        # plot data
        #-----------
        m           = self._get_basemap(projection=projection, geopolygons=geopolygons)
        x, y        = m(self.lonArr, self.latArr)
        # shapefname  = '/projects/life9360/geological_maps/qfaults'
        # m.readshapefile(shapefname, 'faultline', linewidth=2, color='blue')
        # shapefname  = '/projects/life9360/AKgeol_web_shp/AKStategeolarc_generalized_WGS84'
        # m.readshapefile(shapefname, 'geolarc', linewidth=1, color='blue')
        shapefname  = '../AKfaults/qfaults'
        m.readshapefile(shapefname, 'faultline', linewidth=2, color='grey')
        shapefname  = '../AKgeol_web_shp/AKStategeolarc_generalized_WGS84'
        m.readshapefile(shapefname, 'geolarc', linewidth=1, color='grey')
        # shapefname  = '/projects/life9360/AK_sediments/Cook_Inlet_sediments_WGS84'
        # m.readshapefile(shapefname, 'faultline', linewidth=1, color='blue')
        
        if cmap == 'ses3d':
            cmap        = colormaps.make_colormap({0.0:[0.1,0.0,0.0], 0.2:[0.8,0.0,0.0], 0.3:[1.0,0.7,0.0],0.48:[0.92,0.92,0.92],
                            0.5:[0.92,0.92,0.92], 0.52:[0.92,0.92,0.92], 0.7:[0.0,0.6,0.7], 0.8:[0.0,0.0,0.8], 1.0:[0.0,0.0,0.1]})
        elif cmap == 'cv':
            import pycpt
            cmap    = pycpt.load.gmtColormap('./cv.cpt')
        else:
            try:
                if os.path.isfile(cmap):
                    import pycpt
                    cmap    = pycpt.load.gmtColormap(cmap)
            except:
                pass
        ################################3
        if hillshade:
            from netCDF4 import Dataset
            from matplotlib.colors import LightSource
        
            etopodata   = Dataset('/projects/life9360/station_map/grd_dir/ETOPO2v2g_f4.nc')
            etopo       = etopodata.variables['z'][:]
            lons        = etopodata.variables['x'][:]
            lats        = etopodata.variables['y'][:]
            ls          = LightSource(azdeg=315, altdeg=45)
            # nx          = int((m.xmax-m.xmin)/40000.)+1; ny = int((m.ymax-m.ymin)/40000.)+1
            etopo,lons  = shiftgrid(180.,etopo,lons,start=False)
            # topodat,x,y = m.transform_scalar(etopo,lons,lats,nx,ny,returnxy=True)
            ny, nx      = etopo.shape
            topodat,xtopo,ytopo = m.transform_scalar(etopo,lons,lats,nx, ny, returnxy=True)
            m.imshow(ls.hillshade(topodat, vert_exag=1., dx=1., dy=1.), cmap='gray')
            mycm1=pycpt.load.gmtColormap('/projects/life9360/station_map/etopo1.cpt')
            mycm2=pycpt.load.gmtColormap('/projects/life9360/station_map/bathy1.cpt')
            mycm2.set_over('w',0)
            m.imshow(ls.shade(topodat, cmap=mycm1, vert_exag=1., dx=1., dy=1., vmin=0, vmax=8000))
            m.imshow(ls.shade(topodat, cmap=mycm2, vert_exag=1., dx=1., dy=1., vmin=-11000, vmax=-0.5))
        ###################################################################
        if hillshade:
            m.fillcontinents(lake_color='#99ffff',zorder=0.2, alpha=0.2)
        else:
            m.fillcontinents(lake_color='#99ffff',zorder=0.2)
        if hillshade:
            im          = m.pcolormesh(x, y, mdata, cmap=cmap, shading='gouraud', vmin=vmin, vmax=vmax, alpha=.5)
        else:
            im          = m.pcolormesh(x, y, mdata, cmap=cmap, shading='gouraud', vmin=vmin, vmax=vmax)
        cb          = m.colorbar(im, "bottom", size="3%", pad='2%')
        cb.set_label(clabel, fontsize=12, rotation=0)
        plt.suptitle(str(period)+' sec', fontsize=20)
        cb.ax.tick_params(labelsize=15)
        cb.set_alpha(1)
        cb.draw_all()
        print 'plotting data from '+dataid
        # # cb.solids.set_rasterized(True)
        cb.solids.set_edgecolor("face")
        m.shadedrelief(scale=1., origin='lower')
        if showfig:
            plt.show()
        return
    
    def generate_corrected_map(self, runid, glbdir, outdir, runtype=1, pers=np.array([]), glbpfx='smpkolya_phv_R_', outpfx='smpkolya_phv_R_'):
        """
        Generate corrected global phave velocity map using a regional phase velocity map.
        =================================================================================================================
        ::: input parameters :::
        dataid              - dataid for regional phase velocity map
        glbdir              - location of global reference phase velocity map files
        outdir              - output directory
        pers                - period array for correction (default is 4)
        glbpfx              - prefix for global reference phase velocity map files
        outpfx              - prefix for output reference phase velocity map files
        -----------------------------------------------------------------------------------------------------------------
        ::: output format ::::
        outdir/outpfx+str(int(per))
        =================================================================================================================
        """
        if not os.path.isdir(outdir):
            os.makedirs(outdir)
        if pers.size == 0:
            pers            = np.append( np.arange(7.)*10.+40., np.arange(2.)*25.+125.)
        rundict     = {0: 'smooth_run', 1: 'qc_run'}
        dataid      = rundict[runtype]+'_'+str(runid)
        ingrp       = self[dataid]
        per_arr     = self.attrs['period_array']
        tempgrp     = ingrp['%g_sec'%( per_arr[0] )]
        lonlat_arr  = tempgrp['lons_lats'].value
        for per in pers:
            inglbfname      = glbdir+'/'+glbpfx+str(int(per))
            try:
                pergrp      = ingrp['%g_sec'%( per )]
            except KeyError:
                print 'No regional data for period = '+str(per)+' sec'
                continue
            if not os.path.isfile(inglbfname):
                print 'No global data for period = '+str(per)+' sec'
                continue
            outfname        = outdir+'/'+outpfx+'%g' %(per)
            inglbarr        = np.loadtxt(inglbfname)
            outArr          = inglbarr.copy()
            velocity        = pergrp['velocity'].value
            for ig in range(inglbarr[:,0].size):
                glb_lon     = inglbarr[ig,0]
                glb_lat     = inglbarr[ig,1]
                glb_C       = inglbarr[ig,2]
                for ir in range(lonlat_arr[:, 0].size):
                    reg_lon = lonlat_arr[ir, 0]
                    reg_lat = lonlat_arr[ir, 1]
                    reg_C   = velocity[ir, 0]
                if abs(reg_lon-glb_lon)<0.05 and abs(reg_lat-glb_lat)<0.05 and reg_C != 0 :
                    if glb_C - reg_C < 0.5 and glb_C - reg_C > -0.5:
                        outArr[ig, 2]     = reg_C
                    else:
                        print 'Large changes in regional map: \
                                vel_glb = '+str(glb_C)+' km/s'+' vel_reg = '+str(reg_C)+' km/sec, '+str(reg_lon)+' '+str(reg_lat)
            np.savetxt(outfname, outArr, fmt='%g %g %.4f')
        return
    
    def print_gauss_info(self, runid=0, gaussstd=None):
        """
        print the gauss standard deviation information
        """
        dataid      = 'reshaped_qc_run_'+str(runid)
        pers        = self.attrs['period_array']
        ingrp       = self[dataid]
        isotropic   = ingrp.attrs['isotropic']
        if isotropic:
            print 'isotropic inversion results do not output gaussian std!'
            return
        mask        = ingrp['mask2']
        for per in pers:
            # get data
            pergrp  = ingrp['%g_sec'%( per )]
            mgauss  = pergrp['gauss_std'].value
            index   = np.logical_not(mask)
            mgauss2 = mgauss[index]
            gstdmin = mgauss2.min()
            gstdmax = mgauss2.max()
            if gaussstd is None:
                Nmin    = mgauss2[mgauss2==gstdmin].size
                print 'T = '+str(per)+' sec; min gauss_std: '+str(gstdmin)+' km, number of mins: '+str(Nmin)+'; max gauss_std: '+str(gstdmax)+' km'
            else:
                Nmin    = mgauss2[mgauss2<=gaussstd].size    
                print 'T = '+str(per)+' sec; min gauss_std: '+str(gstdmin)+' km, number of grids less than threhhold: '+str(Nmin)+'; max gauss_std: '+str(gstdmax)+' km'
        return
    
    def interp_surface(self, workingdir='./raytomo_interp_surface', dlon=0.05, dlat=0.05, runid=0, deletetxt=True):
        """interpolate inverted velocity maps and uncertainties to a finer grid for joint inversion
        =================================================================================================================
        ::: input parameters :::
        workingdir  - working directory
        dlon/dlat   - grid interval for interpolation
        runid       - id of run
        =================================================================================================================
        """
        self._get_lon_lat_arr('qc_run_'+str(runid))
        dataid          = 'reshaped_qc_run_'+str(runid)
        pers            = self.attrs['period_array']
        grp             = self[dataid]
        isotropic       = grp.attrs['isotropic']
        org_grp         = self['qc_run_'+str(runid)]
        minlon          = self.attrs['minlon']
        maxlon          = self.attrs['maxlon']
        minlat          = self.attrs['minlat']
        maxlat          = self.attrs['maxlat']
        if isotropic:
            print 'isotropic inversion results do not output gaussian std!'
            return
        if org_grp.attrs['dlon'] == dlon and org_grp.attrs['dlat'] == dlat:
            print 'No need for interpolation!'
            return
        if org_grp.attrs['dlon'] > dlon and org_grp.attrs['dlat'] > dlat:
            sfx         = 'HD'
        elif org_grp.attrs['dlon'] < dlon and org_grp.attrs['dlat'] < dlat:
            sfx         = 'LD'
        else:
            sfx         = 'interp'
        org_grp.attrs.create(name = 'dlon_'+sfx, data=dlon)
        org_grp.attrs.create(name = 'dlat_'+sfx, data=dlat)
        mask1           = grp['mask1']
        mask2           = grp['mask2']
        index1          = np.logical_not(mask1)
        index2          = np.logical_not(mask2)
        for per in pers:
            working_per = workingdir+'/'+str(per)+'sec'
            if not os.path.isdir(working_per):
                os.makedirs(working_per)
            #-------------------------------
            # get data
            #-------------------------------
            try:
                pergrp      = grp['%g_sec'%( per )]
                vel         = pergrp['vel_iso'].value
                vel_sem     = pergrp['vel_sem'].value
            except KeyError:
                print 'No data for T = '+str(per)+' sec'
                continue
            #-------------------------------
            # interpolation for velocity
            #-------------------------------
            field2d_v   = field2d_earth.Field2d(minlon=minlon, maxlon=maxlon, dlon=dlon,
                            minlat=minlat, maxlat=maxlat, dlat=dlat, period=per, evlo=(minlon+maxlon)/2., evla=(minlat+maxlat)/2.)
            field2d_v.read_array(lonArr = self.lonArr[index1], latArr = self.latArr[index1], ZarrIn = vel[index1])
            outfname    = 'interp_vel.lst'
            field2d_v.interp_surface(workingdir=working_per, outfname=outfname)
            vHD_dset    = pergrp.create_dataset(name='vel_iso_'+sfx, data=field2d_v.Zarr)
            #-------------------------------
            # interpolation for uncertainties
            #-------------------------------
            field2d_un  = field2d_earth.Field2d(minlon=minlon, maxlon=maxlon, dlon=dlon,
                            minlat=minlat, maxlat=maxlat, dlat=dlat, period=per, evlo=(minlon+maxlon)/2., evla=(minlat+maxlat)/2.)
            field2d_un.read_array(lonArr = self.lonArr[index2], latArr = self.latArr[index2], ZarrIn = vel_sem[index2])
            outfname    = 'interp_un.lst'
            field2d_un.interp_surface(workingdir=working_per, outfname=outfname)
            unHD_dset   = pergrp.create_dataset(name='vel_sem_'+sfx, data=field2d_un.Zarr)
        if deletetxt:
            shutil.rmtree(workingdir)
        return
    
    def plot_interp(self, runid, datatype, period, shpfx=None, clabel='', cmap='cv', projection='lambert', hillshade=False,\
             geopolygons=None, vmin=None, vmax=None, showfig=True, sfx='HD'):
        """plot HD maps from the tomographic inversion
        =================================================================================================================
        ::: input parameters :::
        runid           - id of run
        datatype        - datatype for plotting
        period          - period of data
        clabel          - label of colorbar
        cmap            - colormap
        projection      - projection type
        geopolygons     - geological polygons for plotting
        vmin, vmax      - min/max value of plotting
        showfig         - show figure or not
        =================================================================================================================
        """
        dataid          = 'qc_run_'+str(runid)
        self._get_lon_lat_arr(dataid, sfx=sfx)
        try:
            ingroup     = self['reshaped_'+dataid]
        except KeyError:
            try:
                self.creat_reshape_data(runtype=runtype, runid=runid)
                ingroup = self['reshaped_'+dataid]
            except KeyError:
                raise KeyError(dataid+ ' not exists!')
        pers            = self.attrs['period_array']
        if not period in pers:
            raise KeyError('period = '+str(period)+' not included in the database')
        pergrp          = ingroup['%g_sec'%( period )]
        if datatype == 'vel' or datatype=='velocity' or datatype == 'v':
            datatype    = 'vel_iso_'+sfx
        if datatype == 'un' or datatype=='sem' or datatype == 'vel_sem':
            datatype    = 'vel_sem_'+sfx
        try:
            data    = pergrp[datatype].value
        except:
            outstr      = ''
            for key in pergrp.keys():
                outstr  +=key
                outstr  +=', '
            outstr      = outstr[:-1]
            raise KeyError('Unexpected datatype: '+datatype+\
                           ', available datatypes are: '+outstr)
        #-----------
        # plot data
        #-----------
        m           = self._get_basemap(projection=projection, geopolygons=geopolygons)
        x, y        = m(self.lonArr, self.latArr)
        shapefname  = '/projects/life9360/geological_maps/qfaults'
        m.readshapefile(shapefname, 'faultline', linewidth=2, color='grey')
        shapefname  = '/projects/life9360/AKgeol_web_shp/AKStategeolarc_generalized_WGS84'
        m.readshapefile(shapefname, 'faultline', linewidth=1, color='grey')
        
        if cmap == 'ses3d':
            cmap        = colormaps.make_colormap({0.0:[0.1,0.0,0.0], 0.2:[0.8,0.0,0.0], 0.3:[1.0,0.7,0.0],0.48:[0.92,0.92,0.92],
                            0.5:[0.92,0.92,0.92], 0.52:[0.92,0.92,0.92], 0.7:[0.0,0.6,0.7], 0.8:[0.0,0.0,0.8], 1.0:[0.0,0.0,0.1]})
        elif cmap == 'cv':
            import pycpt
            cmap    = pycpt.load.gmtColormap('./cv.cpt')
        else:
            try:
                if os.path.isfile(cmap):
                    import pycpt
                    cmap    = pycpt.load.gmtColormap(cmap)
            except:
                pass
        ################################3
        if hillshade:
            from netCDF4 import Dataset
            from matplotlib.colors import LightSource
        
            etopodata   = Dataset('/projects/life9360/station_map/grd_dir/ETOPO2v2g_f4.nc')
            etopo       = etopodata.variables['z'][:]
            lons        = etopodata.variables['x'][:]
            lats        = etopodata.variables['y'][:]
            ls          = LightSource(azdeg=315, altdeg=45)
            # nx          = int((m.xmax-m.xmin)/40000.)+1; ny = int((m.ymax-m.ymin)/40000.)+1
            etopo,lons  = shiftgrid(180.,etopo,lons,start=False)
            # topodat,x,y = m.transform_scalar(etopo,lons,lats,nx,ny,returnxy=True)
            ny, nx      = etopo.shape
            topodat,xtopo,ytopo = m.transform_scalar(etopo,lons,lats,nx, ny, returnxy=True)
            m.imshow(ls.hillshade(topodat, vert_exag=1., dx=1., dy=1.), cmap='gray')
            mycm1=pycpt.load.gmtColormap('/projects/life9360/station_map/etopo1.cpt')
            mycm2=pycpt.load.gmtColormap('/projects/life9360/station_map/bathy1.cpt')
            mycm2.set_over('w',0)
            # m.imshow(ls.shade(topodat, cmap=mycm1, vert_exag=1., dx=1., dy=1., vmin=0, vmax=8000))
            # m.imshow(ls.shade(topodat, cmap=mycm2, vert_exag=1., dx=1., dy=1., vmin=-11000, vmax=-0.5))
        ###################################################################
        if hillshade:
            m.fillcontinents(lake_color='#99ffff',zorder=0.2, alpha=0.2)
        else:
            m.fillcontinents(lake_color='#99ffff',zorder=0.2)
        if hillshade:
            im          = m.pcolormesh(x, y, data, cmap=cmap, shading='gouraud', vmin=vmin, vmax=vmax, alpha=.5)
        else:
            im          = m.pcolormesh(x, y, data, cmap=cmap, shading='gouraud', vmin=vmin, vmax=vmax)
        cb          = m.colorbar(im, "bottom", size="3%", pad='2%')
        cb.set_label(clabel, fontsize=12, rotation=0)
        plt.suptitle(str(period)+' sec', fontsize=20)
        cb.ax.tick_params(labelsize=15)
        cb.set_alpha(1)
        cb.draw_all()
        print 'plotting data from '+dataid
        # # cb.solids.set_rasterized(True)
        cb.solids.set_edgecolor("face")
        # m.shadedrelief(scale=1., origin='lower')
        if showfig:
            plt.show()
        return
    
    def plot_hist(self, runtype, runid, period, datatype='res', clabel='', showfig=True):
        datatype    = datatype.lower()
        rundict     = {0: 'smooth_run', 1: 'qc_run'}
        dataid      = rundict[runtype]+'_'+str(runid)
        self._get_lon_lat_arr(dataid)
        try:
            ingroup     = self[dataid]
        except KeyError:
            raise KeyError(dataid+ ' not exists!')
        pers        = self.attrs['period_array']
        if not period in pers:
            raise KeyError('period = '+str(period)+' not included in the database')
        pergrp  = ingroup['%g_sec'%( period )]
        if runtype == 1:
            isotropic   = ingroup.attrs['isotropic']
        else:
            isotropic   = True
        if datatype == 'res' or datatype=='residual':
            datatype    = 'residual'
            dataind     = 8
        data    = (pergrp[datatype].value)[:, dataind]
        ax      = plt.subplot()
        plt.hist(data, bins=200)
        outstd  = data.std()
        plt.xlim(-7, 7)
        plt.ylabel('Phase velocity measurements', fontsize=20)
        plt.xlabel('Misfit (sec)', fontsize=20)
        plt.title(str(period)+' sec, std = %g sec' %outstd, fontsize=30)
        ax.tick_params(axis='x', labelsize=20)
        ax.tick_params(axis='y', labelsize=20)
        if showfig:
            plt.show()
        return data
        
    
    
    def _numpy2ma(self, inarray, reason_n=None):
        """Convert input numpy array to masked array
        """
        if reason_n==None:
            outarray                        = ma.masked_array(inarray, mask=np.zeros(self.reason_n.shape) )
            outarray.mask[self.reason_n!=0] = 1
        else:
            outarray                        = ma.masked_array(inarray, mask=np.zeros(reason_n.shape) )
            outarray.mask[reason_n!=0]      = 1
        return outarray
    
    def np2ma(self):
        """Convert numpy data array to masked data array
        """
        try:
            reason_n    = self.reason_n
        except:
            raise AttrictError('No reason_n array!')
        self.vel_iso    = self._numpy2ma(self.vel_iso)
        self.dv         = self._numpy2ma(self.dv)
        self.pdens      = self._numpy2ma(self.pdens)
        self.pdens1     = self._numpy2ma(self.pdens1)
        self.pdens2     = self._numpy2ma(self.pdens2)
        self.azicov1    = self._numpy2ma(self.azicov1)
        self.azicov2    = self._numpy2ma(self.azicov2)
        try:
            self.amp2   = self._numpy2ma(self.amp2)
            self.psi2   = self._numpy2ma(self.psi2)
        except:
            pass
        try:
            self.amp4   = self._numpy2ma(self.amp4)
            self.psi4   = self._numpy2ma(self.psi4)
        except:
            pass
        return
    
    def get_data4plot(self, dataid, period):
        """
        Get data for plotting
        =======================================================================================
        ::: input parameters :::
        dataid              - dataid (e.g. smooth_run_0, qc_run_0 etc.)
        period              - period
        ---------------------------------------------------------------------------------------
        generated data arrays:
        ----------------------------------- isotropic version ---------------------------------
        self.vel_iso        - isotropic velocity
        self.dv             - velocity perturbation
        self.pdens          - path density (R1 and R2)
        self.pdens1         - path density (R1)
        self.pdens2         - path density (R2)
        self.azicov1        - azimuthal coverage, squared sum method(0-10)
        self.azicov2        - azimuthal coverage, maximum value method(0-180)
        ---------------------------------- anisotropic version --------------------------------
        include all the array above(but will be converted to masked array), and
        self.psi2/amp2      - fast axis/amplitude for psi2 anisotropy
        self.psi4/amp4      - fast axis/amplitude for psi4 anisotropy
        self.cradius        - cone radius (resolution)
        self.reason_n       - array to represent valid/invalid data points
        =======================================================================================
        """
        self._get_lon_lat_arr(dataid)
        subgroup            = self[dataid+'/%g_sec'%( period )]
        self.period         = period
        self.datatype       = self[dataid].attrs['datatype']
        try:
            self.isotropic  = self[dataid].attrs['isotropic']
        except:
            self.isotropic  = True
        if self.isotropic:
            self.vel_iso    = subgroup['velocity'].value
            self.vel_iso    = self.vel_iso.reshape(self.Nlat, self.Nlon)
            self.dv         = subgroup['Dvelocity'].value
            self.dv         = self.dv.reshape(self.Nlat, self.Nlon)
            self.pdens      = subgroup['path_density'].value
            self.pdens      = self.pdens.reshape(self.Nlat, self.Nlon)
            self.azicov1    = (subgroup['azi_coverage'].value)[:,0]
            self.azicov1    = self.azicov1.reshape(self.Nlat, self.Nlon)
            self.azicov2    = (subgroup['azi_coverage'].value)[:,1]
            self.azicov2    = self.azicov2.reshape(self.Nlat, self.Nlon)
        else:
            self.anipara    = self[dataid].attrs['anipara']
            # initialize dataset
            self.vel_iso    = np.zeros(self.lonArr.shape)
            if self.anipara!=0:
                self.amp2   = np.zeros(self.lonArr.shape)
                self.psi2   = np.zeros(self.lonArr.shape)
            if self.anipara==2:
                self.amp4   = np.zeros(self.lonArr.shape)
                self.psi4   = np.zeros(self.lonArr.shape)
            self.dv         = np.zeros(self.lonArr.shape)
            self.pdens      = np.zeros(self.lonArr.shape)
            self.pdens1     = np.zeros(self.lonArr.shape)
            self.pdens2     = np.zeros(self.lonArr.shape)
            self.azicov1    = np.zeros(self.lonArr.shape)
            self.azicov2    = np.zeros(self.lonArr.shape)
            self.cradius    = np.zeros(self.lonArr.shape)
            self.reason_n   = np.ones(self.lonArr.shape)
            # read data from hdf5 database
            lon_lat_array   = subgroup['lons_lats'].value
            vel_iso         = (subgroup['velocity'].value)[:,0]
            dv              = subgroup['Dvelocity'].value
            if self.anipara != 0:
                amp2        = (subgroup['velocity'].value)[:,3]
                psi2        = (subgroup['velocity'].value)[:,4]
            if self.anipara == 2:
                amp4        = (subgroup['velocity'].value)[:,7]
                psi4        = (subgroup['velocity'].value)[:,8]
            inlon           = lon_lat_array[:,0]
            inlat           = lon_lat_array[:,1]
            pdens           = (subgroup['path_density'].value)[:,0]
            pdens1          = (subgroup['path_density'].value)[:,1]
            pdens2          = (subgroup['path_density'].value)[:,2]
            azicov1         = (subgroup['azi_coverage'].value)[:,0]
            azicov2         = (subgroup['azi_coverage'].value)[:,1]
            # cradius=(subgroup['resolution'].value)[:,0]
            for i in range(inlon.size):
                lon         = inlon[i]
                lat         = inlat[i]
                index       = np.where((self.lonArr==lon)*(self.latArr==lat))
                # print index
                self.reason_n[index[0], index[1]]   = 0
                self.vel_iso[index[0], index[1]]    = vel_iso[i]
                if self.anipara!=0:
                    self.amp2[index[0], index[1]]   = amp2[i]
                    self.psi2[index[0], index[1]]   = psi2[i]
                if self.anipara==2:
                    self.amp4[index[0], index[1]]   = amp4[i]
                    self.psi4[index[0], index[1]]   = psi4[i]
                self.dv[index[0], index[1]]         = dv[i]
                self.pdens[index[0], index[1]]      = pdens[i]
                self.pdens1[index[0], index[1]]     = pdens1[i]
                self.pdens2[index[0], index[1]]     = pdens2[i]
                self.azicov1[index[0], index[1]]    = azicov1[i]
                self.azicov2[index[0], index[1]]    = azicov2[i]
                # self.cradius[index[0], index[1]]=cradius[i]
            self.np2ma()
        return
            
    
    def plot_vel_iso(self, dataid=None, period=None, projection='lambert', fastaxis=False, geopolygons=None, showfig=True, vmin=None, vmax=None):
        """Plot isotropic velocity
        """
        vdict       = {'ph': 'C', 'gr': 'U'}
        if dataid !=None and period !=None:
            self.get_data4plot(dataid=dataid, period=period)
        try:
            vel_iso = self.vel_iso
        except:
            print 'Specify dataid and period to get data for plotting!'
            return
        m           = self._get_basemap(projection=projection, geopolygons=geopolygons)
        x, y        = m(self.lonArr, self.latArr)
        cmap        = colormaps.make_colormap({0.0:[0.1,0.0,0.0], 0.2:[0.8,0.0,0.0], 0.3:[1.0,0.7,0.0],0.48:[0.92,0.92,0.92],
                        0.5:[0.92,0.92,0.92], 0.52:[0.92,0.92,0.92], 0.7:[0.0,0.6,0.7], 0.8:[0.0,0.0,0.8], 1.0:[0.0,0.0,0.1]})
        im          = m.pcolormesh(x, y, vel_iso, cmap=cmap, shading='gouraud', vmin=vmin, vmax=vmax)
        cb          = m.colorbar(im, "bottom", size="3%", pad='2%')
        cb.set_label(vdict[self.datatype]+' (km/s)', fontsize=12, rotation=0)
        plt.title(str(self.period)+' sec', fontsize=20)
        if fastaxis:
            try:
                self.plot_fast_axis(inbasemap=m)
            except:
                pass
        if showfig:
            plt.show()
        return
        
    def plot_fast_axis(self, projection='lambert', inbasemap=None, factor=1, showfig=False, psitype=2):
        """Plot fast axis(psi2 or psi4)
        """
        if inbasemap==None:
            m   = self._get_basemap(projection=projection)
        else:
            m   = inbasemap
        x, y    = m(self.lonArr, self.latArr)
        if psitype==2:
            psi = self.psi2
        elif psitype==4:
            psi = self.psi4
        U       = np.sin(psi)
        V       = np.cos(psi)
        if factor!=None:
            x   = x[0:self.Nlat:factor, 0:self.Nlon:factor]
            y   = y[0:self.Nlat:factor, 0:self.Nlon:factor]
            U   = U[0:self.Nlat:factor, 0:self.Nlon:factor]
            V   = V[0:self.Nlat:factor, 0:self.Nlon:factor]
        Q       = m.quiver(x, y, U, V, scale=50, width=0.001, headaxislength=0)
        if showfig:
            plt.show()
        return
    
    def plot_array(self, inarray, title='', label='', projection='lambert', fastaxis=False, geopolygons=None, showfig=True, vmin=None, vmax=None):
        """Plot input array
        """
        if inarray.shape!=self.lonArr.shape:
            raise ValueError('Shape of input array is not compatible with longitude/latitude array!')
        m=self._get_basemap(projection=projection, geopolygons=geopolygons)
        x, y=m(self.lonArr, self.latArr)
        cmap = colormaps.make_colormap({0.0:[0.1,0.0,0.0], 0.2:[0.8,0.0,0.0], 0.3:[1.0,0.7,0.0],0.48:[0.92,0.92,0.92],
            0.5:[0.92,0.92,0.92], 0.52:[0.92,0.92,0.92], 0.7:[0.0,0.6,0.7], 0.8:[0.0,0.0,0.8], 1.0:[0.0,0.0,0.1]})
        im=m.pcolormesh(x, y, inarray, cmap=cmap, shading='gouraud', vmin=vmin, vmax=vmax)
        cb = m.colorbar(im, "bottom", size="3%", pad='2%')
        cb.set_label(label, fontsize=12, rotation=0)
        plt.title(title+str(self.period)+' sec', fontsize=20)
        if fastaxis:
            try:
                self.plot_fast_axis(inbasemap=m)
            except:
                pass
        if showfig:
            plt.show()
        return
    
    
    
    def plot_global_map(self, period, resolution='i', inglbpfx='./MAPS/smpkolya_phv_R', geopolygons=None, showfig=True, vmin=None, vmax=None):
        """
        Plot global phave velocity map 
        =================================================================================================================
        ::: input parameters :::
        period              - input period
        resolution          - resolution in Basemap object
        inglbpfx            - prefix of input global velocity map files
        geopolygons         - geopolygons for plotting
        showfig             - show figure or not
        vmin/vmax           - minimum/maximum value for plotting
        =================================================================================================================
        """
        inglbfname          = inglbpfx+'_'+str(int(period))
        inArr               = np.loadtxt(inglbfname)
        lonArr              = inArr[:,0]
        lonArr[lonArr>180]  = lonArr[lonArr>180]-360
        lonArr              = lonArr.reshape(181, 360)
        latArr              = inArr[:,1]
        latArr              = latArr.reshape(181, 360)
        phvArr              = inArr[:,2]
        phvArr              = phvArr.reshape(181, 360)
        minlon              = self.attrs['minlon']
        maxlon              = self.attrs['maxlon']
        minlat              = self.attrs['minlat']
        maxlat              = self.attrs['maxlat']
        lat_centre          = (maxlat+minlat)/2.0
        lon_centre          = (maxlon+minlon)/2.0
        m                   = Basemap(projection='moll',lon_0=lon_centre, lat_0=lat_centre, resolution=resolution)
        x, y                = m(lonArr, latArr)
        cmap                = colormaps.make_colormap({0.0:[0.1,0.0,0.0], 0.2:[0.8,0.0,0.0], 0.3:[1.0,0.7,0.0],0.48:[0.92,0.92,0.92],
                                0.5:[0.92,0.92,0.92], 0.52:[0.92,0.92,0.92], 0.7:[0.0,0.6,0.7], 0.8:[0.0,0.0,0.8], 1.0:[0.0,0.0,0.1]})
        im                  = m.pcolormesh(x, y, phvArr, cmap=cmap, shading='gouraud', vmin=vmin, vmax=vmax)
        m.drawcoastlines(linewidth=1.0)
        cb                  = m.colorbar(im, "bottom", size="3%", pad='2%')
        cb.set_label('C (km/s)', fontsize=12, rotation=0)
        plt.title(str(period)+' sec', fontsize=20)
        # m.readshapefile('./tectonicplates/PB2002_plates', 
        #         name='tectonic_plates', 
        #         drawbounds=True, 
        #         color='red')
        if showfig: plt.show()
        return
        
        
