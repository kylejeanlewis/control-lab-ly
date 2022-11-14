# %% -*- coding: utf-8 -*-
"""
Created on Fri 2022/03/18 09:00:00

@author: Chang Jie
"""
from easy_biologic import BiologicProgram

class CPLimit( BiologicProgram ):
    """
    Runs a cyclic amperometry technqiue.
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
                [Default: IRange.m10 ]
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
        self._parameter_types = tfs.CALIMIT
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