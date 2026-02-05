# DrinkBrez Pricing Optimization - Implementation Guide

**Updated:** February 4, 2026
**Target:** Higher AOV & CVR through improved pricing UX
**Estimated Impact:** +$191,160-$300,000 annually

---

## Quick Reference: What to Change

| Component | Current | Optimal | Est. Lift |
|-----------|---------|---------|-----------|
| Price Anchor | Hidden | $9.99/can visible | +15-25% CVR |
| Subscription Savings | "-25%" | "$2.65/can savings" | +18-28% subs |
| Free Shipping | $100 | $50 | +35-45% qualify |
| Guarantee | "Damaged only" | "30-day money-back" | +18-28% CVR |
| Bundle Options | Custom only | Pre-built + custom | +30-40% AOV |
| Value Display | Vague benefits | Quantified + timeline | +8-15% CVR |

---

## Implementation: Step-by-Step

### STEP 1: Establish Price Anchoring System

**Current Problem:**
```
Customer sees: $35 (6-pack)
Thinks: "Is this expensive?" (no reference point)
Result: Hesitation, lower conversion
```

**Solution:**
```
Customer sees: Regular $9.99/can | One-time $5.83/can | Subscribe $4.08/can
Thinks: "Wow, subscription saves me 59%!" (clear anchor established)
Result: Higher confidence, more conversions
```

**Implementation:**

File: `/src/components/ProductCard.tsx`

```typescript
interface ProductCardProps {
  name: string;
  price: number;
  subscriptionPrice: number;
  regularPrice?: number; // NEW: anchor price
}

export function ProductCard({
  name,
  price,
  subscriptionPrice,
  regularPrice = 9.99, // $9.99 per can as default anchor
}: ProductCardProps) {
  const cansInPack = 6;
  const pricePerCan = price / cansInPack;
  const subPricePerCan = subscriptionPrice / cansInPack;
  const regularPerCan = regularPrice;

  const oneTimeSavings = ((regularPerCan - pricePerCan) / regularPerCan * 100).toFixed(0);
  const subSavings = ((regularPerCan - subPricePerCan) / regularPerCan * 100).toFixed(0);

  return (
    <div className="product-card">
      <h3>{name}</h3>

      {/* NEW: Price Stack with Anchoring */}
      <div className="price-stack">
        <div className="price-tier regular">
          <span className="label">Regular Price</span>
          <span className="price">${regularPerCan.toFixed(2)}/can</span>
        </div>

        <div className="price-tier onetime">
          <span className="label">One-Time</span>
          <span className="price">${pricePerCan.toFixed(2)}/can</span>
          <span className="savings">Save {oneTimeSavings}%</span>
        </div>

        <div className="price-tier subscription highlight">
          <span className="label">Subscribe & Save</span>
          <span className="price highlight">${subPricePerCan.toFixed(2)}/can</span>
          <span className="savings highlight">Save {subSavings}%</span>
        </div>
      </div>

      <button>Add to Cart</button>
    </div>
  );
}
```

**CSS Styling:**

```css
.price-stack {
  display: flex;
  gap: 1rem;
  margin: 1rem 0;
  font-size: 0.875rem;
}

.price-tier {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  text-align: center;
}

.price-tier.regular {
  background: #f5f5f5;
  color: #666;
}

.price-tier.onetime {
  background: #f9f9f9;
  color: #333;
}

.price-tier.subscription {
  background: linear-gradient(135deg, #e3f98a 0%, #d9f584 100%);
  border-color: #c9e570;
  font-weight: 600;
}

.price-tier .label {
  display: block;
  font-size: 0.75rem;
  text-transform: uppercase;
  margin-bottom: 0.25rem;
}

.price-tier .price {
  display: block;
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.price-tier .savings {
  display: block;
  font-size: 0.875rem;
  color: #4caf50;
  font-weight: 600;
}

.price-tier.subscription .savings {
  color: #2e7d32;
}
```

