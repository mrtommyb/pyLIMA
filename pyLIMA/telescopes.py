# -*- coding: utf-8 -*-
"""
Created on Thu Aug 27 16:39:32 2015

@author: ebachelet
"""
from __future__ import division

import numpy as np
import astropy.io.fits as fits

import microltoolbox
import microlparallax

# Conventions for magnitude and flux lightcurves for all pyLIMA. If the injected lightcurve format differs, please
# indicate this in the correponding lightcurve_magnitude_dictionnary or lightcurve_flux_dictionnary, see below.
PYLIMA_LIGHTCURVE_MAGNITUDE_CONVENTION = ['time', 'mag', 'err_mag']
PYLIMA_LIGHTCURVE_FLUX_CONVENTION = ['time', 'flux', 'err_flux']


class Telescope(object):
    """
    ######## Telescope module ########

    This module create a telescope object with the informations (attributes) needed for the fits.

    Attributes :

        location : The location of your observatory. Should be "Earth" (default) or "Space".

        altitude : Altitude in meter of the telescope. Default is 0.0 (sea level).

        longitude : Longitude of the telescope in degrees. Default is 0.57.

        latitude : Latitude in degrees. Default is 49.49 .

        gamma : (Microlensing covention) Limb darkening coefficient :math:`\\Gamma` associated to the filter.
                 The classical (Milne definition) linear limb darkening coefficient can be found using:
                 u=(3*gamma)/(2+gamma).
                 Default is 0.0 (i.e uniform source brightness)

        lightcurve_magnitude : a numpy array describing your data in magnitude.

        lightcurve_magnitude_dictionnary : a python dictionnary to transform the lightcurve_magnitude
                                          input to pyLIMA convention.

        lightcurve_flux : a numpy array describing your data in flux.

        lightcurve_flux_dictionnary : a python dictionnary to transform the lightcurve_flux input to pyLIMA convention.

        reference_flux : a float used for the transformation of difference fluxes to real fluxes. Default is 10000.0 .

        deltas-positions : a list containing the position shift of this observatory due to parallax.
                           Default is an empty list. More details in microlparallax.

    :param string name: name of the telescope. Default is 'NDG'

    :param string camera_filter: telescope filter used. Should be a string which follows the convention of :
               " Gravity and limb-darkening coefficients for the Kepler, CoRoT, Spitzer, uvby,
               UBVRIJHK,
               and Sloan photometric systems"
               Claret, A. and Bloemen, S. 2011A&A...529A..75C. For example, 'I' (default) is
               Johnson_Cousins I filter
               and 'i'' is the SDSS-i' Sloan filter.


    :param array_like light_curve_magnitude:  a numpy array with time, magnitude and error in magnitude.
                                              Default is an None.

    :param dict light_curve_magnitude_dictionnary: a python dictionnary that informs your columns convention. Used to
                                                   translate to pyLIMA convention [time,mag,err_mag].
                                                   Default is {'time': 0, 'mag' : 1, 'err_mag' : 2 }


    :param array-like light_curve_flux:  a numpy array with time, flux and error in flux. Default is an None.

    :param dict light_curve_flux_dictionnary: a python dictionnary that informs your columns convention. Used to
                                              translate to pyLIMA convention [time,flux,err_flux].
                                              Default is {'time': 0, 'flux' : 1, 'err_flux' : 2 }

    :param float reference_flux: a float used for the transformation of difference fluxes to real fluxes.
                                 Default is 0.0 .

    :param str clean_the_lightcurve : a string indicated if you want pyLIMA to clean your lightcurves. Highly recommanded!
    """

    def __init__(self, name='NDG', camera_filter='I', light_curve_magnitude=None,
                 light_curve_magnitude_dictionnary=None,
                 light_curve_flux=None, light_curve_flux_dictionnary=None,
                 reference_flux=0.0, clean_the_lightcurve='Yes'):
        """Initialization of the attributes described above."""

        self.name = name
        self.filter = camera_filter  # Claret2011 convention

        if light_curve_magnitude_dictionnary is None:
            light_curve_magnitude_dictionnary = {'time': 0, 'mag': 1, 'err_mag': 2}

        if light_curve_flux_dictionnary is None:
            light_curve_flux_dictionnary = {'time': 0, 'flux': 1, 'err_flux': 2}

        self.lightcurve_magnitude_dictionnary = light_curve_magnitude_dictionnary
        self.lightcurve_flux_dictionnary = light_curve_flux_dictionnary
        self.reference_flux = reference_flux

        self.lightcurve_magnitude = []
        self.lightcurve_flux = []

        if light_curve_magnitude is None:

            pass

        else:

            self.lightcurve_magnitude = light_curve_magnitude
            self.lightcurve_magnitude = self.arrange_the_lightcurve_columns('magnitude')

            if clean_the_lightcurve == 'Yes':
                self.lightcurve_magnitude = self.clean_data_magnitude()

            self.lightcurve_flux = self.lightcurve_in_flux()

            if clean_the_lightcurve == 'Yes':
                 self.lightcurve_flux = self.clean_data_flux()

        if light_curve_flux is None:

            pass

        else:

            self.lightcurve_flux = light_curve_flux
            self.lightcurve_flux = self.arrange_the_lightcurve_columns('flux')

            if clean_the_lightcurve == 'Yes':
                self.lightcurve_flux = self.clean_data_flux()


            self.lightcurve_magnitude = self.lightcurve_in_magnitude()




        self.location = 'Earth'
        self.altitude = 0.0  # meters
        self.longitude = 0.57  # degrees
        self.latitude = 49.49  # degrees
        self.gamma = 0.0  # This mean you will fit uniform source brightness
        self.deltas_positions = []

    def arrange_the_lightcurve_columns(self, choice):
        """Rearange the lightcurve to the pyLIMA convention.

            :param string choice: 'magnitude' or 'flux'. A string which indicated on which lightcurves apply
                                   the sorting.

            :return: the lightcurve sorted in pyLIMA convention
            :rtype: array_like
        """

        if choice == 'magnitude':

            lightcurve = []
            for good_column in PYLIMA_LIGHTCURVE_MAGNITUDE_CONVENTION:
                lightcurve.append(self.lightcurve_magnitude[:, self.lightcurve_magnitude_dictionnary[good_column]])

            lightcurve = np.array(lightcurve).T
            return lightcurve

        if choice == 'flux':

            lightcurve = []
            for good_column in PYLIMA_LIGHTCURVE_FLUX_CONVENTION:
                lightcurve.append(self.lightcurve_flux[:, self.lightcurve_flux_dictionnary[good_column]])

            lightcurve = np.array(lightcurve).T
            lightcurve[:, 1] = lightcurve[:, 1] + self.reference_flux
            return lightcurve

    def n_data(self, choice='magnitude'):
        """ Return the number of data points in the lightcurve.

        :param string choice: 'magnitude' (default) or 'flux' The unit you want to check data for.

        :return: the size of the corresponding lightcurve
        :rtype: int
        """

        if choice == 'flux':
            return len(self.lightcurve_flux[:, 0])

        if choice == 'magnitude':
            return len(self.lightcurve_magnitude[:, 0])

    def find_gamma(self, Teff, log_g, claret_path='./data/'):
        """
        Set the associated :math:`\\Gamma` linear limb-darkening coefficient associated to the filter,
        the given effective
        temperature and the given surface gravity in log10 cgs.

        WARNING. Two strong assomption are made :
                  - the microturbulent velocity turbulent_velocity is fixed to 2 km/s

                  - the metallicity is fixed equal to the Sun : metallicity=0.0
        :param float Teff: The effective temperature of the source in Kelvin.
        :param float log_g: The log10 surface gravity in cgs.
        :param string claret_path: path to the Claret table.
        """
        # assumption   Microturbulent velocity =2km/s, metallicity= 0.0 (Sun value) Claret2011
        # convention
        turbulent_velocity = 2.0
        metallicity = 0.0

        # TODO: Use read claret generator

        claret_table = fits.open(claret_path + 'Claret2011.fits')
        claret_table = np.array([claret_table[1].data['log g'], claret_table[1].data['Teff (K)'],
                                 claret_table[1].data['Z (Sun)'], claret_table[1].data['Xi (km/s)'],
                                 claret_table[1].data['u'], claret_table[1].data['filter']]).T

        # Find the raw corresponding to the requested filter.

        indexes_filter = np.where(claret_table[:, 5] == self.filter)[0]
        claret_table_reduce = claret_table[indexes_filter, :-1].astype(float)

        # Find the raw by computing distance of all raw and coefficient

        limb_darkening_coefficient_raw_index = np.sqrt((claret_table_reduce[:, 0] - log_g) ** 2 +
                                                       (claret_table_reduce[:, 1] - Teff) ** 2 +
                                                       (claret_table_reduce[:, 2] - metallicity) ** 2 +
                                                       (claret_table_reduce[:, 3] - turbulent_velocity) ** 2).argmin()

        linear_limb_darkening_coefficient = claret_table_reduce[limb_darkening_coefficient_raw_index, -1]

        self.gamma = 2 * linear_limb_darkening_coefficient / (3 - linear_limb_darkening_coefficient)

    def compute_parallax(self, event, parallax):
        """ Compute and set the deltas_positions attribute due to the parallax.

        :param object event: a event object. More details in the event module.
        :param list parallax: a list containing the parallax model and to_par. More details in microlparallax module.
        """
        para = microlparallax.MLParallaxes(event, parallax)
        para.parallax_combination(self)
        print 'Parallax(' + parallax[0] + ') estimated for the telescope ' + self.name + ': SUCCESS'

    def clean_data_magnitude(self):
        """
        Clean outliers of the telescope for the fits. Points are considered as outliers if they
        are 10 mag brighter
        or fainter than the lightcurve median or if nan appears in any columns or errobar higher
        than a 1 mag.

        :return: the cleaned magnitude lightcurve
        :rtype: array_like
        """

        maximum_accepted_precision = 1.0

        index = np.where((~np.isnan(self.lightcurve_magnitude).any(axis=1)) &
                         (np.abs(self.lightcurve_magnitude[:, 2]) <= maximum_accepted_precision))[0]

        lightcurve = self.lightcurve_magnitude[index]

        index = np.where((np.isnan(self.lightcurve_magnitude).any(axis=1)) &
                         (np.abs(self.lightcurve_magnitude[:, 2]) > maximum_accepted_precision))[0]
        if len(index) != 0:
            self.bad_points_magnitude = index
            print 'pyLIMA found some bad points in the telescope ' + self.name + ', you can found these in the ' \
                   'bad_points_magnitude attribute.'

        return lightcurve

    def clean_data_flux(self):
        """
        Clean outliers of the telescope for the fits. Points are considered as outliers if they
        are 10 mag brighter
        or fainter than the lightcurve median or if nan appears in any columns or errobar higher
        than a 1 mag.

        :return: the cleaned magnitude lightcurve
        :rtype: array_like
        """

        maximum_accepted_precision = 1.0
        flux = self.lightcurve_flux[:, 1]
        error_flux = self.lightcurve_flux[:, 2]
        index = np.where(
            (~np.isnan(self.lightcurve_flux).any(axis=1)) & (np.abs(error_flux / flux) <= maximum_accepted_precision))[0]


        lightcurve = self.lightcurve_flux[index]

        index = np.where(
            (np.isnan(self.lightcurve_flux).any(axis=1)) & (np.abs(error_flux / flux) > maximum_accepted_precision))[0]
        if len(index) != 0:


            self.bad_points_flux = index
            print 'pyLIMA found some bad points in the telescope ' + self.name + ', you can found these in the ' \
                                                                             'bad_points_flux attribute.'
        return lightcurve

    def lightcurve_in_flux(self):
        """
        Transform magnitude to flux using m=27.4-2.5*log10(flux) convention. Transform error bar
        accordingly. More details in microltoolbox module.

        :param string clean: 'Yes' or 'No'. Perform or not a clean_data call to avoid outliers.

        :return: the lightcurve in flux, lightcurve_flux.
        :rtype: array_like
        """

        lightcurve = self.lightcurve_magnitude

        time = lightcurve[:, 0]
        mag = lightcurve[:, 1]
        err_mag = lightcurve[:, 2]

        flux = microltoolbox.magnitude_to_flux(mag)
        error_flux = microltoolbox.error_magnitude_to_error_flux(err_mag, flux)
        lightcurve_in_flux = np.array([time, flux, error_flux]).T

        return lightcurve_in_flux

    def lightcurve_in_magnitude(self):
        """
        Transform flux to magnitude using m = 27.4-2.5*log10(flux) convention. Transform error bar
        accordingly. More details in microltoolbox module.

        :return: the lightcurve in magnitude, lightcurve_magnitude.
        :rtype: array_like
        """
        lightcurve = self.lightcurve_flux

        time = lightcurve[:, 0]
        flux = lightcurve[:, 1]
        error_flux = lightcurve[:, 2]

        magnitude = microltoolbox.flux_to_magnitude(flux)
        error_magnitude = microltoolbox.error_flux_to_error_magnitude(error_flux, flux)

        ligthcurve_magnitude = np.array([time, magnitude, error_magnitude]).T



        return ligthcurve_magnitude
