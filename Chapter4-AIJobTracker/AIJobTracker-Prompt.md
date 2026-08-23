I want to generate AI job tracker 

below is prompt available 

make sure do not assume extract requirement. Just create everything using details in prompt . make sure its Kanban view scrollable to right and left to user and ever job card has message under its name and above money saying "You have applied this job in naukri" or You have applied this job in linked in  and if its under wishlist section it shall display "Yu have wishlisted in Monster" like wise in little thick pink /red color .  

also above kanban boafrd add summary of applications status like how many applications are submitted how many are in interview round state how many are offer received like wise in detail. 
Also add atleast 2 under offer received , 1 under interview round which should be like on going interview for it now like that

Create a local-first, highly advanced AI QA Cockpit and Application Pipeline as a single-page React application scaffolded with Vite. All data must persist locally using IndexedDB via the idb package wrapper. No backend dependencies, tracking, or authentication are allowed.

Data Model — Each card (Application & Automation Gate) stores:
- id (UUIDv4, auto-generated on insertion)
- Company name (text, required, trimmed, max 50 chars)
- Job title / role (text, required, trimmed, max 50 chars)
- Application Channel (Dropdown selector: "LinkedIn", "Naukri", "Wellfound", "Direct / Cold Outreach", "Company Career Portal", "Indeed")
- Date applied / Date updated (automated ISO timestamps)
- Target Compensation (optional text, e.g., "$145k - $175k")
- Tech Stack Tagging (multi-select tag array: "Playwright", "PyTest", "LangSmith", "LlamaIndex Evaluation", "GitHub Actions", "Docker", "Selenium Grid")
- Priority State (Dropdown selector: "High", "Medium", "Low")
- Application Lifecycle Status (Dropdown mapping columns)

Dynamic Grid Kanban Columns Layout (5 Sticky Locked Headers):
1. 🎯 Wishlist & Triage — Initial target pool tracking companies with open AI infrastructure or quality testing requirements.
2. 📝 Applied & Pending — Complete formal documentation and resume matching payloads successfully transmitted.
3. ⚙️ Technical Assessment — Live initial screening loops or algorithmic test assignments.
4. 🧪 Interview Loops — Deep-dive live coding, core automation testing, or prompt vulnerability assertions.
5. 💰 Offer & Negotiation — Formal documentation delivered; tracking negotiation cycles.

Deterministic Seed Layout Data (Hydrate Exactly Following This Array):
- Card 1: { companyName: "NeuroFlow Systems", jobTitle: "Senior QA Engineer - AI Agents", priority: "High", applicationChannel: "LinkedIn", targetCompensation: "$145k - $175k", techStack: ["Playwright", "LLM Evals", "Python"], lifecycleStatus: "wishlist" }
- Card 2: { companyName: "Flipkart", jobTitle: "AI Automation Specialist", priority: "Medium", applicationChannel: "Flipkart Portal", targetCompensation: "$130k - $160k", techStack: ["Selenium", "LangChain", "PyTest"], lifecycleStatus: "wishlist" }
- Card 3: { companyName: "Dell", jobTitle: "Lead ML QA Engineer", priority: "High", applicationChannel: "Dell Careers", targetCompensation: "$160k - $190k", techStack: ["Cypress", "PyTorch", "CI/CD"], lifecycleStatus: "applied" }
- Card 4: { companyName: "Cognitive Labs", jobTitle: "QA Engineer (Agentic Workflows)", priority: "Low", applicationChannel: "LinkedIn", targetCompensation: "$120k - $150k", techStack: ["Playwright", "TypeScript", "Evals"], lifecycleStatus: "applied" }

UI/UX & Design Token Constraints:
- Main Heading Requirement: Prominently display a static, clear typography title header text component reading "AI Tracker for QA Engineer" at the absolute apex of the application canvas workflow dashboard layout.
- Search and Filtering Panel Layout: Render an inline toolbar right below the statistics bar containing a left-aligned search input box and a right-aligned horizontal segmented pill row filter for Priority selection ("All", "High", "Medium", "Low").
- Horizontal Kanban Layout Sequence: The columns must be laid out horizontally in a side-by-side series format where the columns fill the layout width contextually.
- Card Sourcing Context Placement & Conditional Syntax Logic: Inside each Kanban card body layout, directly below the job metadata layout and immediately above the Target Compensation box, render an explicit contextual sentence string. 
  - If the card resides in the "Wishlist & Triage" pipeline stage column, evaluate and print the exact syntax template rule using its current application channel: "(You wishlisted it in [channel_name_here])" (e.g. "(You wishlisted it in LinkedIn)" or "(You wishlisted it in Flipkart Portal)").
  - For all other pipeline execution columns across the board matrix (e.g., Applied & Pending), evaluate and print the exact syntax template rule: "(You applied this job in [channel_name_here])" (e.g., "(You applied this job in LinkedIn)" or "(You applied this job in Dell Careers)").
- Priority Visual Anchor Banding: Each card must possess a solid 4px wide solid vertical colored border on its left-most boundary edge mapping to its priority context (High = Rose-500 red, Medium = Amber-500 yellow, Low = Emerald-500 green).
- Micro Column Shifting Controllers: Provide small left (<) and right (>) button arrows in the sub-footer section of each card allowing user tracking movements across the kanban columns linearly.