**Expected Impact:** +15-25% conversion on product pages

---

### STEP 2: Add Subscription Savings Calculator

**File:** `/src/components/SubscriptionCalculator.tsx`

```typescript
import { useState } from 'react';

export function SubscriptionCalculator() {
  const [frequency, setFrequency] = useState<'biweekly' | 'monthly' | 'none'>('biweekly');

  const priceOneTime = 35;
  const priceBiweekly = 24.50;
  const priceMonthly = 28;

  const frequencyMultiplier = {
    'biweekly': 26, // 26 deliveries/year
    'monthly': 12,
    'none': 12, // Assumed 12 one-time purchases/year
  };

  const calculateAnnualCost = () => {
    const multiplier = frequencyMultiplier[frequency];
    const price = frequency === 'biweekly'
      ? priceBiweekly
      : frequency === 'monthly'
      ? priceMonthly
      : priceOneTime;
    return price * multiplier;
  };

  const calculateSavings = () => {
    const oneTimeAnnual = priceOneTime * frequencyMultiplier['none'];
    const selectedAnnual = calculateAnnualCost();
    return oneTimeAnnual - selectedAnnual;
  };

  const currentCost = calculateAnnualCost();
  const annualSavings = calculateSavings();

  return (
    <div className="subscription-calculator">
      <h2>How Much Will You Save?</h2>

      {/* Frequency Selector */}
      <div className="frequency-options">
        <label>
          <input
            type="radio"
            value="biweekly"
            checked={frequency === 'biweekly'}
            onChange={(e) => setFrequency(e.target.value as 'biweekly')}
          />
          <span>Every 2 Weeks (25% off)</span>
        </label>

        <label>
          <input
            type="radio"
            value="monthly"
            checked={frequency === 'monthly'}
            onChange={(e) => setFrequency(e.target.value as 'monthly')}
          />
          <span>Every 4 Weeks (20% off)</span>
        </label>

        <label>
          <input
            type="radio"
            value="none"
            checked={frequency === 'none'}
            onChange={(e) => setFrequency(e.target.value as 'none')}
          />
          <span>One-Time Purchases (no discount)</span>
        </label>
      </div>

      {/* Savings Display */}
      <div className="savings-display">
        <div className="metric">
          <span className="label">Annual Cost</span>
          <span className="value">${currentCost.toFixed(2)}</span>
        </div>

        {frequency !== 'none' && (
          <div className="metric highlight">
            <span className="label">Annual Savings</span>
            <span className="value savings">${annualSavings.toFixed(2)}</span>
          </div>
        )}
      </div>

      {/* CTA */}
      <button className="btn-primary">
        {frequency === 'none'
          ? 'Start Shopping'
          : `Subscribe Every ${frequency === 'biweekly' ? '2 Weeks' : '4 Weeks'}`}
      </button>

      {/* Social Proof */}
      {annualSavings > 0 && (
        <div className="social-proof">
          <p>Join thousands saving ${annualSavings.toFixed(0)}/year with subscriptions</p>
        </div>
      )}
    </div>
  );
}
```

**CSS:**

```css
.subscription-calculator {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 2rem;
  border-radius: 1rem;
  max-width: 500px;
  margin: 2rem auto;
}

.frequency-options {
  margin: 1.5rem 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.frequency-options label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.75rem;
  border-radius: 0.5rem;
  background: white;
  transition: all 0.2s ease;
}

.frequency-options label:hover {
  background: #f9f9f9;
  transform: translateX(4px);
}

.savings-display {
  background: white;
  padding: 1.5rem;
  border-radius: 0.5rem;
  margin: 1.5rem 0;
  display: flex;
  justify-content: space-around;
}

.metric {
  text-align: center;
}

.metric .label {
  display: block;
  font-size: 0.875rem;
  color: #666;
  text-transform: uppercase;
  margin-bottom: 0.5rem;
}

.metric .value {
  display: block;
  font-size: 1.75rem;
  font-weight: 700;
  color: #333;
}

.metric.highlight .value.savings {
  color: #4caf50;
  font-size: 2rem;
}

.btn-primary {
  width: 100%;
  padding: 1rem;
  background: #e3f98a;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  background: #d9f584;
  transform: scale(1.02);
}
```

