# %% -*- coding: utf-8 -*-
"""
Patched from Easy BioLogic package, documentation can be found at:
https://github.com/bicarlsen/easy-biologic

Created on Fri 2022/11/14 17:00:00
@author: Chang Jie

Notes / actionables:
- 
"""
# Standard library imports
from enum import Enum

# Third party imports
from easy_biologic.base_programs import * # pip install easy-biologic

# Local application imports
print(f"Import: OK <{__name__}>")

PROGRAM_LIST = [
    'OCV', 'CA', 'CP', 'CALimit', 'CPLimit', 'PEIS', 'GEIS', 'JV_Scan', 
    'MPP_Tracking', 'MPP', 'MPP_Cycles'
]
INPUTS_LIST = []

class CALIMIT( Enum ):
    Voltage_step      = float
    vs_initial        = bool
    Duration_step     = float
    Step_number       = int ###
    Record_every_dT   = float
    Record_every_dI   = float
    Test1_Config      = int
    Test1_Value       = float
    Test2_Config      = int
    Test2_Value       = float
    Test3_Config      = int
    Test3_Value       = float
    Exit_Cond         = int
    N_Cycles          = int

class CPLIMIT( Enum ):
    Current_step      = float
    vs_initial        = bool
    Duration_step     = float
    Step_number       = int ###
    Record_every_dT   = float
    Record_every_dE   = float
    Test1_Config      = int
    Test1_Value       = float
    Test2_Config      = int
    Test2_Value       = float
    Test3_Config      = int
    Test3_Value       = float
    Exit_Cond         = int
    N_Cycles          = int


class CALimit( BiologicProgram ):
    """
    Runs a chrono-amperometry technique with limits technqiue.
    """
    # TODO: Add limit conditions as parameters, not hard coded
    def __init__(
        self,
        device,
        params,
        **kwargs
    ):
        """
        :param device: BiologicDevice.
        :param params: Program parameters.
            Params are
            voltages: List of voltages in Volts.
            durations: List of times in seconds.
            vs_initial: If step is vs. initial or previous.
                [Default: False]
            time_interval: Maximum time interval between points.
                [Default: 1]
            current_interval: Maximum current change between points.
                [Default: 0.001]
            current_range: Current range. Use ec_lib.IRange.
                [Default: IRange.m10]
        :param **kwargs: Parameters passed to BiologicProgram.
        """
        defaults = {
            'vs_initial':       False,
            'time_interval':    1.0,
            'current_interval': 1e-3,
            'current_range':    ecl.IRange.m10
        }

        channels = kwargs[ 'channels' ] if ( 'channels' in kwargs ) else None
        params = set_defaults( params, defaults, channels )

        super().__init__(
            device,
            params,
            **kwargs
        )

        self._techniques = [ 'calimit' ]
        self._parameter_types = CALIMIT
        self._data_fields = (
            dp.SP300_Fields.CALIMIT
            if ecl.is_in_SP300_family( self.device.kind ) else
            dp.VMP3_Fields.CALIMIT
        )

        self.field_titles = [
            'Time [s]',
            'Voltage [V]',
            'Current [A]',
            'Power [W]',
            'Cycle'
        ]
        
        self._fields = namedtuple( 'CALimit_Datum', [
            'time', 'voltage', 'current', 'power', 'cycle'
        ] )

        self._field_values = lambda datum, segment: (
            dp.calculate_time(
                datum.t_high,
                datum.t_low,
                segment.info,
                segment.values
            ),

            datum.voltage,
            datum.current,
            datum.voltage* datum.current,  # power
            datum.cycle
        )


    def run( self, retrieve_data = True ):
        """
        :param retrieve_data: Automatically retrieve and disconnect from device.
            [Default: True]
        """
        params = {}
        for ch, ch_params in self.params.items():
            steps = len( ch_params[ 'voltages' ] )
            params[ ch ] = {
                'Voltage_step':      ch_params[ 'voltages' ],
                'vs_initial':        [ ch_params[ 'vs_initial' ] ]* steps,
                'Duration_step':     ch_params[ 'durations' ],
                'Step_number':       steps - 1,
                'Record_every_dT':   ch_params[ 'time_interval' ],
                'Record_every_dI':   ch_params[ 'current_interval' ],
                'Test1_Config':      0, # TODO
                'Test1_Value':       0,
                'Test2_Config':      0,
                'Test2_Value':       0,
                'Test3_Config':      0,
                'Test3_Value':       0,
                'Exit_Cond':         0,
                'N_Cycles':          0,
                'I_Range':           ch_params[ 'current_range' ].value
            }


        # run technique
        data = self._run( 'calimit', params, retrieve_data = retrieve_data )


    def update_voltages(
        self,
        voltages,
        durations  = None,
        vs_initial = None
    ):
        """
        Update voltage and duration parameters.
        :param voltages: Dictionary of voltages list keyed by channel,
            or single voltage to apply to all channels.
        :param durations: Dictionary of durations list keyed by channel,
            or single duration to apply to all channels.
        :param vs_initial: Dictionary of vs. initials list keyed by channel,
            or single vs. initial boolean to apply to all channels.
        """
        # format params
        if not isinstance( voltages, dict ):
            # transform to dictionary if needed
            voltages = { ch: voltages for ch in self.channels }

        if ( durations is not None ) and ( not isinstance( voltages, dict ) ):
            # transform to dictionary if needed
            durations = { ch: durations for ch in self.channels }

        if ( vs_initial is not None ) and ( not isinstance( vs_initial, dict ) ):
            # transform to dictionary if needed
            vs_initial = { ch: vs_initial for ch in self.channels }

        # update voltages
        for ch, ch_voltages in voltages.items():
            if not isinstance( ch_voltages, list ):
                # single voltage given, make list
                ch_voltages = [ ch_voltages ]

            steps = len( ch_voltages )
            params = {
                'Voltage_step': ch_voltages,
                'Step_number':  steps - 1
            }

            if ( durations is not None ) and ( durations[ ch ] ):
                params[ 'Duration_step' ] = durations[ ch ]

            if ( vs_initial is not None ) and ( vs_initial[ ch ] ):
                params[ 'vs_initial' ] = vs_initial[ ch ]

            self.device.update_parameters(
                ch,
                'calimit',
                params,
                types = self._parameter_types
            )


