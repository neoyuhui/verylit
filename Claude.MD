## Updated product direction

The product is a safety-first CJTS preparation and claim-readiness assistant.

It must not simply generate a persuasive claim. It should help the SRP:

1. Tell the story in their own words
2. Distinguish facts from assumptions and inferences
3. Organise parties, agreement, issues, chronology, remedy, and evidence
4. Check whether important information is known, unclear, missing, or unverified
5. Identify contradictions
6. Consider the respondent’s likely position
7. Identify evidence that supports or undermines each material assertion
8. Prepare a factual draft and evidence bundle for user review
9. Verify procedural information against official sources
10. Escalate uncertain or legally complex matters to appropriate human or official assistance

The system must begin by checking whether the matter appears connected to Singapore and whether the Small Claims Tribunals may be the appropriate forum.

## Core workflow

Use this workflow:

1. Scope and disclaimer
2. Jurisdiction and forum screening
3. User’s original account
4. Preliminary fact extraction
5. Clarification questions
6. Evidence upload and categorisation
7. Verification and contradiction detection
8. Mandatory counter-argument challenge
9. Pre-filing readiness check
10. Preparation of chronology, issue matrix, checklist, and factual draft
11. User confirmation
12. Official-source links and escalation options

Do not allow the user to skip the safety and verification steps before generating a final factual draft.

## Scope and disclaimer

At the start, display:

“This tool is an independent prototype. It does not provide legal advice, does not determine whether you will win, and is not affiliated with the Singapore Courts. It helps organise your account, identify missing information, and check procedural readiness. You remain responsible for verifying and submitting your information.”

The assistant should explain that a preliminary readiness check is not a legal opinion or guarantee that a claim will succeed.

## User’s original account

Begin with:

“Tell me what happened in your own words. You may include incomplete details, emotions, uncertainty, or typos. We will organise and verify the information later.”

Preserve the original account exactly.

Do not immediately rewrite it into legal or persuasive language.

Store separately:

- Original user account
- Transcription
- Extracted facts
- Inferences
- Uncertainties
- User-confirmed facts
- Draft factual summary

## Fact extraction

After the user gives their account, produce a preliminary understanding.

Use categories such as:

- Parties
- Agreement or transaction
- Chronology
- Main issue
- Requested outcome
- Amounts
- Documents mentioned
- Missing information
- Possible contradictions
- Inferences requiring verification

This categorisation is non-exhaustive and must not be presented as a complete legal test.

Use language such as:

“This is a preliminary organisation of the information you provided. It is not a legal assessment or conclusion.”

Do not say that the user “fulfils” the SCT conditions unless each condition has been verified against an official source and the wording is appropriately qualified.

## Facts, inferences, and uncertainty

Every extracted statement must be classified as one of:

- User-stated fact
- Document-supported fact
- Officially verified procedural fact
- Inference
- Assumption
- Contradiction
- Missing information
- Unverified information

Use visible labels.

Example:

User-stated fact:
“The photographer refused to provide the raw photographs.”

Inference detected:
“You suggested that the photographer’s health condition caused the poor photographs.”

Clarification:
“Do you have evidence supporting that connection, such as a message from the photographer or another record?”

Never convert an inference into a fact.

Never write:

“His scoliosis caused him to perform the contract inadequately.”

Unless the user specifically states this and reliable evidence supports it, write:

“You stated that you believe his health condition affected the photographs. This connection has not been verified.”

## Mandatory clarification questions

Ask clarification questions before producing a final factual summary.

Questions may include:

- What was agreed?
- When was it agreed?
- What was paid?
- How much was paid?
- When was payment made?
- What exactly was promised?
- What exactly happened?
- When did each event happen?
- What outcome did you originally expect?
- What outcome are you now requesting?
- What did the other party say?
- Did you give the other party an opportunity to respond or fix the issue?
- What documents support each important fact?
- Which facts are uncertain?
- Which details are based only on assumptions?

Ask only questions relevant to the user’s issue.

## Evidence mapping

Every important factual assertion should be mapped to one of:

1. User’s original account
2. Uploaded evidence
3. Official procedural source
4. Unverified information

Use this structure:

| Assertion | Source | Status | Follow-up |
|---|---|---|---|
| Payment was made | Receipt uploaded by user | Supported by document | Check amount and date |
| Refund was requested | WhatsApp screenshot | Supported by document | Confirm screenshot date |
| Poor photographs were caused by health condition | User’s inference | Unverified | Ask for supporting evidence |

The system must ask:

- “What evidence supports this?”
- “Is this based on something you saw, something someone told you, or your own assumption?”
- “Do you have a document showing this?”
- “Is there evidence that may point in the other direction?”

## Contradiction detection

Compare information across:

- User’s story
- Speech transcription
- Uploaded documents
- Timeline
- Form entries
- Previous answers

Flag contradictions such as:

- User states $500 was paid but receipt shows $650
- User states the agreement happened in June but a message shows July
- User states a refund was requested but no communication is provided
- User names an individual but the evidence names a company
- User states the business is active but the ACRA information suggests otherwise

When a contradiction exists:

1. Highlight it neutrally.
2. Show both conflicting values.
3. Ask the user to clarify.
4. Do not silently select one value.
5. Do not proceed to a final draft until the user confirms how it should be represented.

Use:

“I found two different amounts in the information provided. Please check which amount is accurate, or explain why both amounts appear.”

## Mandatory counter-argument step

Before finalising a claim summary, the assistant must challenge confirmation bias.

Ask:

- “What might the respondent say happened?”
- “What explanation might the respondent give?”
- “Which facts could make your position more difficult?”
- “Is there any document that may support the respondent’s version?”
- “Did the respondent offer an explanation, repair, refund, replacement, or alternative?”
- “Are there facts that do not fit your current account?”
- “What evidence would you want the respondent to produce?”