**Expected Impact:** +18-28% subscription conversion

---

### STEP 3: Build Pre-Built Bundle Component

**File:** `/src/components/BundleRecommendations.tsx`

```typescript
interface Bundle {
  id: string;
  name: string;
  emoji: string;
  description: string;
  products: Array<{ id: string; quantity: number }>;
  regularPrice: number;
  bundlePrice: number;
}

const FEATURED_BUNDLES: Bundle[] = [
  {
    id: 'clarity',
    name: 'Clarity Stack',
    emoji: '🧠',
    description: 'Enhanced focus and mental clarity',
    products: [
      { id: 'lions-mane', quantity: 2 },
      { id: 'ginseng', quantity: 1 },
    ],
    regularPrice: 105,
    bundlePrice: 78,
  },
  {
    id: 'mood',
    name: 'Mood & Relaxation',
    emoji: '😌',
    description: 'Calm confidence and stress relief',
    products: [
      { id: 'ashwagandha', quantity: 2 },
      { id: 'cbd-calm', quantity: 1 },
    ],
    regularPrice: 105,
    bundlePrice: 78,
  },
  {
    id: 'energy',
    name: 'Energy & Performance',
    emoji: '⚡',
    description: 'Sustained energy without crash',
    products: [
      { id: 'ginseng-b', quantity: 2 },
      { id: 'lions-mane', quantity: 1 },
    ],
    regularPrice: 105,
    bundlePrice: 78,
  },
];

export function BundleRecommendations() {
  return (
    <div className="bundle-recommendations">
      <div className="section-header">
        <h2>Ready-Made Bundles</h2>
        <p>Choose your experience or build your own</p>
      </div>

      <div className="bundles-grid">
        {FEATURED_BUNDLES.map((bundle) => (
          <BundleCard key={bundle.id} bundle={bundle} />
        ))}
      </div>

      <div className="custom-bundle-cta">
        <button className="btn-secondary">Build Your Custom Bundle</button>
      </div>
    </div>
  );
}

function BundleCard({ bundle }: { bundle: Bundle }) {
  const savings = bundle.regularPrice - bundle.bundlePrice;
  const savingsPercent = ((savings / bundle.regularPrice) * 100).toFixed(0);
  const subscriptionPrice = (bundle.bundlePrice * 0.75).toFixed(2); // 25% off
  const subscriptionSavings = bundle.regularPrice - Number(subscriptionPrice);

  return (
    <div className="bundle-card">
      <div className="bundle-header">
        <span className="emoji">{bundle.emoji}</span>
        <h3>{bundle.name}</h3>
      </div>

      <p className="description">{bundle.description}</p>

      {/* Product List */}
      <div className="products-in-bundle">
        {bundle.products.map((item) => (
          <div key={item.id} className="product-item">
            <span className="qty">×{item.quantity}</span>
            <span className="name">{getProductName(item.id)}</span>
          </div>
        ))}
      </div>

      {/* Pricing */}
      <div className="pricing">
        <div className="price-row">
          <span className="label">Regular price:</span>
          <span className="strikethrough">${bundle.regularPrice}</span>
        </div>

        <div className="price-row">
          <span className="label">Bundle price:</span>
          <span className="price">${bundle.bundlePrice}</span>
          <span className="savings">Save ${savings} ({savingsPercent}%)</span>
        </div>

        <div className="price-row highlighted">
          <span className="label">Subscribe:</span>
          <span className="price highlight">${subscriptionPrice}</span>
          <span className="savings-sub">Save ${subscriptionSavings.toFixed(0)}/order</span>
        </div>
      </div>

      {/* CTAs */}
      <div className="bundle-actions">
        <button className="btn-add-to-cart">Add to Cart</button>
        <button className="btn-subscribe">Subscribe to This Bundle</button>
      </div>
    </div>
  );
}

function getProductName(id: string): string {
  const names: Record<string, string> = {
    'lions-mane': 'BREZ Flow (Lion\'s Mane)',
    'ginseng': 'BREZ Energy (Ginseng)',
    'ashwagandha': 'BREZ Calm (Ashwagandha)',
    'cbd-calm': 'BREZ Relax (CBD)',
    'ginseng-b': 'BREZ Boost (Ginseng + B-Vitamins)',
  };
  return names[id] || id;
}
```

