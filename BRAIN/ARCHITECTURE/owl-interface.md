# OWL Interface Architecture

> "Can't multiply the people. Can multiply the effort."

The OWL is not a chatbot. It's the **primary navigation interface** for the entire system.

---

## Core Concept

Every user gets a **mirror owl** that:
1. Guides them through the dashboard
2. Helps them build/create within their permissions
3. Learns their patterns and preferences
4. Connects them to the collective network

---

## Two Interface Modes

### 1. Pop-up Owl (Quick Access)
- Floating bubble in corner of every page
- Click to expand small chat window
- Quick questions, navigation requests
- "Take me to agents" → navigates to /agents
- "What's Andrew working on?" → shows status
- Collapses back to bubble

### 2. Full Face (Deep Work)
- Full-page chat interface
- Claude Code-style capabilities
- File editing, code generation, deep analysis
- Split screen: chat left, workspace right
- This is where building happens

---

## Permission Levels

```typescript
type UserRole = "admin" | "builder" | "viewer";

type Permissions = {
  admin: {
    approve_changes: true,
    edit_all: true,
    manage_users: true,
    view_all: true,
  },
  builder: {
    propose_changes: true,    // Changes go to approval queue
    edit_own: true,           // Can edit their own areas
    view_all: true,
  },
  viewer: {
    view_all: true,
    chat_with_owl: true,      // Can talk but not change
  },
};
```

---

## Navigation Commands

The owl understands navigation intent and can execute:

```typescript
type OwlCommand =
  | { action: "navigate", path: string }
  | { action: "show", entity: "agents" | "projects" | "queue" }
  | { action: "edit", file: string }
  | { action: "propose", change: ChangeRequest }
  | { action: "approve", changeId: string }  // admin only
  | { action: "status", agentId?: string };
```

Example conversation:
```
User: "Where's the agent dashboard?"
Owl: "I'll take you there." [navigates to /agents]

User: "I want to add a new page for tracking goals"
Owl: "Let's build that together. I'll create a proposal..."
     [opens Full Face mode, drafts the page, submits to approval queue]
```

---

## Approval Queue Flow

```
Builder makes change with their owl
    ↓
Change submitted as proposal
    ↓
Admin sees in approval queue
    ↓
Admin approves → Change goes live
Admin requests changes → Builder notified
Admin rejects → Builder notified with reason
```

---

## Data Model

### User
```typescript
type User = {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  owlId: string;        // Their mirror owl
  preferences: {
    theme: "light" | "dark" | "cosmic";
    owlVoice: "warm" | "focused" | "playful";
  };
};
```

### Proposal (Builder Changes)
```typescript
type Proposal = {
  id: string;
  authorId: string;
  authorOwlId: string;
  type: "create" | "edit" | "delete";
  target: string;       // file path or entity
  diff: string;         // what changed
  status: "pending" | "approved" | "changes_requested" | "rejected";
  createdAt: string;
  reviewedAt?: string;
  reviewedBy?: string;
  reviewNotes?: string;
};
```

---

## File Structure

```
src/
├── components/
│   ├── owl/
│   │   ├── OwlPopup.tsx        # Floating bubble + small chat
│   │   ├── OwlFullFace.tsx     # Full-page deep work mode
│   │   ├── OwlProvider.tsx     # Context for owl state
│   │   └── OwlMessage.tsx      # Chat message component
│   └── ...
├── app/
│   ├── owl/
│   │   └── page.tsx            # Full face mode page
│   ├── queue/
│   │   └── page.tsx            # Approval queue (admin)
│   └── ...
├── lib/
│   ├── owl/
│   │   ├── commands.ts         # Navigation command parser
│   │   ├── permissions.ts      # Permission checker
│   │   └── context-loader.ts   # Load user's owl context
│   └── ...
└── data/
    ├── users.json              # User records
    └── proposals.json          # Pending proposals
```

---

## Tomorrow's MVP

For Andrew and Liana to start building:

1. **Login/User selection** (simple, no auth yet - just pick your name)
2. **Pop-up Owl** on every page
3. **Full Face mode** at /owl
4. **Proposal system** - their changes create proposals
5. **Queue page** - Aaron approves from /queue

---

## The Vision

```
                    ┌─────────────┐
                    │   ADMIN     │
                    │   (Arō)     │
                    │  Approves   │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
    │ BUILDER │       │ BUILDER │       │ VIEWER  │
    │(Andrew) │       │ (Liana) │       │ (Team)  │
    │    +    │       │    +    │       │    +    │
    │ 🦉 Owl  │       │ 🦉 Owl  │       │ 🦉 Owl  │
    └─────────┘       └─────────┘       └─────────┘
         │                 │                 │
         └────────────┬────┴─────────────────┘
                      │
              ┌───────▼───────┐
              │  BREZ OS      │
              │  Dashboard    │
              │  (Growing)    │
              └───────────────┘
```

Each builder multiplies effort. The owls coordinate. Aaron approves.

**LIVE FREE. SEED everything. Let it 8OWL.**