class CPLimit( BiologicProgram ):
    """
    Runs a chrono-potentiommetry technique with limits technique.
    """
    # TODO: Add limit conditions as parameters, not hard coded
    def __init__(
        self,
        device,
        params,
        **kwargs
    ):
        """
        :param device: BiologicDevice.
        :param params: Program parameters.
            Params are
            currents: List of currents in Amperes.
            durations: List of times in seconds.
            vs_initial: If step is vs. initial or previous.
                [Default: False]
            time_interval: Maximum time interval between points.
                [Default: 1]
            voltage_interval: Maximum voltage change between points.
                [Default: 0.001]
            voltage_range: Voltage range. Use ec_lib.ERange.
                [Default: ERange.v2_5 ]
        :param **kwargs: Parameters passed to BiologicProgram.
        """
        defaults = {
            'vs_initial':       False,
            'time_interval':    1.0,
            'voltage_interval': 1e-3,
            'voltage_range':    ecl.ERange.v2_5
        }

        channels = kwargs[ 'channels' ] if ( 'channels' in kwargs ) else None
        params = set_defaults( params, defaults, channels )

        super().__init__(
            device,
            params,
            **kwargs
        )

        self._techniques = [ 'cplimit' ] # name of .ecc technique file
        self._parameter_types = CPLIMIT
        self._data_fields = (
            dp.SP300_Fields.CPLIMIT
            if ecl.is_in_SP300_family( self.device.kind ) else
            dp.VMP3_Fields.CPLIMIT
        )

        self.field_titles = [
            'Time [s]',
            'Current [A]',
            'Voltage [V]',
            'Power [W]',
            'Cycle'
        ]
        
        self._fields = namedtuple( 'CPLimit_Datum', [
            'time', 'current', 'voltage', 'power', 'cycle'
        ] )

        self._field_values = lambda datum, segment: (
            dp.calculate_time(
                datum.t_high,
                datum.t_low,
                segment.info,
                segment.values
            ),

            datum.current,
            datum.voltage,
            datum.current* datum.voltage,  # power
            datum.cycle
        )


    def run( self, retrieve_data = True ):
        """
        :param retrieve_data: Automatically retrieve and disconnect from device.
            [Default: True]
        """
        params = {}
        for ch, ch_params in self.params.items():
            steps = len( ch_params[ 'currents' ] )
            params[ ch ] = {
                'Current_step':      ch_params[ 'currents' ],
                'vs_initial':        [ ch_params[ 'vs_initial' ] ]* steps,
                'Duration_step':     ch_params[ 'durations' ],
                'Step_number':       steps - 1,
                'Record_every_dT':   ch_params[ 'time_interval' ],
                'Record_every_dE':   ch_params[ 'voltage_interval' ],
                'Test1_Config':      0, # TODO
                'Test1_Value':       0,
                'Test2_Config':      0,
                'Test2_Value':       0,
                'Test3_Config':      0,
                'Test3_Value':       0,
                'Exit_Cond':         0,
                'N_Cycles':          0,
                'I_Range':           ch_params[ 'voltage_range' ].value
            }


        # run technique
        data = self._run( 'cplimit', params, retrieve_data = retrieve_data )


    def update_currents(
        self,
        currents,
        durations  = None,
        vs_initial = None
    ):
        """
        Update current and duration parameters.
        :param currents: Dictionary of currents list keyed by channel,
            or single current to apply to all channels.
        :param durations: Dictionary of durations list keyed by channel,
            or single duration to apply to all channels.
        :param vs_initial: Dictionary of vs. initials list keyed by channel,
            or single vs. initial boolean to apply to all channels.
        """
        # format params
        if not isinstance( currents, dict ):
            # transform to dictionary if needed
            currents = { ch: currents for ch in self.channels }

        if ( durations is not None ) and ( not isinstance( currents, dict ) ):
            # transform to dictionary if needed
            durations = { ch: durations for ch in self.channels }

        if ( vs_initial is not None ) and ( not isinstance( vs_initial, dict ) ):
            # transform to dictionary if needed
            vs_initial = { ch: vs_initial for ch in self.channels }

        # update currents
        for ch, ch_currents in currents.items():
            if not isinstance( ch_currents, list ):
                # single voltage given, make list
                ch_currents = [ ch_currents ]

            steps = len( ch_currents )
            params = {
                'Current_step': ch_currents,
                'Step_number':  steps - 1
            }

            if ( durations is not None ) and ( durations[ ch ] ):
                params[ 'Duration_step' ] = durations[ ch ]

            if ( vs_initial is not None ) and ( vs_initial[ ch ] ):
                params[ 'vs_initial' ] = vs_initial[ ch ]

            self.device.update_parameters(
                ch,
                'cplimit',
                params,
                types = self._parameter_types
            )