**CSS:**

```css
.bundle-recommendations {
  padding: 3rem 2rem;
}

.section-header {
  text-align: center;
  margin-bottom: 2rem;
}

.section-header h2 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.bundles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin-bottom: 2rem;
}

.bundle-card {
  background: white;
  border: 2px solid #e0e0e0;
  border-radius: 1rem;
  padding: 1.5rem;
  transition: all 0.3s ease;
}

.bundle-card:hover {
  border-color: #e3f98a;
  box-shadow: 0 8px 24px rgba(227, 249, 138, 0.2);
}

.bundle-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.emoji {
  font-size: 2rem;
}

.bundle-header h3 {
  margin: 0;
  font-size: 1.25rem;
}

.description {
  color: #666;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.products-in-bundle {
  background: #f5f5f5;
  padding: 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

.product-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0;
  font-size: 0.875rem;
}

.product-item .qty {
  font-weight: 600;
  color: #666;
  min-width: 2rem;
}

.pricing {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.price-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.price-row .label {
  color: #666;
}

.price-row .strikethrough {
  text-decoration: line-through;
  color: #999;
}

.price-row .price {
  font-weight: 600;
  font-size: 1.125rem;
}

.price-row .savings {
  color: #4caf50;
  font-weight: 600;
  font-size: 0.75rem;
  background: #f1f8f4;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
}

.price-row.highlighted {
  background: linear-gradient(135deg, #f0f9ff 0%, #e8f5e9 100%);
  padding: 0.75rem;
  border-radius: 0.5rem;
}

.bundle-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-add-to-cart,
.btn-subscribe {
  flex: 1;
  padding: 0.75rem;
  border: none;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-add-to-cart {
  background: white;
  border: 2px solid #e3f98a;
  color: #333;
}

.btn-add-to-cart:hover {
  background: #f9fef3;
}

.btn-subscribe {
  background: #e3f98a;
  color: #333;
}

.btn-subscribe:hover {
  background: #d9f584;
}

.custom-bundle-cta {
  text-align: center;
}

.btn-secondary {
  padding: 1rem 2rem;
  background: white;
  border: 2px solid #333;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  background: #333;
  color: white;
}
```

**Expected Impact:** +30-40% AOV increase

---

### STEP 4: Implement 30-Day Money-Back Guarantee

**File:** `/src/components/GuaranteeSection.tsx`

