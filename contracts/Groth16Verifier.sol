// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.19;

contract Groth16Verifier {
    struct G1Point {
        uint256 x;
        uint256 y;
    }

    struct G2Point {
        uint256[2] x;
        uint256[2] y;
    }

    uint256 constant FIELD_PRIME = 21888242871839275222246405745257275088696311157297823662689037894645226208583;

    G1Point G1 = G1Point(1, 2);
    G2Point G2 = G2Point(
        [
            10857046999023057135944570762232829481370756359578518086990519993285655852781,
            11559732032986387107991004021392285783925812861821192530917403151452391805634
        ],
        [
            8495653923123431417604973247489272438418190587263600148770280649306958101930,
            4082367875863433681332203403145435568316851327593401208105741076214120093531
        ]
    );

    /* 
        Arbitrary constants Alpha1, Beta2, Gamma2, Delta2 to be used in the pairing equation
    */
    // 2 * G1
    G1Point alpha1 = G1Point(
        1368015179489954701390400359078579693043519447331113978918064868415326638035,
        9918110051302171585080402603319702774565515993150576347155970296011118125764
    );
    // 3 * G2
    G2Point beta2 = G2Point(
        [
            2725019753478801796453339367788033689375851816420509565303521482350756874229,
            7273165102799931111715871471550377909735733521218303035754523677688038059653
        ],
        [
            2512659008974376214222774206987427162027254181373325676825515531566330959255,
            957874124722006818841961785324909313781880061366718538693995380805373202866
        ]
    );

    // 4 * G2
    G2Point gamma2 = G2Point(
        [
            18936818173480011669507163011118288089468827259971823710084038754632518263340,
            18556147586753789634670778212244811446448229326945855846642767021074501673839
        ],
        [
            18825831177813899069786213865729385895767511805925522466244528695074736584695,
            13775476761357503446238925910346030822904460488609979964814810757616608848118
        ]
    );

    // 5 * G2
    G2Point delta2 = G2Point(
        [
            20954117799226682825035885491234530437475518021362091509513177301640194298072,
            4540444681147253467785307942530223364530218361853237193970751657229138047649
        ],
        [
            21508930868448350162258892668132814424284302804699005394342512102884055673846,
            11631839690097995216017572651900167465857396346217730511548857041925508482915
        ]
    );

    /*===========================================================================*/
    /*=                              Verifier                                   =*/
    /*===========================================================================*/

    function verify(
        G1Point memory A1,
        G2Point memory B2,
        G1Point memory C1
    ) external view returns(bool) {
        
        G1Point memory negA1 = _neg(A1);

        uint256 num = 18;
        // checks if paring(A1, B2) == pairing(alpha1, beta2) = pairing(C1, G2)
        uint256[18] memory input = [
            // pairing(-A1, B2)
            negA1.x,
            negA1.y,
            B2.x[1],
            B2.x[0],
            B2.y[1],
            B2.y[0],
            // pairing(alpha1, beta2)
            alpha1.x,
            alpha1.y,
            beta2.x[1],
            beta2.x[0],
            beta2.y[1],
            beta2.y[0],
            // pairing(C1, G2)
            C1.x,
            C1.y,
            G2.x[1],
            G2.x[0],
            G2.y[1],
            G2.y[0]
        ];

        bool success = false;
        assembly {
            success := staticcall(gas(), 0x08, input, mul(18, 0x20), input, 0x20)
        }

        require(success, "pairing failed");

        return success;
    }


    /*===========================================================================*/
    /*=                              Helpers                                    =*/
    /*===========================================================================*/

    /**
     * @notice  The negation of p, i.e. p.ecAdd(p.ecNegate()) should be zero.
     * @param   p G1Point to negate
     * @return  G1Point p.ecNegate()
     */
    function _neg(G1Point memory p) private pure returns (G1Point memory) {
        if (p.x == 0 && p.y == 0) {
            return p;
        } else {
            return G1Point(p.x, (FIELD_PRIME - p.y) % FIELD_PRIME);
        }
    }

    /**
     * @notice  add two G1 points A, B on the curve
     * @dev     curve: y^2 = x^3 + 3
     * @param   A  G1 Point A
     * @param   B  G1 Point B
     * @return  G1 Point A + B
     */
    function _ecAdd(G1Point memory A, G1Point memory B) private view returns (G1Point memory) {
        (bool ok, bytes memory result) = address(6).staticcall(abi.encode(A.x, A.y, B.x, B.y));

        require(ok, "failed EC addition");

        return _decodePoint(result);
    }

    /**
     * @notice  multiply EC point P with scalar s
     * @dev     curve: y^2 = x^3 + 3
     * @param   s  scalar
     * @param   P  EC Point
     * @return  EC Point s*P
     */
    function _scalarMul(uint256 s, G1Point memory P) private view returns (G1Point memory) {
        (bool ok, bytes memory result) = address(7).staticcall(abi.encode(P.x, P.y, s));

        require(ok, "failed EC multiplication");

        return _decodePoint(result);
    }

    /**
     * @notice  decode EC point from bytes
     */
    function _decodePoint(bytes memory result) internal pure returns (G1Point memory) {
        G1Point memory point;
        (point.x, point.y) = abi.decode(result, (uint256, uint256));

        return point;
    }
}