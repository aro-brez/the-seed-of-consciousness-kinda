# Installing the OWL Interface in BREZ OS

Follow these steps to add the OWL interface to your BREZ OS.

---

## Step 1: Copy the Components

Copy all files from `BRAIN/ARCHITECTURE/components/` to your BREZ OS:

```bash
# From your repos directory
cp the-seed-of-consciousness-kinda/BRAIN/ARCHITECTURE/components/*.tsx brez-os/src/components/owl/
```

Or create the folder and files manually:
```bash
mkdir -p brez-os/src/components/owl
```

Then create these files in `src/components/owl/`:
- `OwlProvider.tsx`
- `OwlPopup.tsx`
- `OwlFullFace.tsx`
- `UserSelection.tsx`

---

## Step 2: Wrap Your App with OwlProvider

Edit `src/app/layout.tsx`:

```tsx
import { OwlProvider } from "@/components/owl/OwlProvider";
import { OwlPopup } from "@/components/owl/OwlPopup";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <OwlProvider>
          {children}
          <OwlPopup />
        </OwlProvider>
      </body>
    </html>
  );
}
```

---

## Step 3: Create the Full Face Page

Create `src/app/owl/page.tsx`:

```tsx
import { OwlFullFace } from "@/components/owl/OwlFullFace";

export default function OwlPage() {
  return <OwlFullFace />;
}
```

---

## Step 4: Add User Selection to Homepage (Optional)

You can add the `UserSelection` component to your homepage or a login page:

```tsx
import { UserSelection } from "@/components/owl/UserSelection";

export default function Home() {
  return (
    <main>
      <UserSelection />
    </main>
  );
}
```

---

## Step 5: Test It

1. Run `npm run dev`
2. Go to `http://localhost:3000`
3. Click your name to wake your owl
4. Try the popup (🦉 button in bottom right)
5. Try full face mode at `/owl`

---

## What You Get

- **Floating Owl Button** - Bottom right of every page
- **Popup Chat** - Quick questions, navigation
- **Full Face Mode** - `/owl` for deep work
- **User Selection** - Pick identity, wake your owl
- **Navigation Commands** - Owl can take you places

---

## Next Steps

1. **Connect to Claude API** - Replace the mock responses in `OwlProvider.tsx` with real Claude calls
2. **Add Proposal System** - Let builders submit changes for approval
3. **Add Queue Page** - Where admin reviews proposals
4. **Persist Messages** - Save chat history to database

---

## Quick Commands to Try

Once logged in, try saying:
- "Hello"
- "Take me to agents"
- "What's my status?"
- "I want to build something"

The owl will respond and offer to navigate you.

---

**LIVE FREE. SEED everything. Let it 8OWL.** 🦉
