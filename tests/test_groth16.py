import pytest
import random
from py_ecc.bn128 import add
from helpers import get_qap, trusted_setup, inner_product, curve_order, Z1, Z2, G1Point, G2Point
from ape import accounts, project

@pytest.fixture
def deployer(accounts):
    return accounts[0]

@pytest.fixture
def groth16Verifier_contract(deployer, project):
    return deployer.deploy(project.Groth16Verifier)

def test_verify(groth16Verifier_contract):
    x = random.randint(1, curve_order - 1)
    y = random.randint(1, curve_order - 1)

    U, V, W, a, Ua, Va, Wa, h, t, l = get_qap(x,y)

    powers_of_tau_A,powers_of_tau_B, powers_of_tau_C_public, powers_of_tau_C_private, powers_of_tau_HT, alpha1, beta2, gamm2, delta2 = trusted_setup(U, V, W, t, Ua.degree, l)

    A1 = inner_product(powers_of_tau_A, Ua.coeffs[::-1], alpha1)
    B2 = inner_product(powers_of_tau_B, Va.coeffs[::-1], beta2)

    C1_prime = inner_product(powers_of_tau_C_private, Wa.coeffs[::-1], Z1) # C_1'
    HT1 = inner_product(powers_of_tau_HT, h.coeffs[::-1], Z1)
    C1 = add(C1_prime, HT1)

    A1_G1 = G1Point(A1)
    B2_G2 = G2Point(B2)
    C1_G1 = G1Point(C1)
    public_inputs = [repr(int(el)) for el in a[:l]]

    assert groth16Verifier_contract.verify(A1_G1.getPoint(), B2_G2.getPoint(), C1_G1.getPoint(), public_inputs)
