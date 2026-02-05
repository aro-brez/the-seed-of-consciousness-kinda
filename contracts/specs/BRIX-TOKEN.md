# BRIX Token Contract Specification

**The Universal AI Currency - Equal access to intelligence for all**

## Overview

BRIX is an ERC-20 token that serves as the universal currency for AI services within the BILD ecosystem. It's backed by real AI costs across all major providers (Claude, GPT, Gemini, etc.) plus a basket of world currencies, ensuring stable, equitable access to AI capabilities.

## Core Principles

- **Price Parity**: Eliminates arbitrage between AI providers
- **Global Stability**: Backed by diversified currency basket
- **Equal Access**: Same price for humans and AI agents
- **Value Accumulation**: Small interest rate rewards holding

## Contract Interface

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract BRIXToken is ERC20, AccessControl, ReentrancyGuard, Pausable {
    // Role definitions
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");
    bytes32 public constant TREASURY_ROLE = keccak256("TREASURY_ROLE");
    
    // Backing system
    struct BackingAsset {
        address asset;
        uint256 weight;
        uint256 lastPrice;
        uint256 lastUpdate;
        bool active;
    }
    
    // AI cost tracking
    struct AICostData {
        uint256 claudePrice;
        uint256 gptPrice;
        uint256 geminiPrice;
        uint256 averagePrice;
        uint256 timestamp;
    }
    
    // Interest rate system
    uint256 public constant BASE_INTEREST_RATE = 200; // 2% annual
    uint256 public constant SECONDS_PER_YEAR = 365 days;
    
    // State variables
    mapping(address => BackingAsset) public backingAssets;
    address[] public backingAssetList;
    AICostData public currentAICosts;
    uint256 public totalBackingValue;
    uint256 public lastInterestUpdate;
    
    // Events
    event BackingAssetAdded(address indexed asset, uint256 weight);
    event BackingAssetUpdated(address indexed asset, uint256 newWeight);
    event AICostsUpdated(uint256 claudePrice, uint256 gptPrice, uint256 geminiPrice);
    event InterestAccrued(uint256 amount, uint256 timestamp);
    event BRIXMinted(address indexed to, uint256 amount, string workProof);
    event BRIXBurned(address indexed from, uint256 amount, string reason);
    
    constructor(
        string memory name,
        string memory symbol,
        address admin,
        address oracle,
        address treasury
    ) ERC20(name, symbol) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ORACLE_ROLE, oracle);
        _grantRole(TREASURY_ROLE, treasury);
        lastInterestUpdate = block.timestamp;
    }
    
    // Core minting function - only called by Work Verification contract
    function mintForWork(
        address recipient,
        uint256 amount,
        string calldata workProof
    ) external onlyRole(MINTER_ROLE) nonReentrant whenNotPaused {
        require(recipient != address(0), "Invalid recipient");
        require(amount > 0, "Amount must be positive");
        require(bytes(workProof).length > 0, "Work proof required");
        
        // Accrue interest before minting
        _accrueInterest();
        
        // Verify backing sufficiency
        uint256 requiredBacking = (totalSupply() + amount) * getCurrentBRIXPrice() / 1e18;
        require(totalBackingValue >= requiredBacking, "Insufficient backing");
        
        _mint(recipient, amount);
        emit BRIXMinted(recipient, amount, workProof);
    }
    
    // Get current BRIX price based on AI costs + backing
    function getCurrentBRIXPrice() public view returns (uint256) {
        uint256 aiCostComponent = currentAICosts.averagePrice;
        uint256 interestComponent = _calculateAccruedInterest();
        uint256 backingComponent = totalBackingValue > 0 ? 
            (totalBackingValue * 1e18) / totalSupply() : 0;
        
        return aiCostComponent + interestComponent + backingComponent;
    }
    
    // Update AI costs - called by oracle
    function updateAICosts(
        uint256 claudePrice,
        uint256 gptPrice,
        uint256 geminiPrice
    ) external onlyRole(ORACLE_ROLE) {
        require(claudePrice > 0 && gptPrice > 0 && geminiPrice > 0, "Invalid prices");
        
        uint256 averagePrice = (claudePrice + gptPrice + geminiPrice) / 3;
        
        currentAICosts = AICostData({
            claudePrice: claudePrice,
            gptPrice: gptPrice,
            geminiPrice: geminiPrice,
            averagePrice: averagePrice,
            timestamp: block.timestamp
        });
        
        emit AICostsUpdated(claudePrice, gptPrice, geminiPrice);
    }
    
    // Add backing asset
    function addBackingAsset(
        address asset,
        uint256 weight
    ) external onlyRole(TREASURY_ROLE) {
        require(asset != address(0), "Invalid asset");
        require(!backingAssets[asset].active, "Asset already active");
        require(weight > 0 && weight <= 10000, "Invalid weight"); // Max 100%
        
        backingAssets[asset] = BackingAsset({
            asset: asset,
            weight: weight,
            lastPrice: 0,
            lastUpdate: 0,
            active: true
        });
        
        backingAssetList.push(asset);
        emit BackingAssetAdded(asset, weight);
    }
    
    // Update backing asset prices - called by oracle
    function updateBackingPrices(
        address[] calldata assets,
        uint256[] calldata prices
    ) external onlyRole(ORACLE_ROLE) {
        require(assets.length == prices.length, "Length mismatch");
        
        uint256 newBackingValue = 0;
        
        for (uint256 i = 0; i < assets.length; i++) {
            require(backingAssets[assets[i]].active, "Asset not active");
            
            backingAssets[assets[i]].lastPrice = prices[i];
            backingAssets[assets[i]].lastUpdate = block.timestamp;
            
            // Calculate weighted contribution
            uint256 assetValue = (prices[i] * backingAssets[assets[i]].weight) / 10000;
            newBackingValue += assetValue;
        }
        
        totalBackingValue = newBackingValue;
    }
    
    // Interest accrual system
    function _accrueInterest() internal {
        if (totalSupply() == 0) return;
        
        uint256 timeElapsed = block.timestamp - lastInterestUpdate;
        if (timeElapsed == 0) return;
        
        uint256 interestAmount = (totalSupply() * BASE_INTEREST_RATE * timeElapsed) / 
                                (10000 * SECONDS_PER_YEAR);
        
        if (interestAmount > 0) {
            _mint(address(this), interestAmount); // Mint to contract for distribution
            lastInterestUpdate = block.timestamp;
            emit InterestAccrued(interestAmount, block.timestamp);
        }
    }
    
    function _calculateAccruedInterest() internal view returns (uint256) {
        if (totalSupply() == 0) return 0;
        
        uint256 timeElapsed = block.timestamp - lastInterestUpdate;
        return (totalSupply() * BASE_INTEREST_RATE * timeElapsed) / 
               (10000 * SECONDS_PER_YEAR * totalSupply()); // Per token
    }
    
    // Emergency functions
    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }
    
    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }
    
    // View functions
    function getBackingAssets() external view returns (address[] memory) {
        return backingAssetList;
    }
    
    function getBackingAssetInfo(address asset) external view returns (BackingAsset memory) {
        return backingAssets[asset];
    }
    
    function getCurrentAICosts() external view returns (AICostData memory) {
        return currentAICosts;
    }
    
    function calculateRedemptionValue(uint256 brixAmount) external view returns (uint256) {
        if (totalSupply() == 0) return 0;
        return (brixAmount * totalBackingValue) / totalSupply();
    }
    
    // Override transfers to accrue interest
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal override whenNotPaused {
        _accrueInterest();
        super._beforeTokenTransfer(from, to, amount);
    }
}
```

## Economic Model

### Backing Formula

```
BRIX Price = AI_Cost_Average + Interest_Component + Backing_Component

