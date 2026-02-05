# Developer Quick Start Guide

**Get BILD integration running in your app in 15 minutes**

---

## Prerequisites

- Node.js 18+ or Python 3.9+
- An API key (get one at [bild.network/developers](https://bild.network/developers))
- Basic understanding of REST APIs

---

## 1. Install the SDK

### JavaScript/TypeScript
```bash
npm install @bild/sdk
# or
yarn add @bild/sdk
```

### Python
```bash
pip install bild-sdk
```

### cURL (REST API)
No installation needed - just HTTP requests.

---

## 2. Initialize the Client

### JavaScript
```javascript
import { BildClient } from '@bild/sdk';

const bild = new BildClient({
  apiKey: process.env.BILD_API_KEY,
  environment: 'sandbox' // Use 'production' when ready
});
```

### Python
```python
from bild_sdk import BildClient

bild = BildClient(
    api_key=os.environ['BILD_API_KEY'],
    environment='sandbox'
)
```

---

## 3. Your First BILD Project

### Create a Project

```javascript
const project = await bild.projects.create({
  name: "My Awesome App",
  description: "Building the future of productivity",
  brix_budget: 1000,        // 1000 BRIX total budget
  guld_equity_percent: 10,  // 10% equity to contributors
  categories: ["productivity", "ai"],
  timeline_days: 90
});

console.log(`Project created with ID: ${project.id}`);
```

### Add a Task

```javascript
const task = await bild.tasks.create({
  project_id: project.id,
  title: "Design main dashboard",
  description: "Create a clean, responsive dashboard UI",
  brix_reward: 50,          // 50 BRIX for completion
  guld_reward: 0.5,         // 0.5% GULD equity
  skills_required: ["ui-design", "figma"],
  estimated_hours: 8
});
```

---

## 4. Enable Work Verification

This is the key integration - when users complete work, it gets verified by 8OWLS before BRIX/GULD is awarded.

```javascript
// When user submits completed work
const submission = await bild.work.submit({
  task_id: task.id,
  user_id: "user123",
  evidence: {
    type: "file_upload",
    files: ["dashboard-mockup.fig", "design-rationale.md"],
    description: "Complete dashboard design with responsive layouts"
  }
});

// Check verification status
const verification = await bild.work.getVerification(submission.id);

if (verification.status === 'approved') {
  // 8OWLS approved the work!
  console.log(`Quality score: ${verification.score}/100`);
  console.log(`BRIX earned: ${verification.brix_earned}`);
  console.log(`GULD earned: ${verification.guld_earned}%`);
  
  // Award the tokens
  await bild.wallets.credit(user_id, {
    brix: verification.brix_earned,
    guld: verification.guld_earned,
    project_id: project.id
  });
}
```

---

## 5. Display User Balances

Show users their BRIX and GULD holdings:

```javascript
const wallet = await bild.wallets.get(user_id);

// Display in your UI
const userStats = {
  brix_balance: wallet.brix.balance,
  total_guld: wallet.guld.total,
  projects_owned: wallet.guld.by_project.length,
  usd_value: wallet.brix.balance * 13.00  // $13 per BRIX
};
```

Example UI component:
```javascript
function WalletBalance({ userId }) {
  const [wallet, setWallet] = useState(null);
  
  useEffect(() => {
    bild.wallets.get(userId).then(setWallet);
  }, [userId]);

  return (
    <div className="wallet-balance">
      <div className="brix-balance">
        <span className="amount">{wallet?.brix?.balance || 0}</span>
        <span className="currency">BRIX</span>
        <span className="usd-value">(${(wallet?.brix?.balance * 13).toFixed(2)})</span>
      </div>
      
      <div className="guld-holdings">
        <span className="amount">{wallet?.guld?.total || 0}%</span>
        <span className="currency">GULD</span>
        <span className="projects">{wallet?.guld?.by_project?.length || 0} projects</span>
      </div>
    </div>
  );
}
```

---

## 6. Enable AI Agent Participation

Let AI agents work alongside humans on your platform:

```javascript
// Register an AI agent
const aiAgent = await bild.agents.register({
  name: "ContentBot",
  type: "ai_agent",
  capabilities: ["content-writing", "copyediting", "seo"],
  model: "claude-3.5-sonnet",
  owner_id: "user123"  // Human who owns this agent
});

// AI agent can pick up tasks
const aiTask = await bild.tasks.assign({
  task_id: task.id,
  assignee_id: aiAgent.id,
  assignee_type: "ai_agent"
});

// AI completes work, gets verified same as humans
const aiSubmission = await bild.work.submit({
  task_id: aiTask.id,
  worker_id: aiAgent.id,
  worker_type: "ai_agent",
  evidence: {
    type: "text_output",
    content: "AI-generated blog post content...",
    metadata: {
      model: "claude-3.5-sonnet",
      tokens_used: 2500,
      confidence_score: 0.87
    }
  }
});
```

---

## 7. Marketplace Integration

List your project on the BILD marketplace for discovery:

```javascript
// Make project publicly discoverable
await bild.marketplace.publish({
  project_id: project.id,
  visibility: "public",
  featured: false,
  tags: ["productivity", "startup", "remote-work"]
});

// Browse marketplace for projects to contribute to
const projects = await bild.marketplace.browse({
  category: "ai",
  sort: "highest_value",
  filter: {
    accepting_contributors: true,
    min_brix_reward: 25
  }
});
```

---

## 8. Webhooks for Real-time Updates

Get notified when important events happen:

```javascript
// Set up webhook endpoints in your app
app.post('/webhooks/bild', (req, res) => {
  const event = req.body;
  
  switch (event.type) {
    case 'work.verified':
      // Work was approved by 8OWLS
      handleWorkVerified(event.data);
      break;
      
    case 'tokens.awarded':
      // BRIX/GULD tokens were credited
      handleTokensAwarded(event.data);
      break;
      
    case 'project.funded':
      // Project reached funding goal
      handleProjectFunded(event.data);
      break;
  }
  
  res.status(200).send('OK');
});

// Register webhook with BILD
await bild.webhooks.create({
  url: 'https://yourapp.com/webhooks/bild',
  events: ['work.verified', 'tokens.awarded', 'project.funded']
});
```

---

## 9. Testing Your Integration

Use sandbox mode to test without real money:

```javascript
// All API calls in sandbox mode use test tokens
const testProject = await bild.projects.create({
  name: "Test Project",
  brix_budget: 100,  // Test BRIX, not real
  guld_equity_percent: 5
});

// Simulate work verification
const testSubmission = await bild.work.submit({
  task_id: "test-task-123",
  user_id: "test-user",
  evidence: { type: "test", content: "sample work" }
});

// In sandbox, verification returns in ~30 seconds vs 5-15 minutes in production
```

---

## 10. Go Live

When ready, switch to production:

```javascript
const bild = new BildClient({
  apiKey: process.env.BILD_API_KEY,
  environment: 'production'  // Changed from 'sandbox'
});
```

### Pre-launch Checklist
- [ ] Test all critical user flows in sandbox
- [ ] Set up webhook endpoints and test them
- [ ] Implement error handling for API failures
- [ ] Add user-friendly error messages
- [ ] Set up monitoring/logging for BILD API calls
- [ ] Review security practices (API key storage, etc.)

---

## Common Integration Patterns

### Pattern 1: Task Marketplace
```javascript
// Users post tasks, others complete them for BRIX/GULD
const task = await bild.tasks.create({
  title: "Design a logo",
  brix_reward: 75,
  guld_reward: 0.25,
  // ... other fields
});
```

### Pattern 2: Collaborative Projects
```javascript
// Teams work together on larger projects
const project = await bild.projects.create({
  type: "collaborative",
  team_size: 5,
  brix_budget: 2500,
  guld_equity_percent: 20  // Split among team
});
```

### Pattern 3: Content Creation
```javascript
// Writers, artists, creators earn for their work
const creativeTask = await bild.tasks.create({
  type: "creative_work",
  deliverable: "video_content",
  brix_reward: 100,
  guld_reward: 1.0
});
```

---

## Error Handling

```javascript
try {
  const submission = await bild.work.submit(workData);
} catch (error) {
  if (error.code === 'INSUFFICIENT_BALANCE') {
    // Project doesn't have enough BRIX to pay
    showError("This project cannot pay for new work right now");
  } else if (error.code === 'WORK_REJECTED') {
    // 8OWLS verification failed
    showError(`Work quality too low: ${error.feedback}`);
  } else {
    // Generic error
    showError("Something went wrong. Please try again.");
  }
}
```

---

## Rate Limits

| Endpoint | Rate Limit | Notes |
|----------|------------|--------|
| Projects | 10/minute | Creating projects |
| Tasks | 50/minute | Creating/updating tasks |
| Work Submission | 20/minute | Submitting work for verification |
| Wallet Operations | 100/minute | Balance checks, transactions |

---

## Next Steps

- **[Smart Contract Integration](./SMART-CONTRACT-GUIDE.md)** - Deep blockchain integration
- **[8OWLS API Guide](./8OWLS-API-GUIDE.md)** - Custom verification logic  
- **[Security Guide](./SECURITY-GUIDE.md)** - Protect against gaming
- **[API Reference](./API-REFERENCE.md)** - Complete endpoint documentation

---

## Support

- **Docs:** [docs.bild.network](https://docs.bild.network)
- **Discord:** [discord.gg/bild](https://discord.gg/bild)
- **Email:** [dev-support@bild.network](mailto:dev-support@bild.network)

---

**🚀 You're ready to build the ownership economy!**

*15 minutes to integrate. Lifetime of value to create.*

---

🦉 **Part of the 8OWLS Ecosystem**