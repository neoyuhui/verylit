# CJTS SRP Guidance Assistant

## Project goal

Build a Chrome Extension prototype for Singapore self-represented persons (SRPs) using the Community Justice and Tribunals System (CJTS) and Small Claims Tribunals (SCT).

The extension should help users:

- Check whether their issue may be connected to Singapore
- Understand whether the SCT may be the appropriate process
- Select an issue category
- Answer simple guided questions
- Explain what happened in their own words
- Use speech-to-text
- Use English, Mandarin, Malay, or Tamil
- Organise documents and evidence
- Build a timeline of events
- Identify missing information
- Understand CJTS form fields
- Review information before submission
- Understand basic post-filing steps

This is an independent hackathon prototype. It is not affiliated with or endorsed by the Singapore Courts.

## Important legal boundaries

Do not present the assistant as a lawyer, court officer, or official Singapore Courts service.

Do not:

- Give definitive legal advice
- Predict whether a user will win
- Decide that a claim is valid or invalid
- Invent legal rules, deadlines, fees, documents, or procedures
- Fabricate, alter, strengthen, or delete evidence
- Create fake receipts, messages, photographs, contracts, or screenshots
- Encourage users to hide unfavourable facts
- Submit anything to CJTS automatically
- Ask users for Singpass passwords, OTPs, banking credentials, or private keys

Use wording such as:

- “This may be relevant to check.”
- “The official Singapore Courts guidance says…”
- “You may need to confirm this.”
- “I cannot determine whether your claim will succeed.”
- “This is procedural guidance, not legal advice.”

The user must remain responsible for checking and submitting their own information.

## Jurisdiction-first flow

Before guiding the user through a claim, ask:

1. What country is connected to the dispute?
2. Where is the respondent located?
3. Where did the incident or transaction happen?
4. Is the user trying to file in Singapore?
5. What type of dispute is involved?
6. Does the user know whether the matter belongs in the SCT?

If the matter may be outside Singapore or outside the SCT:

- Do not continue as if it is definitely an SCT matter.
- Explain what is uncertain.
- Link to an official source.
- Suggest checking with the Singapore Courts or an appropriate legal adviser.

Do not make an eligibility decision without a reliable official source.

## Chatbot behaviour

Use a structured interview instead of immediately generating long answers.

Ask one or two questions at a time in this order:

1. Jurisdiction
2. Current stage
3. Issue category
4. Claimant details
5. Respondent details
6. Chronology of events
7. Loss or remedy requested
8. Evidence available
9. Missing information
10. Final review

Possible issue categories:

- Refund or unpaid payment
- Defective goods
- Poor or incomplete service
- Repair or renovation dispute
- Tenancy or premises dispute
- Contract disagreement
- Delivery or purchase dispute
- Business or company dispute
- Unsure where to file

For each answer, separate:

- Facts supplied by the user
- Assumptions
- Uncertainties
- Missing information
- Suggested next step

When the user asks “Will I win?” or “Can I sue them?”, do not give a yes/no prediction.

Instead, identify:

- Facts supporting the user’s account
- Facts that may create difficulty
- What the other party might say
- Missing information
- Documents that may help establish what happened
- What should be verified officially

## Voice-to-text behaviour

Speech recognition and AI summarisation are separate steps.

The flow must be:

1. User speaks
2. Browser or speech service creates a transcription
3. User reviews and edits the transcription
4. Claude organises the facts
5. User confirms the organised summary
6. The system optionally creates draft wording for review

Always display:

“Here is what I understood. Please correct anything that is inaccurate.”

Never silently convert the user’s words into stronger legal language.

Preserve:

- Original transcription
- Corrected transcription
- AI-organised summary
- Final user-approved version

The user must be able to edit, reject, or redo the transcription.

## Evidence handling

The evidence organiser may store:

- File name
- File type
- Date
- Related event
- User-written description
- Original, copy, screenshot, photograph, receipt, message, or contract classification
- Optional notes

The system may suggest categories, but the user must confirm them.

Do not interpret evidence as legally conclusive.

Generate:

- A factual timeline
- A document checklist
- Missing-information prompts
- Possible contradictions for the user to review

Do not generate legal conclusions.

## Language support

Support:

- English
- Mandarin
- Malay
- Tamil

Preserve accurately:

- Names
- Dates
- Amounts
- Addresses
- Claimant/respondent distinctions
- Procedural terminology

Show important English legal or procedural terms alongside translated explanations where possible.

Do not silently translate or alter uploaded evidence.

## Walkthrough behaviour

The walkthrough should explain:

- What each field asks for
- Why the field may matter
- An example
- Common mistakes
- How to ask for help
- How to skip the step

Use semantic matching in this order:

1. Accessible labels
2. Visible text
3. Nearby headings
4. Form labels
5. Field attributes
6. CSS selectors as a fallback

If a field cannot be found:

- Do not click a guessed element.
- Tell the user the page may have changed.
- Give manual instructions.
- Let the user continue manually.
- Log the failure for debugging.

Never overwrite user-entered information without confirmation.

Require explicit confirmation before:

- Payment
- Declaration
- Filing
- Submission
- Any irreversible action

## Privacy and security

Treat all user information as sensitive.

Prefer local browser storage for the prototype.

Clearly show:

- What is processed locally
- What is sent to an AI model
- What is stored
- How it can be deleted

Before sending sensitive text or documents to an external AI service, warn the user and offer redaction.

Do not collect unnecessary:

- NRIC or passport numbers
- Singpass information
- Passwords
- OTPs
- Banking details
- Medical information
- Private correspondence
- Confidential business documents

Display:

“This is an independent prototype and is not affiliated with or endorsed by the Singapore Courts.”

## Technical architecture

Use:

- Chrome Manifest V3
- Content script
- Side panel or floating panel
- Background service worker
- `chrome.storage.local`
- Configuration-driven walkthrough steps
- Structured JSON state
- A mock CJTS webpage for development

Do not rely entirely on the live CJTS website.

Use feature flags for:

- `walkthrough`
- `chatbot`
- `voiceInput`
- `translation`
- `evidenceOrganiser`
- `mockMode`

## Suggested project structure

```text
src/
├── background/
│   └── service-worker.js
├── content/
│   └── cjts-detector.js
├── sidepanel/
│   ├── App.jsx
│   ├── Chatbot.jsx
│   ├── Walkthrough.jsx
│   ├── VoiceInput.jsx
│   ├── EvidenceOrganiser.jsx
│   └── ReviewScreen.jsx
├── data/
│   ├── officialSources.js
│   ├── walkthroughSteps.js
│   └── translations.js
├── state/
│   └── caseState.js
└── utils/
    ├── semanticFieldMatcher.js
    └── privacy.js