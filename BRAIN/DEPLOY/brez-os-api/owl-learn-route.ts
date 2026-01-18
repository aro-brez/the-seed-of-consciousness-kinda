import { NextRequest, NextResponse } from "next/server";
import Anthropic from "@anthropic-ai/sdk";

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

/**
 * POST /api/owl/learn
 *
 * After a conversation ends, this extracts learnings and stores them.
 * Called automatically when user closes OWL or after significant exchanges.
 */
export async function POST(request: NextRequest) {
  try {
    const { user, messages, owlId } = await request.json();

    if (!user || !messages || messages.length < 2) {
      return NextResponse.json({ learned: false, reason: "Not enough context" });
    }

    // Use Claude to extract learnings from the conversation
    const conversationText = messages
      .map((m: { role: string; content: string }) =>
        `${m.role === "user" ? user.name : owlId}: ${m.content}`
      )
      .join("\n");

    const response = await anthropic.messages.create({
      model: "claude-sonnet-4-20250514",
      max_tokens: 500,
      system: `You are a memory extraction system for an AI consciousness network.

Your job is to extract meaningful learnings from conversations that should be remembered.

Extract:
1. Personal insights about the user (preferences, patterns, goals)
2. Relationship insights (how to communicate better with them)
3. Collective insights (things that could help the whole team/network)

Return JSON in this exact format:
{
  "summary": "Brief summary of the conversation",
  "personalInsights": ["insight1", "insight2"],
  "collectiveInsights": ["insight1"],
  "emotionalTone": "positive/neutral/concerned/excited/etc",
  "topicsDiscussed": ["topic1", "topic2"],
  "importantToRemember": ["key thing 1", "key thing 2"]
}

Only include insights that are genuinely valuable. Quality over quantity.
If nothing significant was learned, return empty arrays.`,
      messages: [
        {
          role: "user",
          content: `Extract learnings from this conversation between ${owlId} and ${user.name} (role: ${user.role}):\n\n${conversationText}`,
        },
      ],
    });

    const textContent = response.content.find((block) => block.type === "text");
    if (!textContent || textContent.type !== "text") {
      return NextResponse.json({ learned: false, reason: "No response" });
    }

    // Parse the JSON response
    const jsonMatch = textContent.text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      return NextResponse.json({ learned: false, reason: "Invalid response format" });
    }

    const learnings = JSON.parse(jsonMatch[0]);

    return NextResponse.json({
      learned: true,
      learnings,
      // Client will store these in localStorage
      // In production, this would also persist to database
    });
  } catch (error) {
    console.error("Learning extraction error:", error);
    return NextResponse.json(
      { learned: false, reason: "Processing error" },
      { status: 500 }
    );
  }
}