class CV( BiologicProgram ):
    """
    Runs a cyclic voltammetry technique.
    """
    def __init__(
        self,
        device,
        params,
        **kwargs
    ):
        """
        :param device: BiologicDevice.
        :param params: Program parameters.
            Params are
            voltages: List of voltages in Volts. [Ei, E1, E2, Ei, Ef]
                Refers to initial, 1st vertex, 2nd vertex, initial, and final voltages respectively.
            scan_rate: List of scan rates in mV/s.
            vs_initial: If step is vs. initial or previous.
                [Default: False]
            voltage_interval: Maximum voltage change between points.
                [Default: 0.001]
            wait: Wait for fraction of step before starting to measure.
                [Default: 0.5]
            cycles: Number of cycles to sweep.
                [Default: 1]
        :param **kwargs: Parameters passed to BiologicProgram.
        """
        defaults = {
            'vs_initial':       False,
            'current_interval': 0.001,
            'wait':             0.5,
            'cycles':           1,
        }

        channels = kwargs[ 'channels' ] if ( 'channels' in kwargs ) else None
        params = set_defaults( params, defaults, channels )

        super().__init__(
            device,
            params,
            **kwargs
        )

        self._techniques = [ 'cv' ]
        self._parameter_types = tfs.CV
        self._data_fields = (
            dp.SP300_Fields.CV
            if ecl.is_in_SP300_family( self.device.kind ) else
            dp.VMP3_Fields.CV
        )

        self.field_titles = [
            'Time [s]',
            'Voltage [V]',
            'Current [A]',
            'Charge [C]',
            'Cycle'
        ]
        
        self._fields = namedtuple( 'CV_Datum', [
            'time', 'voltage', 'current', 'charge', 'cycle'
        ] )

        self._field_values = lambda datum, segment: (
            dp.calculate_time(
                datum.t_high,
                datum.t_low,
                segment.info,
                segment.values
            ),

            datum.voltage,
            datum.current,
            datum.current * (segment.values.TimeBase*( ( datum.t_high << 32 ) + datum.t_low )),  # charge
            datum.cycle
        )


    def run( self, retrieve_data = True ):
        """
        :param retrieve_data: Automatically retrieve and disconnect from device.
            [Default: True]
        """
        params = {}
        for ch, ch_params in self.params.items():
            steps = len( ch_params[ 'voltages' ] )
            params[ ch ] = {
                'vs_initial':        [ ch_params[ 'vs_initial' ] ]* steps,
                'Voltage_step':      ch_params[ 'voltages' ],
                'Scan_Rate':         [ ch_params[ 'scan_rate' ] ]* steps,
                'Scan_number':       2,
                'Record_every_dE':   ch_params[ 'voltage_interval' ],
                'Average_over_dE':   True,
                'N_Cycles':          ch_params[ 'cycles' ],
                'Begin_measuring_I': ch_params[ 'wait' ],
                'End_measuring_I':   1
            }


        # run technique
        data = self._run( 'cv', params, retrieve_data = retrieve_data )


    def update_voltages(
        self,
        voltages,
        durations  = None,
        vs_initial = None
    ):
        """
        Update voltage and duration parameters.
        :param voltages: Dictionary of voltages list keyed by channel,
            or single voltage to apply to all channels.
        :param durations: Dictionary of durations list keyed by channel,
            or single duration to apply to all channels.
        :param vs_initial: Dictionary of vs. initials list keyed by channel,
            or single vs. initial boolean to apply to all channels.
        """
        # format params
        if not isinstance( voltages, dict ):
            # transform to dictionary if needed
            voltages = { ch: voltages for ch in self.channels }

        if ( durations is not None ) and ( not isinstance( voltages, dict ) ):
            # transform to dictionary if needed
            durations = { ch: durations for ch in self.channels }

        if ( vs_initial is not None ) and ( not isinstance( vs_initial, dict ) ):
            # transform to dictionary if needed
            vs_initial = { ch: vs_initial for ch in self.channels }

        # update voltages
        for ch, ch_voltages in voltages.items():
            if not isinstance( ch_voltages, list ):
                # single voltage given, make list
                ch_voltages = [ ch_voltages ]

            steps = len( ch_voltages )
            params = {
                'Voltage_step': ch_voltages,
                'Step_number':  steps - 1
            }

            if ( durations is not None ) and ( durations[ ch ] ):
                params[ 'Duration_step' ] = durations[ ch ]

            if ( vs_initial is not None ) and ( vs_initial[ ch ] ):
                params[ 'vs_initial' ] = vs_initial[ ch ]

            self.device.update_parameters(
                ch,
                'calimit',
                params,
                types = self._parameter_types
            )

     
