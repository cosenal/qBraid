# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module for configuring provider credentials and authentication.

"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

from qbraid_core.devices import get_devices_raw, get_device_metadata

from qbraid._qdevice import QDEVICE_TYPES

from .exceptions import QbraidDeviceNotFoundError, ResourceNotFoundError

if TYPE_CHECKING:
    import qbraid


class QuantumProvider(ABC):
    """
    This class is responsible for managing the interactions and
    authentications with various Quantum services.
    """

    @abstractmethod
    def save_config(self):
        """Save the current configuration."""

    @abstractmethod
    def get_devices(self):
        """Return a list of backends matching the specified filtering."""

    @abstractmethod
    def get_device(self, vendor_device_id: str):
        """Return quantum device corresponding to the specified device ID."""


class QbraidProvider(QuantumProvider):
    """
    This class is responsible for managing the interactions and
    authentications with the AWS and IBM Quantum services.

    Attributes:
        aws_access_key_id (str): AWS access key ID for authenticating with AWS services.
        aws_secret_access_key (str): AWS secret access key for authenticating with AWS services.
        qiskit_ibm_token (str): IBM Quantum token for authenticating with IBM Quantum services.
    """

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, qiskit_ibm_token=None):
        """
        Initializes the QbraidProvider object with optional AWS and IBM Quantum credentials.

        Args:
            aws_access_key_id (str, optional): AWS access key ID. Defaults to None.
            aws_secret_access_key (str, optional): AWS secret access token. Defaults to None.
            qiskit_ibm_token (str, optional): IBM Quantum token. Defaults to None.
        """
        self._aws_provider = self._get_aws_provider(aws_access_key_id, aws_secret_access_key)
        self._ibm_provider = self._get_ibm_provider(qiskit_ibm_token)

    def save_config(self):
        raise NotImplementedError

    def _get_aws_provider(self, aws_access_key_id, aws_secret_access_key):
        if "braket.aws.aws_device.AwsDevice" not in QDEVICE_TYPES:
            return None

        from qbraid.providers.aws import BraketProvider  # pylint: disable=import-outside-toplevel

        try:
            return BraketProvider(aws_access_key_id, aws_secret_access_key)
        except Exception:  # pylint: disable=broad-exception-caught
            return None

    def _get_ibm_provider(self, qiskit_ibm_token):
        if "qiskit_ibm_provider.ibm_backend.IBMBackend" not in QDEVICE_TYPES:
            return None

        from qbraid.providers.ibm import QiskitProvider  # pylint: disable=import-outside-toplevel

        try:
            return QiskitProvider(qiskit_ibm_token)
        except Exception:  # pylint: disable=broad-exception-caught
            return None

    def _get_ibm_runtime(self, qiskit_ibm_token):
        if "qiskit_ibm_runtime.ibm_backend.IBMBackend" not in QDEVICE_TYPES:
            return None

        from qbraid.providers.ibm import QiskitRuntime  # pylint: disable=import-outside-toplevel

        try:
            return QiskitRuntime(qiskit_ibm_token)
        except Exception:  # pylint: disable=broad-exception-caught
            return None

    def get_devices(self) -> "List[qbraid.QDEVICE]":
        """Return a list of backends matching the specified filtering.

        Returns:
            list[QDEVICE]: a list of Backends that match the filtering
                criteria.
        """
        devices = []

        for provider in [self._aws_provider, self._ibm_provider]:
            if provider is not None:
                devices += provider.get_devices()

        return devices

    @staticmethod
    def _get_vendor(vendor_device_id: str) -> str:
        """Return the software vendor of the specified device."""
        if vendor_device_id.startswith("ibm") or vendor_device_id.startswith("simulator"):
            return "ibm"
        if vendor_device_id.startswith("arn:aws"):
            return "aws"

        device_data = get_devices_raw(params={"objArg": vendor_device_id})
        if len(device_data) == 0:
            raise QbraidDeviceNotFoundError(f"Device {vendor_device_id} not found.")

        try:
            return device_data[0]["vendor"].lower()
        except (IndexError, KeyError) as err:
            raise ResourceNotFoundError(f"Failed to load device due to invalid device data.") from err

    def _get_device(self, vendor_device_id: str, vendor: Optional[str] = None) -> "qbraid.QDEVICE":
        """Return quantum device corresponding to the specified device ID.

        Returns:
            QDEVICE: the quantum device corresponding to the given ID

        Raises:
            QbraidDeviceNotFoundError: if no device could be found
        """
        vendor = vendor or self._get_vendor(vendor_device_id)

        if vendor == "ibm" and self._ibm_provider is not None:
            return self._ibm_provider.get_device(vendor_device_id)

        if vendor == "aws" and self._aws_provider is not None:
            return self._aws_provider.get_device(vendor_device_id)

        raise QbraidDeviceNotFoundError(f"Device {vendor_device_id} not found.")

    def get_device(self, qbraid_device_id: str) -> "qbraid.QDEVICE":
        """Return quantum device corresponding to the specified device ID.

        Returns:
            QDEVICE: the quantum device corresponding to the given ID

        Raises:
            QbraidDeviceNotFoundError: if no device could be found
        """
        try:
            device_data = get_device_metadata(qbraid_id=qbraid_device_id)
        except ValueError as err:
            raise QbraidDeviceNotFoundError(f"Device {qbraid_device_id} not found.") from err

        try:
            vendor = device_data["vendor"].lower()
        except (KeyError, AttributeError):
            vendor = None

        try:
            vendor_device_id = device_data["objArg"]
        except KeyError as err:
            raise ResourceNotFoundError(
                f"Failed to load device due to invalid device data: missing required field 'objArg'."
            ) from err
        
        return self._get_device(vendor_device_id, vendor)
