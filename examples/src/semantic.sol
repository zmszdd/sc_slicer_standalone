// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

// 干扰合约 1: 日志记录器 (典型的副作用干扰)
contract AuditLogger {
    event Access(address user, uint256 time);
    // 静态分析通常认为 External Call 是危险的/相关的，因此会保留此合约
    function logAccess(address _user) external {
        emit Access(_user, block.timestamp);
    }
}

// 干扰合约 2: 复杂数学库 (数据流干扰)
contract ComplexMath {
    // 纯计算，无状态修改
    function heavyCompute(uint256 a) external pure returns (uint256) {
        return a * a + 0xDEADBEEF;
    }
}

// 主合约
contract Vault {
    uint256 public totalAssets; // 🎯 我们的切片目标变量
    
    AuditLogger public logger;
    ComplexMath public mathLib;
    address public owner;

    constructor(address _logger, address _math) {
        logger = AuditLogger(_logger);
        mathLib = ComplexMath(_math);
        owner = msg.sender;
    }

    // === 场景 A: 外部调用干扰 ===
    // 静态分析：因为调用了 logger.logAccess，属于控制流依赖，通常会保留整个 Logger 合约。
    // LLM 分析：语义理解 logAccess 只是 "emit event"，不影响 totalAssets，直接剪枝。
    function deposit(uint256 amount) external {
        logger.logAccess(msg.sender); // <--- 干扰点
        totalAssets += amount;
    }

    // === 场景 B: 数据流僵尸代码 ===
    // 静态分析：tempVar 来源于输入，且经过了 mathLib 计算，数据流图 (PDG) 存在依赖。
    // LLM 分析：tempVar 虽然被计算，但最终只用于 require(true) 或无意义判断，未流入 totalAssets。
    function withdraw(uint256 amount) external {
        uint256 tempVar = mathLib.heavyCompute(amount); // <--- 干扰点
        
        // 一个在语义上无效的检查 (恒真条件)，静态工具很难判定 ComplexMath 的返回值范围
        require(tempVar >= 0, "Math error"); 

        require(msg.sender == owner, "Auth");
        totalAssets -= amount;
    }

    // === 场景 C: 语义无关的状态修改 ===
    // 静态分析：lastAccessTime 被修改了，且与 totalAssets 在同一个函数中，通常不区分变量粒度。
    // LLM 分析：明确区分 lastAccessTime 和 totalAssets 是两个独立的状态域。
    uint256 public lastAccessTime;
    function updateState() external {
        lastAccessTime = block.timestamp; // <--- 干扰点
        totalAssets = 100;
    }
}