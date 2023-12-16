import numpy as np
from py_ecc.bn128 import G1, G2, add, multiply, curve_order, eq, Z1, Z2
import galois
import random
from functools import reduce

# Just to make running the tests faster
curve_order = 79

class G1Point:
    def __init__(self, Point):
        self.x = Point[0]
        self.y = Point[1]
    
    def getPoint(self):
            return [
                repr(self.x),
                repr(self.y)
            ]

class G2Point:
    def __init__(self, Point):
        self.x1 = Point[0].coeffs[0]
        self.x2 = Point[0].coeffs[1]
        self.y1 = Point[1].coeffs[0]
        self.y2 = Point[1].coeffs[1]

    def getPoint(self):
            return [
                    [repr(self.x1),
                    repr(self.x2)],
                    [repr(self.y1),
                    repr(self.y2)]
                ]

# curve_order = 79

GF = galois.GF(curve_order)

def invert_negative(row):
    return [curve_order + el if el < 0 else el for el in row]

def interpolate_column(col):
    num_rows = len(col)
    xs = GF(np.array([i for i in range(1, num_rows + 1)]))
    return galois.lagrange_poly(xs, col)

def inner_product_polynomials_with_witness(polys, witness):
    mul_ = lambda x, y: x * y
    sum_ = lambda x, y: x + y
    return reduce(sum_, map(mul_, polys, witness))

def inner_product(ec_points, coeffs, Z):
    return reduce(add, (multiply(point, int(coeff)) for point, coeff in zip(ec_points, coeffs)), Z)

# returns given R1CS matrices and witness vector
def get_r1cs_galois(x, y):
    # Define the matrices
    L = np.array(
            [
                [0, 0, 3, 0, 0, 0],
                [0, 0, 0, 0, 1, 0],
                [0, 0, 1, 0, 0, 0]
            ]
        )

    R = np.array(
            [
                [0, 0, 1, 0, 0, 0],
                [0, 0, 0, 1, 0, 0],
                [0, 0, 0, 5, 0, 0]
            ]
        )

    O = np.array(
            [
                [0, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 1],
                [-3, 1, 1, 2, 0, -1]
            ]
        )
    
    # invert negative elements
    L_galois = GF(np.array(list(map(invert_negative, L))))
    R_galois = GF(np.array(list(map(invert_negative, R))))
    O_galois = GF(np.array(list(map(invert_negative, O))))

    x = GF(x)
    y = GF(y)

    # this is our orignal formula
    out = GF(3) * x * x * y + GF(5) * x * y - x - GF(2) * y + GF(3) 
    v1 = GF(3) * x * x
    v2 = v1 * y

    # the witness vector with the intermediate variables inside
    w = GF(np.array([1, out, x, y, v1, v2]))

    assert all(
        np.equal(
                np.matmul(L_galois, w) * np.matmul(R_galois, w),
                np.matmul(O_galois, w)
            )
        ), "not equal"
    
    # return the matrices and the witness vector on the galois field
    return L_galois, R_galois, O_galois, w

x = random.randint(0, curve_order)
y = random.randint(0, curve_order)

# returns the QAP polynomials
def get_qap(_x, _y):

    L, R, O, w = get_r1cs_galois(_x, _y)

    # axis 0 is the columns.
    # apply_along_axis is the same as doing a for loop over the columns and collecting the results in an array
    U = np.apply_along_axis(interpolate_column, 0, L)
    V = np.apply_along_axis(interpolate_column, 0, R)
    W = np.apply_along_axis(interpolate_column, 0, O)

    a = w

    Ua = inner_product_polynomials_with_witness(U, a)
    Va = inner_product_polynomials_with_witness(V, a)
    Wa = inner_product_polynomials_with_witness(W, a)

    t = galois.Poly([1, curve_order - 1], field = GF) * galois.Poly([1, curve_order - 2], field = GF) * galois.Poly([1, curve_order - 3], field = GF)

    h = (Ua * Va - Wa) // t

    assert Ua * Va == Wa + h * t, "division has a remainder"

    return U, V, W, a, Ua, Va, Wa, h, t

def trusted_setup(U, V, W, t, degree):
    tau = GF(random.randint(1, curve_order - 1))

    # thse values are supposed to be picked randomly by the trusted setup and kept secret
    alpha = GF(2)
    beta = GF(3)
    gammma = GF(4)
    delta = GF(5)
    
    # [tau^0 * G1, tau^1 * G1, ..., tau^degree * G1]
    powers_of_tau_A = [multiply(G1, int(tau ** i)) for i in range(degree + 1)] 
    
    # [tau^0 * G2, tau^1 * G2, ..., tau^degree * G2]
    powers_of_tau_B = [multiply(G2, int(tau ** i)) for i in range(degree + 1)] 



    beta_U_tau = [beta * poly(tau) for poly in U] # [beta * u_0(tau), beta * u_1(tau), ..., beta * u_n-1(tau))]
    alpha_V_tau = [alpha * poly(tau) for poly in V] # [alpha * v_0(tau), alpha * v_1(tau), ..., alpha * v_n-1(tau))]
    W_tau = [poly(tau) for poly in W] # [w_0(tau), w_1(tau), ..., w_n-1(tau))]

    # [
    #    beta*u_0(tau) + alpha*v_0(tau) + w_0(tau), 
    #    beta*u_1(tau) + alpha*v_1(tau) + w_1(tau), 
    #    ..., 
    #    beta*u_n-1(tau) + alpha*v_n-1(tau) + w_n-1(tau)
    #  ]
    C_tau = beta_U_tau + alpha_V_tau + W_tau 

    # [tau^0 * (c*G1), tau^1 * (c*G1), ..., tau^n-1 * (c*G1)]
    powers_of_tau_C = [multiply(G1,int(c)) for c in C_tau]  

    # [tau^0 * (t(tau)*G1), tau^1 * (t(tau)*G1), ..., tau^degree(t) * (t(tau)*G1)]
    powers_of_tau_HT = [multiply(G1, int(tau**i * t(tau))) for i in range(t.degree)] 

    alpha1 = multiply(G1, int(alpha))
    beta2 = multiply(G2, int(beta))

    return powers_of_tau_A, powers_of_tau_B, powers_of_tau_C, powers_of_tau_HT, alpha1, beta2

