// SPDX-License-Identifier: BUSL-1.1
pragma solidity ^0.8.24;
import {Errors} from "./Errors.sol";

/*//////////////////////////////////////////////////////////////
                       BUILDER WALLETS
//////////////////////////////////////////////////////////////*/

interface IERC20 {
    function balanceOf(address) external view returns (uint256);

    function transfer(address to, uint256 amount) external returns (bool);
}

contract BuilderWallet {
    address public immutable FACTORY;
    address public builderAdmin;

    constructor(address factory) {
        FACTORY = factory;
    }

    function init(address _builderAdmin) external {
        builderAdmin = _builderAdmin;
    }

    function sweep(address token, address to) external {
        if (msg.sender != builderAdmin) revert Errors.NotBuilder();

        uint256 bal = IERC20(token).balanceOf(address(this));
        if (bal == 0) return;

        bool ok = IERC20(token).transfer(to, bal);
        if (!ok) {
            // `from` is this wallet, `balance` is pre-transfer token balance
            revert Errors.TransferFailed(token, address(this), bal, bal);
        }
    }
}

library Create2Lib {
    function deploy(
        uint256 value,
        bytes32 salt,
        bytes memory code
    ) internal returns (address addr) {
        assembly {
            addr := create2(value, add(code, 0x20), mload(code), salt)
        }
        require(addr != address(0), "CREATE2 failed");
    }
}

contract BuilderFactory {
    using Create2Lib for uint256;

    address public immutable OWNER;

    constructor(address owner) {
        if (owner == address(0)) revert Errors.ZeroAddress();
        OWNER = owner;
    }

    modifier onlyOwner() {
        _onlyOwner();
        _;
    }

    function _onlyOwner() internal {
        require(msg.sender == OWNER, "NOT_OWNER");
    }

    /**
     * @notice Deploys a BuilderWallet contract using CREATE2.
     * @param builderCode The uint256 used as the CREATE2 salt (must match caller's referral code).
     * @param builderAdmin The EOA/multisig allowed to sweep tokens from the wallet.
     * @return wallet The deployed wallet address (deterministic).
     */
    function deployBuilder(
        uint48 builderCode,
        address builderAdmin
    ) external onlyOwner returns (address wallet) {
        bytes32 salt = bytes32(uint256(builderCode));

        // Constructor args are part of the init code and therefore part of the CREATE2 address.
        bytes memory initCode = abi.encodePacked(
            type(BuilderWallet).creationCode,
            abi.encode(address(this))
        );

        wallet = Create2Lib.deploy(0, salt, initCode);
        // now set the admin in storage (not part of init code)
        BuilderWallet(wallet).init(builderAdmin);
    }

    /**
     * @notice Computes the CREATE2 address for (builderCode, builderAdmin).
     * @dev Must match the formula used in the RiskEngine.
     */
    function predictBuilderWallet(uint48 builderCode) external view returns (address) {
        bytes32 salt = bytes32(uint256(builderCode));

        bytes32 initCodeHash = keccak256(
            abi.encodePacked(type(BuilderWallet).creationCode, abi.encode(address(this)))
        );

        bytes32 h = keccak256(abi.encodePacked(bytes1(0xff), address(this), salt, initCodeHash));

        return address(uint160(uint256(h)));
    }
}