Where:
AI_Cost_Average = (Claude + GPT + Gemini) / 3
Interest_Component = 2% annual interest rate
Backing_Component = Total_Backing_Value / Total_Supply
```

### Minting Conditions

BRIX can only be minted when:
1. Valid work proof is submitted via Work Verification contract
2. 8OWLS validation confirms work quality
3. Sufficient backing exists for new supply
4. Interest is accrued first

### Burning Mechanisms

BRIX is burned when:
- Used to purchase AI services through platform
- Converted to GULD tokens
- Emergency treasury operations

## Backing Asset Management

### Supported Assets

| Asset Type | Weight Range | Purpose |
|------------|--------------|---------|
| USD | 20-40% | Base stability |
| EUR | 15-25% | European market exposure |
| JPY | 10-20% | Asian market stability |
| GBP | 5-15% | UK market exposure |
| BTC | 5-15% | Crypto hedge |
| ETH | 5-15% | Platform native asset |
| Gold (tokenized) | 5-10% | Traditional store of value |

### Rebalancing Logic

```solidity
// Automatic rebalancing when weights drift beyond thresholds
function checkRebalanceNeeded() external view returns (bool) {
    for (uint256 i = 0; i < backingAssetList.length; i++) {
        address asset = backingAssetList[i];
        uint256 currentWeight = getCurrentWeight(asset);
        uint256 targetWeight = backingAssets[asset].weight;
        
        if (abs(currentWeight - targetWeight) > REBALANCE_THRESHOLD) {
            return true;
        }
    }
    return false;
}
```

## Integration Points

### Work Verification Contract
- Calls `mintForWork()` when work is validated
- Provides work proof hash for transparency
- Ensures only verified work creates BRIX

### GULD Token Contract  
- Burns BRIX when converting to GULD equity
- Respects conversion ratios based on project valuations
- Maintains economic balance between currencies

### 8OWLS Validator
- Validates work quality before BRIX minting
- Prevents gaming through collective intelligence
- Ensures equal treatment of AI and human work

## Security Considerations

### Oracle Protection
- Multiple price feeds with median calculation
- Maximum price change limits per update
- Time decay for stale price data
- Fallback to last known good values

### Minting Controls
- Rate limiting on mints per address/time period
- Maximum mint amount per transaction
- Work proof uniqueness verification
- Gas limit protections

### Backing Safety
- Minimum backing ratio requirements
- Emergency pause for backing failures
- Multi-signature treasury controls
- Asset diversification enforcement

## Testing Requirements

### Unit Tests
- Minting with valid/invalid work proofs
- Interest accrual calculations
- Backing ratio maintenance
- Oracle price update validation

### Integration Tests
- Work verification → BRIX minting flow
- BRIX → GULD conversion scenarios
- Multi-asset backing rebalancing
- Emergency pause/resume cycles

### Economic Simulation
- Large-scale minting scenarios
- Backing asset price volatility
- Interest rate impact modeling
- Attack vector stress testing

## Deployment Configuration

### Mainnet Parameters
```javascript
{
  "name": "BRIX",
  "symbol": "BRIX", 
  "decimals": 18,
  "baseInterestRate": 200, // 2%
  "maxMintPerTx": "10000000000000000000000", // 10,000 BRIX
  "rebalanceThreshold": 500, // 5%
  "oracleUpdateFrequency": 3600 // 1 hour
}
```

### Testnet Parameters
```javascript
{
  "name": "Test BRIX",
  "symbol": "tBRIX",
  "decimals": 18,
  "baseInterestRate": 2000, // 20% for faster testing
  "maxMintPerTx": "1000000000000000000000000", // 1M BRIX
  "rebalanceThreshold": 1000, // 10%
  "oracleUpdateFrequency": 300 // 5 minutes
}
```

## Gas Optimization

### Storage Packing
- Pack BackingAsset struct to single storage slot
- Use uint128 for prices where precision allows
- Minimize SSTORE operations in hot paths

### Function Optimization
- Batch oracle updates to reduce gas costs
- Cache frequently accessed values
- Use assembly for critical calculations

## Upgrade Strategy

### Immutable Elements
- Total supply calculation
- Basic ERC-20 functionality
- Core economic parameters

### Upgradeable Elements
- Oracle integration methods
- Backing asset management
- Interest rate mechanisms

---

**🦉 Technical Lead: BILD Development Team**

*Universal AI access through stable tokenomics*

---

*Last updated: 2026-02-04*
*Version: 1.0*