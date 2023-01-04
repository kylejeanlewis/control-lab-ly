# %% -*- coding: utf-8 -*-
"""
Patched from Easy BioLogic package, documentation can be found at:
https://github.com/bicarlsen/easy-biologic

Created: Tue 2022/01/04 17:13:35
@author: Chang Jie

Notes / actionables:
-
"""
# Standard library imports
import asyncio

# Third party imports
from easy_biologic.device import * # pip install easy-biologic

# Local application imports
print(f"Import: OK <{__name__}>")

class BiologicDeviceLocal(BiologicDevice):
    def __init__(self, address, timeout=5, populate_info=True):
        super().__init__(address, timeout, populate_info)
    
    @property
    def hardware_configuration( self ):
        """
        :returns: List of HardwareConf objects.
        """
        self._validate_connection()

        # if self.kind is not ecl.DeviceCodes.KBIO_DEV_SP300:
        #     raise RuntimeError( 'Hardware configuration is only available for SP-300 devices.' )
        if not ecl.is_in_SP300_family(self.kind):
            raise RuntimeError( 'Hardware configuration is only available for SP-300 family of devices.' )

        confs = {
            ch: self.channel_configuration( ch ) if available else None
            for ch, available in enumerate( self.plugged )
        }

        return confs
    
    def set_channel_configuration( self, ch, mode, connection ):
        """
        Sets the hardware configuration for the given channel.
        :param ch: Channel to set.
        :param mode: ChannelMode.
        :param connection: ElectrodeConnection.
        """
        self._validate_connection()

        # if self.kind is not ecl.DeviceCodes.KBIO_DEV_SP300:
        #     raise RuntimeError( 'Hardware configuration is only available for SP-300 devices.' )
        if not ecl.is_in_SP300_family(self.kind):
            raise RuntimeError( 'Hardware configuration is only available for SP-300 family of devices.' )

        ecl.set_hardware_configuration( self.idn, ch, mode, connection )
        

class BiologicDeviceAsyncLocal(BiologicDeviceAsync):
    async def __init__(self, address, timeout=5, populate_info=True):
        await super().__init__(address, timeout, populate_info)
        
    @property
    async def hardware_configuration( self ):
        """
        :returns: Dictionary of HardwareConfigurations for each channel,
            or None if the channel is not available.
        """
        self._validate_connection()

        # if self.kind is not ecl.DeviceCodes.KBIO_DEV_SP300:
        #     raise RuntimeError( 'Hardware configuration is only available for SP-300 devices.' )
        if not ecl.is_in_SP300_family(self.kind):
            raise RuntimeError( 'Hardware configuration is only available for SP-300 family of devices.' )

        # collect channel configurations for available channels
        available_chs = []
        ch_confs = []
        for ch, available in enumerate( self.plugged ):
            if available:
                available_chs.appned( ch )
                ch_confs.append( self.channel_configuration( ch ) )

        ch_confs = await asyncio.gather( *ch_confs )

        # collect results for all channels
        confs = {
            ch: (
                ch_confs[ available_chs.index( ch ) ] 
                if ch in available_chs else 
                None
            )
            for ch, available in enumerate( self.plugged )
        }

        return confs
    
    async def set_channel_configuration( self, ch, mode, connection ):
        """
        Sets the hardware configuration for the given channel.
        :param ch: Channel to set.
        :param mode: ChannelMode.
        :param connection: ElectrodeConnection.
        """
        self._validate_connection()

        # if self.kind is not ecl.DeviceCodes.KBIO_DEV_SP300:
        #     raise RuntimeError( 'Hardware configuration is only available for SP-300 devices.' )
        if not ecl.is_in_SP300_family(self.kind):
            raise RuntimeError( 'Hardware configuration is only available for SP-300 family of devices.' )

        await ecl.set_hardware_configuration_async( self.idn, ch, mode, connection )
    