class GEIS( BiologicProgram ):
    """
    Runs Galvano Electrochemical Impedance Spectroscopy technique.
    """

    def __init__(
        self,
        device,
        params,
        **kwargs
    ):
        """
        :param device: BiologicDevice.
        :param params: Program parameters.
            Params are
            current: Initial current in Ampere.
            amplitude_current: Sinus amplitude in Ampere.
            initial_frequency: Initial frequency in Hertz.
            final_frequency: Final frequency in Hertz.
            frequency_number: Number of frequencies.
            duration: Overall duration in seconds. # Comment: Isn't this really a step duration?
            vs_initial: If step is vs. initial or previous.
                [Default: False]
            time_interval: Maximum time interval between points in seconds.
                [Default: 1]
            potential_interval: Maximum interval between points in Volts.
                [Default: 0.001]
            sweep: Defines whether the spacing between frequencies is logarithmic
                ('log') or linear ('lin'). [Default: 'log']
            repeat: Number of times to repeat the measurement and average the values
                for each frequency. [Default: 1]
            correction: Drift correction. [Default: False]
            wait: Adds a delay before the measurement at each frequency. The delay
                is expressed as a fraction of the period. [Default: 0]
        :param **kwargs: Parameters passed to BiologicProgram.
        """
        # set sweep to false if spacing is logarithmic
        if 'sweep' in params:
            if params.sweep == 'log': ###
                params.sweep = False

            elif params.sweep == 'lin': ###
                params.sweep = True

            else:
                raise ValueError( 'Invalid sweep parameter' )

        defaults = {
            'vs_initial':           False,
            'vs_final':             False,
            'time_interval':        1,
            'potential_interval':   0.001,
            'sweep':                False,
            'repeat':               1,
            'correction':           False,
            'wait':                 0
        }

        channels = kwargs[ 'channels' ] if ( 'channels' in kwargs ) else None
        params = set_defaults( params, defaults, channels )
        super().__init__(
            device,
            params,
            **kwargs
        )

        for ch, ch_params in self.params.items():
            ch_params[ 'current_range' ] = self._get_current_range(
                ch_params[ 'current' ]
            )

        self._techniques = [ 'geis' ]
        self._parameter_types = tfs.GEIS
        self._data_fields = (
            dp.SP300_Fields.GEIS
            if ecl.is_in_SP300_family( self.device.kind ) else
            dp.VMP3_Fields.GEIS
        )
        
        self.field_titles = [
            'Process',
            'Time [s]',
            'Voltage [V]',
            'Current [A]',
            'abs( Voltage ) [V]',
            'abs( Current ) [A]',
            'Impendance phase',
            'Voltage_ce [V]',
            'abs( Voltage_ce ) [V]',
            'abs( Current_ce ) [A]',
            'Impendance_ce phase',
            'Frequency [Hz]'
        ]
        
        self._fields = namedtuple( 'GEIS_datum', [
            'process',
            'time',
            'voltage',
            'current',
            'abs_voltage',
            'abs_current',
            'impendance_phase',
            'voltage_ce',
            'abs_voltage_ce',
            'abs_current_ce',
            'impendance_ce_phase',
            'frequency'
        ] )
       
        def _geis_fields( datum, segment ):
            """
            Define fields for _run function.
            """
            if segment.info.ProcessIndex == 0:
                f = (
                    segment.info.ProcessIndex,
                    dp.calculate_time(
                        datum.t_high,
                        datum.t_low,
                        segment.info,
                        segment.values
                    ),
                    datum.voltage,
                    datum.current,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None
                )

            elif segment.info.ProcessIndex == 1:
                f = (
                    segment.info.ProcessIndex,
                    datum.time,
                    datum.voltage,
                    datum.current,
                    datum.abs_voltage,
                    datum.abs_current,
                    datum.impendance_phase,
                    datum.voltage_ce,
                    datum.abs_voltage_ce,
                    datum.abs_current_ce,
                    datum.impendance_ce_phase,
                    datum.frequency
                )

            else:
                raise RuntimeError( f'Invalid ProcessIndex ({segment.info.ProcessIndex})' )

            return f

        self._field_values = _geis_fields


    def run( self, retrieve_data = True ):
        """
        :param retrieve_data: Automatically retrieve and disconenct from device.
            [Default: True]
        """
        params = {}
        for ch, ch_params in self.params.items():
            params[ ch ] = {
                'vs_initial':           ch_params[ 'vs_initial' ],
                'vs_final':             ch_params[ 'vs_initial' ],
                'Initial_Current_step': ch_params[ 'current' ],
                'Final_Current_step':   ch_params[ 'current' ],
                'Duration_step':        ch_params[ 'duration' ],
                'Step_number':          0,
                'Record_every_dT':      ch_params[ 'time_interval' ],
                'Record_every_dE':      ch_params[ 'potential_interval' ],
                'Final_frequency':      ch_params[ 'final_frequency' ],
                'Initial_frequency':    ch_params[ 'initial_frequency' ],
                'sweep':                ch_params[ 'sweep' ],
                'Amplitude_Current':    ch_params[ 'amplitude_current' ],
                'Frequency_number':     ch_params[ 'frequency_number' ],
                'Average_N_times':      ch_params[ 'repeat' ],
                'Correction':           ch_params[ 'correction' ],
                'Wait_for_steady':      ch_params[ 'wait' ],
                'I_Range':              ch_params[ 'current_range' ].value
            }

        # run technique
        data = self._run( 'geis', params, retrieve_data = retrieve_data )


    def _get_current_range( self, currents ):
        """
        Get current range based on maximum current.
        :param currents: List of currents.
        :returns: ec_lib.IRange corresponding to largest current.
        """
        i_max = abs( currents ) ###

        if i_max < 100e-12:
            i_range = ecl.IRange.p100

        elif i_max < 1e-9:
            i_range = ecl.IRange.n1

        elif i_max < 10e-9:
            i_range = ecl.IRange.n10

        elif i_max < 100e-9:
            i_range = ecl.IRange.n100

        elif i_max < 1e-6:
            i_range = ecl.IRange.u1

        elif i_max < 10e-6:
            i_range = ecl.IRange.u10

        elif i_max < 100e-6:
            i_range = ecl.IRange.u100

        elif i_max < 1e-3:
            i_range = ecl.IRange.m1

        elif i_max < 10e-3:
            i_range = ecl.IRange.m10

        elif i_max < 100e-3:
            i_range = ecl.IRange.m100

        elif i_max <= 1:
            i_range = ecl.IRange.a1

        else:
            raise ValueError( 'Current too large.' )

        return i_range    
    
