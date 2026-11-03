# FinAssist AI — DBS Knowledge Base Source Register

**Last checked:** 3 November 2026  
**Geographic scope:** DBS/POSB Singapore personal banking information  
**Purpose:** Traceability for the five Markdown files indexed by the FinAssist AI RAG pipeline.

## 1. Source inventory

| Knowledge-base file | Official source | Main coverage |
|---|---|---|
| `01_dbs_card_faqs.md` | https://www.dbs.com.sg/personal/cards/cards-faqs.page | Card eligibility, application processing, PIN reset, card support |
| `01_dbs_card_faqs.md` | https://www.dbs.com.sg/personal/cards/cards-application-checklist.page | Additional card application eligibility information |
| `02_dbs_fraud_reporting.md` | https://www.dbs.com.sg/personal/support/guide-security-on-scams-and-fraud.html | Scam response, compromised details, Safety Switch, reporting |
| `02_dbs_fraud_reporting.md` | https://www.dbs.com.sg/personal/bank-safely/get-help.page | DBS Scam Defence and support |
| `02_dbs_fraud_reporting.md` | https://www.dbs.com.sg/personal/contact-us | Official contact channels and 24-hour fraud hotline |
| `03_dbs_transaction_disputes.md` | https://www.dbs.com.sg/personal/support/general-incorrect-transaction.html | Transaction checks, fraud disputes, pending transactions, dispute outcomes |
| `03_dbs_transaction_disputes.md` | https://www.dbs.com.sg/personal/cards/cards-faqs.page | Related card FAQ information |
| `04_dbs_lost_stolen_cards.md` | https://www.dbs.com.sg/personal/support/card-issues-lost-card.html | Blocking/replacing cards and conditional liability information |
| `04_dbs_lost_stolen_cards.md` | https://www.dbs.com.sg/personal/contact-us | Official contact channels |
| `05_dbs_fees_and_charges.md` | https://www.dbs.com.sg/personal/cards/cards-rates-fees.page | Selected card fees, interest and overseas transaction charges |
| `05_dbs_fees_and_charges.md` | https://www.dbs.com.sg/personal/cards/cards-faqs.page | Related card fee and payment FAQ information |

## 2. How these documents were prepared

The Markdown files are AI-assisted summaries of selected publicly available DBS webpages. AI was used to organise source information into topic-based sections and retrieval-friendly passages.

The summaries were checked against the linked official DBS pages for key figures, procedures, conditions and limitations. They are not verbatim copies, official DBS publications or a complete representation of DBS policy.

## 3. Scope boundaries

- The knowledge base contains selected DBS/POSB Singapore personal-card and fraud-support information only.
- It does not cover all DBS products, policies, terms, exceptions or customer circumstances.
- The SQLite transaction database is synthetic demonstration data. It is not connected to DBS and contains no actual DBS customer transactions.
- FinAssist AI is an independently developed academic prototype. It is not affiliated with, endorsed by or operated by DBS.
- The chatbot cannot access real bank accounts, block cards, activate the Safety Switch, submit disputes, reverse transfers or investigate customer cases.

## 4. Retrieval and answer policy

- If retrieved passages do not support an answer, the chatbot should say that the available knowledge base does not contain enough information.
- Product-specific conditions must not be generalised to other cards.
- Conditional liability limits must always retain their conditions.
- Fees and rates must be identified by card category, transaction type and relevant conditions.
- Do not promise dispute success, reimbursement, fund recovery or a fixed investigation outcome.
- For active fraud or lost-card incidents, direct the customer to DBS's official hotline rather than presenting the chatbot as an emergency service.

## 5. Maintenance procedure

When refreshing the knowledge base:

1. Open each official source URL and confirm that it is still accessible.
2. Check whether the relevant figures, instructions, conditions or contact details have changed.
3. Update only the sections supported by the source.
4. Preserve important qualifications and exceptions.
5. Update the `Last checked` date in the relevant Markdown file and this register.
6. Run retrieval tests for each topic.
7. Re-run the answer-grounding and safety evaluation before presenting the updated chatbot.

## 6. Suggested retrieval test queries

- Am I eligible for a DBS debit card if I am 16?
- What is the general income requirement for a DBS credit card?
- How long does a DBS card application take?
- What should I do if I gave my banking OTP to a scammer?
- What is the DBS fraud hotline if I am overseas?
- How do I report an unauthorised credit-card transaction?
- Can DBS cancel a pending card transaction?
- Does the S$100 lost-card liability limit apply automatically?
- What is the cash advance fee on the selected DBS credit-card fee page?
- Is the overseas SGD processing fee the same for debit and credit cards?