Show two separate views:

1. User’s current account
2. Possible respondent position

The respondent position must be labelled as a possible argument, not as a fact.

The purpose is to identify missing information and evidence, not to argue against the user.

## Preliminary readiness check

The readiness check may assess whether the file appears:

- Ready for further review
- Missing important information
- Contains unresolved contradictions
- Requires official verification
- May require human or legal assistance

Do not call the result a prediction of success.

Do not use a numerical “chance of winning” score.

Use statuses such as:

- Known
- Unclear
- Missing
- Contradictory
- Unverified
- Requires official confirmation

## Official-source retrieval

Procedural information must come from official sources rather than model memory.

Important topics include:

- SCT eligibility
- Claim limits
- Time limits
- Filing fees
- Required documents
- Respondent details
- ACRA information
- Service
- Consultation
- Enforcement or execution
- Which court or tribunal may be appropriate

If the information cannot be verified from an official source, say:

“I do not have a verified answer. Please check the current Singapore Courts or CJTS guidance, or obtain appropriate legal assistance.”

Link important procedural assertions to the relevant official source.

## Evidence upload and document preparation

Allow users to:

- Drag and drop documents
- Upload images, PDFs, screenshots, receipts, messages, and photographs
- Add document descriptions
- Associate documents with timeline events
- Mark documents as original, copy, screenshot, or photograph
- Review extracted text before it is used
- Delete documents

The prototype may convert uploaded images into a PDF evidence bundle for user review.

However:

- Do not modify the original image
- Preserve the original file
- Clearly label generated PDFs as compiled copies
- Do not claim that conversion verifies authenticity
- Do not silently OCR or translate evidence without showing the result
- Do not submit the bundle automatically

## Outputs to prepare

After sufficient information has been collected, prepare:

1. Chronology
2. Party matrix
3. Agreement summary
4. Issue matrix
5. Requested outcome
6. Evidence bundle index
7. Missing-information checklist
8. Contradiction report
9. Possible respondent position
10. Pre-filing readiness checklist
11. Factual draft for user review

These outputs are organisational tools, not legal advice.

## Issue matrix

Use a non-exhaustive issue matrix:

| Topic | What the user said | Evidence | Status | Clarification needed |
|---|---|---|---|---|
| Parties | Photographer operated a one-person business | Business page and messages | Unclear | Confirm legal name and entity |
| Agreement | Photography service was hired for wedding | Messages and payment record | Partially supported | Confirm agreed deliverables |
| Performance | Photographs were poor or unusable | Photographs | User evidence available | Identify specific defects |
| Health condition | User believes this caused poor performance | User statement | Inference | Ask whether supporting evidence exists |
| Requested outcome | Raw unedited photographs or refund | User statement | User-confirmed if accepted | Confirm preferred remedy |

Do not present this matrix as a complete legal test.

## Escalation

If the system identifies a matter requiring human or official help, provide:

- The reason for escalation
- The relevant official organisation
- The official webpage
- Available contact or access instructions
- A reminder that the assistant cannot decide the legal issue

Possible escalation topics include:

- Unclear jurisdiction
- Possible limitation issue
- Unclear respondent identity
- Bankruptcy or insolvency
- Complex business structure
- Privacy or confidentiality concern
- Enforcement or execution
- Foreign-law issue
- Serious contradiction
- Matter outside SCT scope

## Eligibility and pre-filing screening workflow

The prototype must include a structured pre-filing screening flow before the user proceeds with claim preparation.

The screening flow should cover:

1. Parties and entity details
2. Nature of the dispute
3. Service and respondent location
4. Contractual relationship
5. ACRA status and registered address
6. Possible mediation or arbitration clauses
7. Whether the claim involves a restricted subject matter
8. Whether the user is seeking an available type of order

The questions must be asked conditionally. Do not show every question to every user.

### Parties and entity details

The system may need to ask:

- Are you claiming as an individual?
- If not, are you claiming as a corporate entity?
- Is your corporate entity in liquidation or winding-up?
- Are you claiming against the correct party with whom you have a contractual obligation?
- Is the other party an individual?
- Is the other party a corporate entity?
- Is the other party in liquidation or winding-up?
- Do you have a recent ACRA record showing the entity’s address and status?
- Is there a mediation or arbitration clause in the agreement?

If an ACRA record is required, explain that the user should obtain the current record from the official ACRA website. Do not imply that the prototype can verify the entity unless it is connected to an authoritative, current source.

### Nature of dispute

The system may need to ask:

- Are you the owner of the property?
- Did the cause of action arise on or before the relevant date specified by the current official SCT guidance?
- Did the damage arise out of or in connection with a motor vehicle?
- Are you seeking a money order, work order, and/or an order for delivery of vacant possession?

If an answer suggests that the SCT may not have jurisdiction:

- Do not allow the assistant to state a definitive legal conclusion unless supported by the current official source.
- Display that the matter may fall outside SCT jurisdiction.
- Link to the relevant official source.
- Recommend checking with the Singapore Courts or obtaining appropriate legal advice.

### Service

The system may need to ask:

- Is the party or company located in Singapore?
- Does the party have a registered address in Singapore?
- Are you able to locate and personally serve or bring the claim to the other party’s attention in Singapore?

Service questions must be treated as procedural screening prompts, not as a guarantee that service will be valid.

### Source-control requirement

All jurisdiction, eligibility, date, claim-limit, entity-status, service, and available-remedy questions must be stored with:

- Official source URL
- Source title
- Date last reviewed
- Applicable process or claim type
- Version or notes
- Review status

Do not rely on Claude’s general memory for these questions.

If a question contains a date, deadline, limit, fee, or jurisdictional rule, verify it against the current official source before displaying it to users.