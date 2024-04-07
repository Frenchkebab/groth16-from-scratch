# Groth16 Implementation from scratch

## Install & Run Script

```
# clone repository
git clone git@github.com:Frenchkebab/groth16-from-scratch.git
cd groth16-from-scratch

# install dependencies
python -m venv ape-devel
source ape-devel/bin/activate
pip install --upgrade pip
pip install eth-ape'[recommended-plugins]'

# run script
ape test
```
Since Field Prim of BN128 curve is very big, this test takes a while


## Groth16Verifier.sol

The contract **`Groth16Verifier.sol`** verifies if the prover knows correct values `out`, `x`, `y` that satisfies the following formula:
$$out = 3x^2y + 5xy - x - 2y + 3$$

Using **Groth16**, the prover can prove the fact that he knows those values without exposing them.

## Resources

To learn more about the process, check out the resources below:

- https://www.rareskills.io/zk-book
- https://www.rareskills.io/post/groth16
- https://github.com/tornadocash/tornado-core/blob/master/contracts/Verifier.sol