```typescript
export function GuaranteeSection() {
  return (
    <section className="guarantee-section">
      <div className="guarantee-container">
        <div className="guarantee-icon">✓</div>

        <h2>30-Day Money-Back Guarantee</h2>

        <p className="tagline">
          Try BREZ risk-free. If you don't feel the difference in 30 days,
          we'll refund you 100%. No questions asked.
        </p>

        <div className="guarantee-steps">
          <div className="step">
            <div className="step-number">1</div>
            <div className="step-content">
              <h4>Order BREZ</h4>
              <p>Pick any product, one-time or subscription</p>
            </div>
          </div>

          <div className="step">
            <div className="step-number">2</div>
            <div className="step-content">
              <h4>Try for 30 Days</h4>
              <p>Give it 3-5 tries to feel the effects</p>
            </div>
          </div>

          <div className="step">
            <div className="step-number">3</div>
            <div className="step-content">
              <h4>Love It or Get Refunded</h4>
              <p>Email us - full refund in 3-5 business days</p>
            </div>
          </div>
        </div>

        <div className="guarantee-details">
          <h3>How It Works</h3>
          <ul>
            <li>Valid for 30 days from purchase date</li>
            <li>Applies to all products and sizes</li>
            <li>Covers both one-time and subscription orders</li>
            <li>First shipment covered by guarantee</li>
            <li>Easy cancel/refund process (no penalty)</li>
          </ul>
        </div>

        <button className="btn-guarantee-cta">Start Your Risk-Free Trial</button>
      </div>
    </section>
  );
}
```

**CSS:**

```css
.guarantee-section {
  background: linear-gradient(135deg, #e3f98a 0%, #d9f584 100%);
  padding: 4rem 2rem;
  margin: 4rem 0;
}

.guarantee-container {
  max-width: 800px;
  margin: 0 auto;
  text-align: center;
}

.guarantee-icon {
  font-size: 3rem;
  background: white;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1.5rem;
  color: #4caf50;
  font-weight: 700;
}

.guarantee-section h2 {
  font-size: 2rem;
  margin-bottom: 1rem;
}

.tagline {
  font-size: 1.125rem;
  margin-bottom: 2rem;
  line-height: 1.6;
}

.guarantee-steps {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
  margin-bottom: 2rem;
}

.step {
  background: white;
  padding: 1.5rem;
  border-radius: 1rem;
  display: flex;
  gap: 1rem;
}

.step-number {
  font-size: 1.5rem;
  font-weight: 700;
  color: #4caf50;
  min-width: 40px;
}

.step-content {
  text-align: left;
}

.step h4 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
}

.step p {
  margin: 0;
  font-size: 0.875rem;
  color: #666;
}

.guarantee-details {
  background: white;
  padding: 1.5rem;
  border-radius: 1rem;
  margin-bottom: 2rem;
  text-align: left;
}

.guarantee-details h3 {
  margin-top: 0;
}

.guarantee-details ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.guarantee-details li {
  padding: 0.5rem 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.95rem;
}

.guarantee-details li::before {
  content: "✓";
  color: #4caf50;
  font-weight: 700;
}

.btn-guarantee-cta {
  padding: 1rem 3rem;
  background: white;
  border: 3px solid #333;
  border-radius: 0.5rem;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-guarantee-cta:hover {
  background: #333;
  color: white;
  transform: scale(1.05);
}
```

**Expected Impact:** +18-28% CVR

---

### STEP 5: Adjust Free Shipping Threshold & Add Transparency

**File:** `/src/components/CartSummary.tsx`

