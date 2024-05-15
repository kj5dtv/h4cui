# -*- coding: utf-8 -*-
"""
cnc_ports.py - part of the h4cui project

Module with CNCPortUtil class and related functions for handling CNC (com0com) and physical ports.

classes:
    CNCPortUtil: Utility class for handling CNC (com0com) ports.

This is free software licensed under the BSD 3-Clause License (see LICENSE file for details).
"""
from typing import List, Tuple, Any

import wmi
from com_wrapper import ComWrap
from data_classes import CNCBus, CNCPort, PhysicalPort

HUB4COM_PATH = "C:\\Program Files (x86)\\com0com\\hub4com.exe"
STATUS_OK = "OK"
PNP_CLASS_CNC_PORTS = "CNCPorts"
PNP_CLASS_PORTS = "Ports"
DEVICE_ID_ROOT = "ROOT"


class CNCPortUtil:
    """Utility class for handling CNC (com0com) ports.  This modules uses WMI to query for devices and classify 
    them into physical ports, CNC busses, and CNC ports.  It also provides methods for getting primary and secondary 
    CNC port pairs.  This relies on the hub4com utility to create virtual serial ports.  There are wrapper classes
    found in the data_classes module for representing physical ports, CNC busses, and CNC ports.

    Attributes:
        baud (int): Baud rate for the CNC ports.
        hub4com_path (str): Path to the hub4com executable.
        hub4com_output (str): Output from the hub4com command.
        wmi (wmi.WMI): WMI interface object.
        busses (List[CNCBus]): List of CNC bus objects.
        cnc_ports (List[CNCPort]): List of CNC port objects.
        physical_ports (List[PhysicalPort]): List of physical port objects.
    """

    def __init__(self):
        """Initializes CNCPortUtil with default values and classifies devices."""
        self.baud: int = 115200
        self.hub4com_path: str = HUB4COM_PATH
        self.hub4com_output: str = ""
        self.wmi: Any = wmi.WMI()
        all_devices: List[ComWrap] = [ComWrap(d) for d in self.wmi.Win32_PnPEntity() if d.Status == STATUS_OK]

        self.busses: List[CNCBus] = []
        self.cnc_ports: List[CNCPort] = []
        self.physical_ports: List[PhysicalPort] = []

        self._classify_devices(devices=all_devices)

    def _classify_devices(self, devices: List[ComWrap]):
        """Classifies devices into physical ports, CNC busses, and CNC ports.

        Args:
            devices (List[ComWrap]): List of ComWrap objects representing devices.
        """
        for device in devices:
            device_class = getattr(device, "DEVPKEY_Device_Class", "")
            device_instance_id = getattr(device, "DEVPKEY_Device_InstanceId", "")

            if device_class == PNP_CLASS_PORTS:
                self.physical_ports.append(PhysicalPort(device))
            elif device_class == PNP_CLASS_CNC_PORTS:
                if device_instance_id.startswith(DEVICE_ID_ROOT):
                    self.busses.append(CNCBus(device))
                else:
                    self.cnc_ports.append(CNCPort(device))

    @property
    def cnc_port_pairs(self) -> List[Tuple[CNCPort, CNCPort]]:
        """Returns pairs of primary and secondary CNC ports.

        Returns:
            List[Tuple[CNCPort, CNCPort]]: List of tuples where each tuple contains a primary and secondary CNC port.
        """
        secondary_ports_dict = {port.instance_id: port for port in self.secondary_cnc_ports}
        return [(port, secondary_ports_dict[port.sibling_instance_id]) for port in self.primary_cnc_ports if port.sibling_instance_id in secondary_ports_dict]

    @property
    def primary_cnc_ports(self) -> List[CNCPort]:
        """Returns all primary CNC ports.

        Returns:
            List[CNCPort]: List of primary CNC ports.
        """
        return [port for port in self.cnc_ports if port.is_primary_port]

    @property
    def secondary_cnc_ports(self) -> List[CNCPort]:
        """Returns all secondary CNC ports.

        Returns:
            List[CNCPort]: List of secondary CNC ports.
        """
        return [port for port in self.cnc_ports if not port.is_primary_port]