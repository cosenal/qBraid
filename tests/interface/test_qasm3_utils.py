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
Unit tests for OpenQASM 3 utility functions.

"""

import logging
import os

import numpy as np
import pytest
from qiskit.circuit import QuantumCircuit
from qiskit.qasm3 import dumps, loads

from qbraid.interface import circuits_allclose, random_circuit
from qbraid.interface.qbraid_qasm3.random_circuit import _qasm3_random
from qbraid.interface.qbraid_qasm3.tools import (
    _convert_to_contiguous_qasm3,
    convert_to_qasm3,
    qasm3_depth,
    qasm3_num_qubits,
    qasm3_qubits,
)

from .._data.qasm3.circuits import qasm3_bell, qasm3_shared15

lib_dir = os.path.dirname(os.path.dirname(__file__))
qasm3_lib = os.path.join(lib_dir, "_data", "qasm3", "qelib_qasm3.qasm")
with open(qasm3_lib, mode="r", encoding="utf-8") as file:
    gate_def_qasm3 = file.read()


def test_qasm_qubits():
    """Test getting QASM qubits"""

    assert qasm3_qubits(qasm3_bell()) == [("q", 2)]
    assert qasm3_qubits(qasm3_shared15()) == [("q", 4)]


def test_qasm3_num_qubits():
    """Test calculating number of qubits in qasm3 circuit"""
    num_qubits = np.random.randint(2, 10)
    qiskit_circuit = random_circuit("qiskit", num_qubits=num_qubits)
    qasm3_str = dumps(qiskit_circuit)
    assert qasm3_num_qubits(qasm3_str) == num_qubits


def test_qasm3_depth():
    """Test calculating qasm depth of qasm3 circuit"""
    depth = np.random.randint(2, 10)
    qasm3_str = _qasm3_random(depth=depth, seed=42)
    assert qasm3_depth(qasm3_str) == depth


@pytest.mark.skip(reason="QASM3ImporterError")
def test_qasm3_depth_alternate_qubit_syntax():
    """Test calculating qasm depth of qasm3 circuit"""
    qasm3_str = """OPENQASM 3.0;
bit[1] __bits__;
qubit[1] __qubits__;
h __qubits__[0];
__bits__[0] = measure __qubits__[0];"""
    assert qasm3_depth(qasm3_str) == 1


def _check_output(output, expected):
    actual_circuit = loads(output)
    expected_circuit = loads(expected)
    assert actual_circuit == expected_circuit


@pytest.mark.parametrize(
    "num_qubits, depth, max_operands, seed, measure",
    [
        (
            None,
            None,
            None,
            None,
            False,
        ),  # Test case 1: Generate random circuit with default parameters
        (3, 3, 3, 42, False),  # Test case 2: Generate random circuit with specified parameters
        (None, None, None, None, True),  # Test case 3: Generate random circuit with measurement
    ],
)
def test_qasm3_random(num_qubits, depth, max_operands, seed, measure):
    """Test random circuit generation using _qasm_random"""

    circuit = _qasm3_random(
        num_qubits=num_qubits, depth=depth, max_operands=max_operands, seed=seed, measure=measure
    )
    assert qasm3_num_qubits(circuit) >= 1
    if num_qubits is not None:
        assert qasm3_num_qubits(circuit) == num_qubits


def test_qasm3_random_with_known_seed():
    """Test generating random OpenQASM 3 circuit from known seed"""
    circuit = _qasm3_random(num_qubits=3, depth=3, max_operands=3, seed=42, measure=True)
    assert qasm3_num_qubits(circuit) == 3

    out__expected = """
// Random Circuit generated by qBraid
OPENQASM 3.0;
include "stdgates.inc";
/*
    seed = 42
    num_qubits = 3
    depth = 3
    max_operands = 3
*/
qubit[3] q;
bit[3] c;
y q[0];
crx(5.3947298351621535) q[1],q[2];
cz q[0],q[2];
t q[1];
cp(0.8049616944763924) q[1],q[2];
u1(2.829858307545725) q[0];
c[0] = measure q[0];
c[1] = measure q[1];
c[2] = measure q[2];

"""
    _check_output(circuit, out__expected)


def test_convert_to_expanded_contiguous_qasm_3():
    """Test conversion of qasm3 to expanded contiguous qasm3"""
    qasm_test = """
    OPENQASM 3.0;
    gate custom q1, q2, q3{
        x q1;
        y q2;
        z q3;
    }
    qreg q1[2];
    qubit[2] q2;
    qubit[3] q3;
    qubit q4;
    
    x q1[0];
    y q2[0];
    z q3;
    """

    qasm_expected = qasm_test + """i q1[1];\ni q2[1];\ni q4[0];\n"""

    assert _convert_to_contiguous_qasm3(qasm_test, expansion=True) == qasm_expected


def test_convert_to_compressed_contiguous_qasm_3():
    """Test conversion of qasm3 to compressed contiguous qasm3"""
    qasm_test = """
    OPENQASM 3.0;
    gate custom q1, q2, q3{
        x q1;
        y q2;
        z q3;
    }
    qreg q1[2];
    qubit[2] q2;
    qubit[3] q3;
    qubit q4;
    qubit[5]   q5;
    qreg qr[3];
    
    x q1[0];
    y q2[1];
    z q3;
    
    
    qubit[3] q6;
    
    cx q6[1], q6[2];
    """

    qasm_expected = """
    OPENQASM 3.0;
    gate custom q1, q2, q3{
        x q1;
        y q2;
        z q3;
    }
    qreg q1[1];
    qubit[1] q2;
    qubit[3] q3;
    
    
    
    
    x q1[0];
    y q2[0];
    z q3;
    
    
    qubit[2] q6;
    
    cx q6[0], q6[1];
    """

    assert _convert_to_contiguous_qasm3(qasm_test, expansion=False) == qasm_expected


QASM_TEST_DATA = [
    (
        """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[1] ;