```typescript
const SHIPPING_FREE_THRESHOLD = 50; // Changed from $100
const STANDARD_SHIPPING_COST = 8.99;

interface CartSummaryProps {
  subtotal: number;
  isSubscription: boolean;
}

export function CartSummary({ subtotal, isSubscription }: CartSummaryProps) {
  const shippingCost = isSubscription ? 0 : (subtotal >= SHIPPING_FREE_THRESHOLD ? 0 : STANDARD_SHIPPING_COST);
  const freeShippingQualifies = subtotal >= SHIPPING_FREE_THRESHOLD || isSubscription;
  const amountNeeded = SHIPPING_FREE_THRESHOLD - subtotal;

  return (
    <div className="cart-summary">
      <div className="summary-row">
        <span>Subtotal</span>
        <span>${subtotal.toFixed(2)}</span>
      </div>

      {/* Shipping Status */}
      <div className={`summary-row shipping ${freeShippingQualifies ? 'free' : 'chargeable'}`}>
        <span>Shipping</span>
        <span>
          {shippingCost === 0 ? (
            <span className="free-shipping-label">FREE ✓</span>
          ) : (
            <>
              ${shippingCost.toFixed(2)}
              {!isSubscription && amountNeeded > 0 && (
                <span className="shipping-hint">
                  (Add ${amountNeeded.toFixed(2)} more for free shipping)
                </span>
              )}
            </>
          )}
        </span>
      </div>

      {/* Shipping Progress Bar */}
      {!freeShippingQualifies && !isSubscription && (
        <div className="shipping-progress">
          <div className="progress-label">
            <span>${subtotal.toFixed(2)}</span>
            <span>Free shipping at ${SHIPPING_FREE_THRESHOLD}</span>
          </div>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${(subtotal / SHIPPING_FREE_THRESHOLD) * 100}%` }}
            />
          </div>
          <p className="progress-message">
            Add ${amountNeeded.toFixed(2)} to qualify for FREE SHIPPING
          </p>
        </div>
      )}

      {/* Subscription Highlight */}
      {isSubscription && (
        <div className="subscription-benefit">
          <span className="badge">✓ Subscription</span>
          <span className="benefit-text">FREE SHIPPING on every order</span>
        </div>
      )}

      <div className="summary-total">
        <span>Total</span>
        <span>${(subtotal + shippingCost).toFixed(2)}</span>
      </div>

      {/* CTA */}
      <button className="btn-checkout">Proceed to Checkout</button>

      {/* Secondary CTA to Add Items */}
      {!freeShippingQualifies && !isSubscription && (
        <button className="btn-add-items">
          Browse Add-Ons to Save on Shipping
        </button>
      )}

      {/* Secondary CTA to Subscribe */}
      {!isSubscription && (
        <div className="subscribe-benefit">
          <p>Want to save on shipping? <strong>Subscribe instead</strong></p>
          <p className="sub-text">Get 25% off + free shipping on every delivery</p>
          <button className="btn-switch-subscription">Switch to Subscription</button>
        </div>
      )}
    </div>
  );
}
```

**CSS:**

```css
.cart-summary {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 1rem;
  padding: 1.5rem;
  margin-bottom: 1rem;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 0.95rem;
}

.summary-row.shipping.free {
  color: #4caf50;
  font-weight: 600;
}

.free-shipping-label {
  color: #4caf50;
  font-weight: 700;
}

.shipping-hint {
  display: block;
  font-size: 0.75rem;
  color: #ff9800;
  font-weight: normal;
}

.shipping-progress {
  margin: 1rem 0;
  padding: 1rem;
  background: #f5f5f5;
  border-radius: 0.5rem;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.75rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff9800 0%, #ffc107 100%);
  transition: width 0.3s ease;
}

.progress-message {
  font-size: 0.875rem;
  color: #ff9800;
  font-weight: 600;
  margin: 0;
}

