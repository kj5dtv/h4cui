# -*- coding: utf-8 -*-
"""
com_wrapper.py - part of the h4cui project

This module provides ComWrap and related classes for working with COM objects.

Classes:
    ComWrap: A wrapper for a COM object.

This is free software licensed under the BSD 3-Clause License (see LICENSE file for details).
"""

import pywintypes
from typing import Any, List, Tuple


class ComWrap:
    """A wrapper for a COM object.

    This class provides a convenient way to access the properties of a COM
    object. It retrieves the properties when the instance is created and
    stores them as attributes.

    Attributes:
        o: The COM object.
    """

    def __init__(self, o: Any) -> None:
        """Initializes ComWrap with a COM object.

        Args:
            o: The COM object to wrap.
        """
        self.o = o
        self._set_device_properties()

    def _set_device_properties(self) -> None:
        """Retrieves the properties of the COM object and stores them as attributes.

        If an error occurs while getting the properties, it prints the error
        and continues with an empty property list.
        """
        try:
            device_properties: Any = self.o.GetDeviceProperties()
        except pywintypes.com_error as e:
            print(e)
            device_properties = []

        for prop in device_properties:
            prop_list: List[Any] | Tuple[Any] = (
                prop if isinstance(prop, (list, tuple)) else [prop]
            )
            for p in prop_list:
                if hasattr(p, "KeyName") and hasattr(p, "Data"):
                    setattr(self, p.KeyName, p.Data)