qreg qubits  [10]   ;
creg c[1];
creg bits   [12]   ;
        """,
        f"""
OPENQASM 3.0;
include "stdgates.inc";
{gate_def_qasm3}
qubit[1] q;
qubit[10] qubits;
bit[1] c;
bit[12] bits;
        """,
    ),
    (
        """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
measure q->c;
measure q[0] -> c[1];
        """,
        f"""
OPENQASM 3.0;
include "stdgates.inc";
{gate_def_qasm3}
qubit[2] q;
bit[2] c;
c = measure q;
c[1] = measure q[0];
        """,
    ),
    (
        """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
opaque custom_gate (a,b,c) p,q,r;
        """,
        f"""
OPENQASM 3.0;
include "stdgates.inc";
{gate_def_qasm3}
qubit[2] q;
bit[2] c;
// opaque custom_gate (a,b,c) p,q,r;
        """,
    ),
    (
        """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
        """,
        f"""
OPENQASM 3.0;
include "stdgates.inc";
{gate_def_qasm3}
qubit[1] q;
        """,
    ),
    (
        """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[5];
u(1,2,3) q[0];
sxdg q[0];
csx q[0], q[1];
cu1(0.5) q[0], q[1];
cu3(1,2,3) q[0], q[1];
rzz(0.5) q[0], q[1];
rccx q[0], q[1], q[2];
rc3x q[0], q[1], q[2], q[3];
c3x q[0], q[1], q[2], q[3];
c3sqrtx q[0], q[1], q[2], q[3];
c4x q[0], q[1], q[2], q[3], q[4];
        """,
        f"""
OPENQASM 3.0;   
include "stdgates.inc";
{gate_def_qasm3}
qubit[5] q;
U(1,2,3) q[0];
sxdg q[0];
csx q[0], q[1];
cu1(0.5) q[0], q[1];
cu3(1,2,3) q[0], q[1];
rzz(0.5) q[0], q[1];
rccx q[0], q[1], q[2];
rc3x q[0], q[1], q[2], q[3];
c3x q[0], q[1], q[2], q[3];
c3sqrtx q[0], q[1], q[2], q[3];
c4x q[0], q[1], q[2], q[3], q[4];
        """,
    ),
]


@pytest.mark.parametrize("test_input, expected_output", QASM_TEST_DATA)
def test_convert_to_qasm3_parametrized(test_input, expected_output):
    """Test the conversion of OpenQASM 2 to 3"""
    _check_output(convert_to_qasm3(test_input), expected_output)


def _generate_valid_qasm_strings(seed=42, gates_to_skip=None, num_circuits=100):
    """Returns a list of 100 random qasm2 strings
    which do not contain any of the gates in gates_to_skip

    Current list of invalid gates is ["u", "cu1", "cu2", "cu3", "rxx"]
    For the motivation, see discussion
    - https://github.com/Qiskit/qiskit-qasm3-import/issues/12
    - https://github.com/Qiskit/qiskit-qasm3-import/issues/11#issuecomment-1568505732
    """
    if gates_to_skip is None:
        gates_to_skip = []

    qasm_strings = []
    while len(qasm_strings) < num_circuits:
        try:
            circuit_random = random_circuit("qiskit", seed=seed)
            qasm_str = circuit_random.qasm()
            circuit_from_qasm = QuantumCircuit.from_qasm_str(qasm_str)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logging.error("Invalid QASM generated by random_circuit: %s", e)
            continue

        for gate in gates_to_skip:
            if len(circuit_from_qasm.get_instructions(gate)) > 0:
                break
        else:
            qasm_strings.append(qasm_str)

    return qasm_strings


@pytest.mark.parametrize("qasm2_str", _generate_valid_qasm_strings(gates_to_skip=["r"]))
def test_random_conversion_to_qasm3(qasm2_str):
    """test random gates conversion"""
    qasm3_str = convert_to_qasm3(qasm2_str)
    circuit_orig = QuantumCircuit.from_qasm_str(qasm2_str)
    circuit_test = loads(qasm3_str)

    # ensure that the conversion is correct
    assert circuits_allclose(circuit_orig, circuit_test)


@pytest.mark.skip(reason="Qiskit terra bug")
def test_u0_gate_conversion():
    """test u0 gate conversion
    Separate test due to bug in terra,
    see https://github.com/Qiskit/qiskit-terra/issues/10184
    """

    test_u0 = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[1];
    u0(0.5) q[0];"""

    test_u0_expected = f"""
    OPENQASM 3.0;
    include "stdgates.inc";
    {gate_def_qasm3}
    qubit[1] q;
    u0(0.5) q[0];
    """

    _check_output(convert_to_qasm3(test_u0), test_u0_expected)


def test_rxx_gate_conversion():
    """Test rxx gate conversion"""

    test_rxx = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[3];
    rxx(0.5) q[0], q[1];"""

    test_rxx_expected = f"""
    OPENQASM 3.0;
    include "stdgates.inc";
    {gate_def_qasm3}
    qubit[3] q;

    // rxx gate
    h q[0];
    h q[1];
    cx q[0],q[1];
    rz(0.5) q[1];
    cx q[0],q[1];
    h q[1];
    h q[0];
    """

    _check_output(convert_to_qasm3(test_rxx), test_rxx_expected)