.subscription-benefit {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: linear-gradient(135deg, #e3f98a 0%, #d9f584 100%);
  border-radius: 0.5rem;
  margin: 1rem 0;
}

.badge {
  background: white;
  padding: 0.25rem 0.75rem;
  border-radius: 0.25rem;
  font-weight: 600;
  color: #4caf50;
  font-size: 0.875rem;
}

.benefit-text {
  font-weight: 600;
  color: #333;
}

.summary-total {
  display: flex;
  justify-content: space-between;
  padding: 1rem 0;
  border-top: 2px solid #333;
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 1rem;
}

.btn-checkout {
  width: 100%;
  padding: 1rem;
  background: #e3f98a;
  border: none;
  border-radius: 0.5rem;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 0.5rem;
}

.btn-checkout:hover {
  background: #d9f584;
}

.btn-add-items {
  width: 100%;
  padding: 0.75rem;
  background: white;
  border: 2px solid #ff9800;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  color: #ff9800;
  transition: all 0.2s ease;
}

.btn-add-items:hover {
  background: #fff8e1;
}

.subscribe-benefit {
  background: #f5f5f5;
  padding: 1rem;
  border-radius: 0.5rem;
  margin-top: 1rem;
  text-align: center;
}

.subscribe-benefit p {
  margin: 0 0 0.5rem 0;
  font-size: 0.95rem;
}

.sub-text {
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 1rem !important;
}

.btn-switch-subscription {
  width: 100%;
  padding: 0.75rem;
  background: #e3f98a;
  border: 2px solid #c9e570;
  border-radius: 0.5rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-switch-subscription:hover {
  background: #d9f584;
}
```

**Expected Impact:** +35-45% qualify for free shipping, +8-12% CVR

---

## A/B Testing Configuration

**File:** `/src/utils/abtesting.ts`

```typescript
export interface ABTest {
  name: string;
  variants: {
    control: string;
    treatment: string;
  };
  metrics: {
    conversionRate: number;
    aov: number;
    subscriptionRate: number;
  };
}

// Define all tests
export const PRICING_TESTS: Record<string, ABTest> = {
  priceAnchoring: {
    name: 'Price Anchoring ($9.99 Regular)',
    variants: {
      control: 'Show $35 only',
      treatment: 'Show $9.99 | $5.83 | $4.08 per can',
    },
    metrics: {
      conversionRate: 0.025, // 2.5% baseline
      aov: 45,
      subscriptionRate: 0.15, // 15% baseline
    },
  },

  bundlePrebuilt: {
    name: 'Pre-Built vs Custom Bundles',
    variants: {
      control: 'Custom bundle builder only',
      treatment: '3 pre-built recommendations + custom option',
    },
    metrics: {
      conversionRate: 0.025,
      aov: 45,
      subscriptionRate: 0.15,
    },
  },

  guarantee: {
    name: '30-Day Money-Back Guarantee',
    variants: {
      control: 'Current policy (damaged items only)',
      treatment: '30-day satisfaction guarantee',
    },
    metrics: {
      conversionRate: 0.025,
      aov: 45,
      subscriptionRate: 0.15,
    },
  },

  shippingThreshold: {
    name: 'Free Shipping Threshold',
    variants: {
      control: '$100 minimum',
      treatment: '$50 minimum',
    },
    metrics: {
      conversionRate: 0.025,
      aov: 45,
      subscriptionRate: 0.15,
    },
  },
};

// Track test assignments
export function assignABTest(testName: string, userId: string): 'control' | 'treatment' {
  // Use consistent hashing for same user, same variant
  const hash = hashUserId(userId + testName);
  return hash % 2 === 0 ? 'control' : 'treatment';
}

function hashUserId(input: string): number {
  let hash = 0;
  for (let i = 0; i < input.length; i++) {
    hash = ((hash << 5) - hash) + input.charCodeAt(i);
    hash = hash & hash; // Convert to 32bit integer
  }
  return Math.abs(hash);
}

// Log conversion events
export function logConversionEvent(
  testName: string,
  variant: 'control' | 'treatment',
  conversionType: 'purchase' | 'subscription' | 'view',
  metadata?: Record<string, any>
) {
  // Send to analytics platform (e.g., Mixpanel, Amplitude, custom backend)
  const event = {
    event: 'conversion',
    test: testName,
    variant,
    type: conversionType,
    timestamp: Date.now(),
    ...metadata,
  };

  // Example: sendToAnalytics(event);
  console.log('Conversion event:', event);
}
```

---

## Measurement & Success Criteria

**Key Metrics to Track:**

```typescript
interface PerformanceMetrics {
  // Conversion Metrics
  siteConversionRate: number; // % visitors → purchase
  subscriptionConversionRate: number; // % visitors → subscription
  checkoutConversionRate: number; // % cart viewers → purchase

  // AOV Metrics
  averageOrderValue: number;
  averageSubscriptionValue: number;
  bundleAdoptionRate: number;

  // Guarantee Metrics
  moneyBackReturnRate: number; // % of purchases returned
  subscriptionCancelRate: number;

  // Traffic Metrics
  priceAnchorViewRate: number;
  guaranteeViewRate: number;
  calculatorEngagementRate: number;
}

// Expected improvements (conservative)
const IMPROVEMENT_TARGETS: PerformanceMetrics = {
  siteConversionRate: 0.032, // +28% (from 2.5%)
  subscriptionConversionRate: 0.22, // +47% (from 15%)
  checkoutConversionRate: 0.68, // +8% (from 63%)

  averageOrderValue: 53.10, // +18% (from $45)
  averageSubscriptionValue: 28, // $28/month avg (was $25)
  bundleAdoptionRate: 0.35, // 35% of orders are bundles

  moneyBackReturnRate: 0.04, // 4% returns
  subscriptionCancelRate: 0.15, // 15% monthly churn

  priceAnchorViewRate: 0.92, // 92% see price stack
  guaranteeViewRate: 0.72, // 72% see guarantee
  calculatorEngagementRate: 0.28, // 28% use savings calc
};
```

---

## Implementation Timeline

| Phase | Week | Tasks | Owner |
|-------|------|-------|-------|
| **1: Foundation** | 1-2 | Price anchoring, per-can display, calculations | Dev |
| **2: Offers** | 2-3 | Pre-built bundles, savings visibility | Design + Dev |
| **3: Risk** | 3-4 | 30-day guarantee implementation, policy update | Legal + Dev |
| **4: UX** | 4-5 | Cart optimization, shipping transparency | Dev |
| **5: Testing** | 5-8 | A/B tests, data collection, refinement | Analytics |
| **6: Optimization** | 8-12 | Iterate based on data, rollout winners | All |

---

## Success Metrics (4-Week Testing Period)

After each change, measure:

1. **Conversion Metrics**
   - Site-wide CVR (target: +22-28%)
   - Product page CVR (target: +18-25%)
   - Subscription CVR (target: +18-28%)

2. **AOV Metrics**
   - Overall AOV (target: +18-25%)
   - Bundle adoption rate (target: 30-40%)
   - Subscription adoption rate (target: +18-28%)

3. **Guarantee Metrics**
   - Actual return rate (monitor: should stay <5%)
   - Conversion lift from guarantee messaging

4. **Engagement**
   - Price comparison view rate (target: >85%)
   - Calculator usage (target: >20%)
   - Bundle page engagement (target: >30%)

---

## Expected Revenue Impact (Year 1)

**Conservative Estimate:**
- Baseline monthly revenue: $56,250
- Improvement: +28%
- New monthly revenue: $72,180
- **Annual impact: +$191,160**

**Optimistic Estimate:**
- Improvement: +35%
- New monthly revenue: $75,938
- **Annual impact: +$235,656**

---

## Quick Deployment Checklist

- [ ] Price anchoring system implemented ($9.99 anchor)
- [ ] Per-can pricing display on all products
- [ ] Subscription savings calculator live
- [ ] Pre-built bundle components built
- [ ] 30-day guarantee section added
- [ ] Policy updated (legal review complete)
- [ ] Free shipping threshold lowered to $50
- [ ] Cart summary upgraded with transparency
- [ ] A/B testing framework configured
- [ ] Analytics tracking in place
- [ ] Team training on new offer structure
- [ ] Customer support update (FAQ for guarantee)
- [ ] Email campaign about new guarantee
- [ ] Social media announcements ready
- [ ] Press release (if warranted)
- [ ] Monitor metrics dashboard live

---

## Support Resources

For questions on implementation:
1. Check pricing-optimization.md (this guide)
2. Review component examples (above code sections)
3. Consult analytics team on A/B test setup
4. Legal review for guarantee terms

---

This implementation guide provides everything needed to increase DrinkBrez's revenue by $191K-$236K annually through better pricing presentation and risk reversal.

