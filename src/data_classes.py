# -*- coding: utf-8 -*-
"""
data_classes.py - part of the h4cui project

Module for handling devices and ports and part of the h4cui project.

This module provides classes for handling devices and ports, including
physical ports and CNC ports.

Classes:
    Device: Base class for a device.
    CNCBus: Represents a CNC bus.
    CNCPort: Represents a CNC port.
    PhysicalPort: Represents a physical port.
    
This is free software licensed under the BSD 3-Clause License (see LICENSE file for details).
"""

import re
from dataclasses import dataclass, field
import serial
import winreg
from typing import Optional, ClassVar, Type, Any

from com_wrapper import ComWrap
import re

RE_COM_PORT: re.Pattern[str] = re.compile(pattern=r".*(COM\d+)\)$")

@dataclass
class Device:
    """Base class for a device.

    Attributes:
        device: A ComWrap object representing the device.
        instance_id: The instance ID of the device.
    """

    device: ComWrap
    instance_id: str = field(init=False)

    def __post_init__(self) -> None:
        """Initializes instance_id after the instance has been created."""
        self.instance_id = getattr(self.device, "DEVPKEY_Device_InstanceId", "")

    @property
    def port_name(self) -> str:
        """Returns the instance ID of the device."""
        return self.instance_id

    @classmethod
    def from_device(cls: Type['Device'], device: ComWrap) -> 'Device':
        """Creates a Device instance from a ComWrap object."""
        return cls(device)


@dataclass
class CNCBus(Device):
    """Represents a CNC bus. Inherits from Device."""
    pass


@dataclass
class CNCPort(Device):
    """Represents a CNC port. Inherits from Device.

    Attributes:
        port_id: The port ID of the CNC port.
        sibling_instance_id: The instance ID of the sibling device.
        bus_instance_id: The instance ID of the bus.
    """

    port_id: str = field(init=False)
    sibling_instance_id: str = field(init=False)
    bus_instance_id: str = field(init=False)

    def __post_init__(self) -> None:
        """Initializes port_id, sibling_instance_id, and bus_instance_id after the instance has been created."""
        super().__post_init__()
        self.port_id = getattr(self.device, 'DEVPKEY_Device_LocationInfo')
        self.sibling_instance_id = getattr(self.device, 'DEVPKEY_Device_Siblings', '')[0].upper()
        self.bus_instance_id = getattr(self.device, 'DEVPKEY_Device_Parent')

    @staticmethod
    def get_port_name(instance_id: str) -> Optional[str]:
        """Returns the port name for a given instance ID."""
        key_path = r"SYSTEM\CurrentControlSet\Services\com0com\Parameters\{}".format(
            instance_id
        )
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                display_name, reg_type = winreg.QueryValueEx(key, "PortName")
                return display_name
        except FileNotFoundError:
            print("Registry key not found")
        except OSError:
            print("Error opening registry key")

    @property
    def port_name(self) -> Optional[str]:
        """Returns the port name of the CNC port."""
        return CNCPort.get_port_name(self.port_id)

    @property
    def is_primary_port(self) -> bool:
        """Checks if the CNC port is a primary port."""
        return self.port_id.startswith("CNCA")

    @property
    def localized_port_name(self) -> str:
        """Returns the localized port name of the CNC port."""
        return f"\\\\.\\{self.port_name}"

    @property
    def is_in_use(self) -> bool:
        """Checks if the CNC port is in use."""
        try:
            ser = serial.Serial(self.localized_port_name)
            ser.close()
            return False
        except AttributeError:
            raise
        except serial.SerialException as e:
            return True


@dataclass
class PhysicalPort(Device):
    """Represents a physical port. Inherits from Device.

    Attributes:
        port_id: The port ID of the physical port.
        _port_name: The port name of the physical port.
        description: The description of the physical port.
        driver_description: The driver description of the physical port.
    """

    port_id: str = field(init=False)
    _port_name: str = field(init=False)
    description: str = field(init=False)
    driver_description: str = field(init=False)

    def __post_init__(self) -> None:
        """Initializes port_id, _port_name, description, and driver_description after the instance has been created."""
        super().__post_init__()
        self.port_id = getattr(self.device, 'DEVPKEY_Device_LocationInfo')
        devpkey_name = getattr(self.device, 'DEVPKEY_NAME', '')
        match = RE_COM_PORT.match(devpkey_name)
        self._port_name = match.group(1) if match else ''
        self.description = getattr(self.device, 'DEVPKEY_Device_DeviceDesc')
        self.driver_description = getattr(self.device, 'DEVPKEY_Device_DriverDesc')

    @property
    def port_name(self) -> str:
        """Returns the port name of the physical port."""
        return self._port_name

    @property
    def localized_port_name(self) -> str:
        """Returns the localized port name of the physical port."""
        return f"\\\\.\\{self.port_name}"

    @property
    def is_in_use(self) -> bool:
        """Checks if the physical port is in use."""
        try:
            ser = serial.Serial(self.port_name)
            ser.close()
            return False
        except serial.SerialException:
            return True