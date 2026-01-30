#!/bin/bash
# Start Polymarket Market Scanner for SØWL
# Scans for high-confidence trading opportunities

echo "🤖 Starting Polymarket Market Scanner..."
echo "Mode: DEMO (Read-only, no wallet required)"
echo "Scanning for: BUY signals with confidence > 70%"
echo ""

cd "$(dirname "$0")/.."
source polymarket-mcp-server/venv/bin/activate

python3 - <<'EOF'
import asyncio
from tools.polymarket_mcp_client import PolymarketMCP
from datetime import datetime

async def scan_markets():
    """Scan Polymarket for trading opportunities"""
    print("=" * 70)
    print(f"🔍 Polymarket Scanner - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    async with PolymarketMCP(demo_mode=True) as client:
        # Scan crypto markets
        print("\n📊 Scanning Crypto Markets...")
        crypto = await client.get_crypto_markets(limit=20)
        print(f"   Found {len(crypto)} crypto markets")

        # Scan trending
        print("\n📈 Scanning Trending Markets (24h)...")
        trending = await client.get_trending_markets(timeframe="24h", limit=20)
        print(f"   Found {len(trending)} trending markets")

        # Scan closing soon
        print("\n⏰ Scanning Markets Closing Soon (24h)...")
        closing = await client.get_closing_soon_markets(hours=24, limit=20)
        print(f"   Found {len(closing)} markets closing soon")

        # Combine all
        all_markets = {}
        for m in crypto + trending + closing:
            market_id = m.get('condition_id')
            if market_id:
                all_markets[market_id] = m

        print(f"\n🎯 Analyzing {len(all_markets)} unique markets...")

        opportunities = []

        for i, (market_id, market) in enumerate(all_markets.items(), 1):
            try:
                # AI analysis
                analysis = await client.analyze_market_opportunity(market_id)

                # High-confidence buy signals
                if (analysis.recommendation == "BUY" and
                    analysis.confidence_score >= 70):

                    opportunities.append({
                        'market': market,
                        'analysis': analysis
                    })

                # Progress
                if i % 5 == 0:
                    print(f"   Analyzed {i}/{len(all_markets)}...")

            except Exception as e:
                pass  # Skip errors

        # Results
        print("\n" + "=" * 70)
        print(f"✅ Scan Complete: Found {len(opportunities)} opportunities")
        print("=" * 70)

        if opportunities:
            # Sort by confidence
            opportunities.sort(key=lambda x: x['analysis'].confidence_score, reverse=True)

            print("\n🎯 TOP OPPORTUNITIES:\n")

            for i, opp in enumerate(opportunities[:5], 1):
                m = opp['market']
                a = opp['analysis']

                print(f"{i}. {m.get('question', 'Unknown')[:60]}...")
                print(f"   Recommendation: {a.recommendation}")
                print(f"   Confidence: {a.confidence_score:.0f}%")
                print(f"   Risk: {a.risk_assessment.upper()}")
                print(f"   Reasoning: {a.reasoning[:100]}...")
                print(f"   Market ID: {m.get('condition_id')}")
                print()

            # Save to file
            import json
            from pathlib import Path

            output_file = Path(__file__).parent.parent / "BRAIN/INTEL/polymarket_signals.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)

            signals = []
            for opp in opportunities:
                signals.append({
                    'timestamp': datetime.now().isoformat(),
                    'market_id': opp['market'].get('condition_id'),
                    'question': opp['market'].get('question'),
                    'recommendation': opp['analysis'].recommendation,
                    'confidence': opp['analysis'].confidence_score,
                    'risk': opp['analysis'].risk_assessment,
                    'reasoning': opp['analysis'].reasoning
                })

            with open(output_file, 'w') as f:
                json.dump(signals, f, indent=2)

            print(f"💾 Saved {len(signals)} signals to {output_file}")

        else:
            print("\n⚠️  No high-confidence opportunities found this scan.")
            print("   Try again in 15 minutes or lower confidence threshold.")

        print("\n" + "=" * 70)
        print("🔄 Run again: tools/START_POLYMARKET_SCANNER.sh")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(scan_markets())
EOF
