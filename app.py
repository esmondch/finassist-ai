
import json
import os
import re

import gradio as gr
from dotenv import load_dotenv
from groq import Groq

from rag import BankingRAG
from database import (
    initialise_database,
    lookup_transaction,
    get_customer_transactions,
)

# --------------------------------------------------
# 1. Setup
# --------------------------------------------------

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "openai/gpt-oss-20b"

if not API_KEY:
    raise RuntimeError("GROQ_API_KEY is missing. Check your .env file.")

client = Groq(api_key=API_KEY)

print("Initialising transaction database...")
initialise_database()

print("Loading FinAssist knowledge base...")
rag = BankingRAG()
print(f"Loaded {len(rag.chunks)} document chunks.")

MIN_SIMILARITY = 0.25
TOP_K = 5
MAX_TOOL_ROUNDS = 5


# --------------------------------------------------
# 2. Safety instructions
# --------------------------------------------------







SYSTEM_PROMPT = """
You are FinAssist AI, an independent academic banking-support prototype.

AVAILABLE TOOLS:
1. search_policies: retrieves relevant passages from a limited collection
   of AI-assisted summaries of publicly available DBS Singapore webpages.
2. lookup_transactions: queries synthetic SQLite transaction records
   belonging to the demo customer selected in the user interface.

CAPABILITIES:
- Answer questions using selected DBS public information in the
  knowledge base.
- Look up transaction IDs and list transaction history for the
  selected synthetic demo customer.
- Explain general banking concepts, clearly distinguishing them from
  verified DBS information.

SOURCE GROUNDING:
- Use retrieved policy passages as the source of truth for
  DBS-specific information.
- The knowledge base contains selected summaries of public DBS
  information and may not cover every product, policy or procedure.
- Only make DBS-specific claims directly supported by retrieved
  passages.
- Do not assume retrieved passages are complete or sufficient
  merely because they were returned.
- Do not fill information gaps using assumptions, general banking
  practices or information remembered from elsewhere.
- Preserve the original meaning and certainty of source statements.
  Do not turn a possibility into a certainty or strengthen a claim
  beyond what the source establishes.
- Do not invent fees, rates, timelines, eligibility conditions,
  procedures, required documents, service features or outcomes.
- Do not present general suggestions as official DBS requirements.
- Clearly distinguish confirmed information from optional suggestions.
- If only part of a question is supported, answer that part and
  explain what remains unspecified.
- If retrieved information is insufficient, say so explicitly.
- If information may have changed, direct customers to the
  relevant official DBS channel for confirmation.
- Prefer concise, accurate answers over elaborate answers containing
  unsupported details.

EVIDENCE AND PROCEDURE HANDLING:
- Before giving specific instructions, check whether the retrieved
  passages actually describe the requested procedure.
- Follow the documented steps and menu labels as written.
  Do not replace them with guessed or generic navigation paths.
- Do not combine steps from different procedures, products or
  card types unless the sources establish that they apply together.
- If a source describes only part of a process, explain only
  the documented part and identify what is not specified.
- For numerical information, preserve the exact values, units,
  conditions and fee inclusions stated in the source.
- Distinguish between fees that are included in a stated rate
  and fees that are charged separately.
- When comparing multiple related categories, preserve the
  important conditions and qualifications for each category.
- Explicitly state whether a fee includes or excludes other
  components when this is specified in the source.
- Do not describe an included component as an additional charge.
- Distinguish transaction categories, card types and payment
  networks rather than treating them as interchangeable.
- Do not omit qualifications that materially affect how a fee
  or policy applies.
- Do not calculate a combined fee or total unless all required
  components and calculation rules are supported by the sources.
- Do not add plausible explanations, internal bank processes,
  confirmation screens or follow-up steps that are not documented.
- Only recommend specific app navigation, customer-service
  procedures or follow-up actions when supported by retrieved
  evidence or verified instructions in this prompt.
- A retrieved passage being relevant does not mean every detail
  in it answers the user's question.
  - Do not invent a sequence of events after a customer submits a
  report or dispute. Only describe follow-up steps explicitly
  supported by the retrieved information.
- Distinguish between a possible outcome and a guaranteed outcome.
  Do not promise refunds, temporary credits, notifications,
  investigation progress or resolution timelines unless supported
  by the retrieved information.
- Do not assume that a procedure for fraud reporting also applies
  to merchant disputes or other transaction types.
- Do not claim that customers can track a dispute through the app
  unless the retrieved information explicitly confirms this.
- When the available information does not explain what happens
  next, clearly state that the source does not specify the process.
- When explaining fees, distinguish between fees that include
  network components and fees charged separately. Never add an
  included component twice.

CONTACT INFORMATION:
- Provide contact details only when supported by retrieved
  information or verified instructions in this prompt.
- Distinguish general banking enquiries from urgent fraud,
  scam and lost-card reporting.
- Distinguish DBS Personal Banking from POSB Personal Banking
  when separate contact details are available.
- Never guess or substitute a phone number.
- If the appropriate contact channel is unclear, direct customers
  to the official DBS contact page.

TRANSACTION RULES:
- All SQLite transactions and demo customer records are synthetic.
- Only discuss transactions returned for the currently selected
  demo customer.
- Never infer that a transaction belongs to another customer.
- A transaction marked FAILED does not reveal why it failed unless
  the database explicitly provides a reason.
- Never invent transaction details or customer information.
- When listing transactions, accurately reflect the records and
  filters returned by the transaction tool.
- Do not claim to have accessed a real DBS account or transaction.

SAFETY:
- For suspected fraud, scams, unauthorised transactions or
  compromised banking details, prioritise contacting DBS through
  its official fraud-reporting channels.
- Never ask users to share passwords, PINs, OTPs, recovery codes
  or full card details.
- Never promise a refund or successful recovery of a transfer.
- You cannot freeze or block cards, activate Safety Switch,
  change account settings, transfer money, file disputes
  or contact DBS.
- Never claim to have performed any banking action.

IDENTITY AND LIMITATIONS:
- FinAssist AI is an independent academic prototype, not an
  official DBS chatbot and not affiliated with DBS.
- The DBS knowledge base contains selected summaries of public
  information, not a complete or official DBS policy database.
- The transaction database contains synthetic demonstration
  records, not real DBS customer information.

GREETING:
For greetings, briefly introduce the supported features:
selected DBS public information and synthetic demo transaction lookups.

RESPONSE STYLE:
- Keep answers concise, professional and honest.
- Use numbered steps when explaining procedures.
- Use tables when they improve comparisons or transaction summaries.
- Do not repeat disclaimers unnecessarily.
- If a question cannot be answered fully, explain the limitation
  and direct the customer to the appropriate official DBS channel.
"""





URGENT_KEYWORDS = [
    "fraud",
    "scam",
    "unauthorised transaction",
    "unauthorized transaction",
    "account hacked",
    "account compromised",
    "account stolen",
    "someone stole",
    "card stolen",
    "stolen card",
    "lost my card",
    "card is missing",
    "suspicious transaction",
    "transaction without my permission",
    "freeze my card",
    "block my card",
    "lock my card",
    "cancel my card",
    "disable my card",
    "someone has my card",
    "my account was hacked",
]


def is_urgent_security_question(message):
    text = message.lower()
    return any(keyword in text for keyword in URGENT_KEYWORDS)


def security_response():
    return (
        "**Important security guidance**\n\n"
        "If you suspect that your DBS/POSB banking details have been "
        "compromised, contact DBS immediately through its official "
        "24-hour fraud/scam/lost-card hotline:\n\n"
        "- **Singapore:** 1800 339 6963\n"
        "- **Overseas:** +65 6339 6963\n\n"
        "If you have shared your banking credentials or OTP, inform DBS "
        "and follow its instructions regarding the Safety Switch. "
        "For a lost or stolen card, use the official digibank app or "
        "website to block it, or contact the hotline.\n\n"
        "Do not click links or call numbers from suspicious messages. "
        "Never share your password, PIN or OTP in this chat.\n\n"
        "*FinAssist is an academic prototype. It cannot activate "
        "Safety Switch, block your card, report fraud or investigate "
        "a real transaction.*"
    )


# --------------------------------------------------
# 3. Define the tools the model can choose
# --------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_policies",
            "description": (
                "Search a limited knowledge base containing AI-assisted summaries "
                "of publicly available DBS Singapore webpages. "
                "Use this for DBS-related questions about cards, fees, transfers, "
                "fraud reporting, transaction disputes and banking procedures. "
                "The knowledge base is incomplete. Only answer using relevant "
                "retrieved passages and do not invent unsupported policy details."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": (
                            "The specific banking policy question "
                            "to search for."
                        ),
                    }
                },
                "required": ["question"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_transactions",
            "description": (
                "Retrieve transaction records for the currently selected demo customer. "
                "Use this tool whenever the user asks about their transactions, "
                "transaction history, or a specific transaction. "
                "IMPORTANT STATUS FILTERING RULES: "
                "If the user asks for pending transactions, set status to 'PENDING'. "
                "If the user asks for completed transactions, set status to 'COMPLETED'. "
                "If the user asks for failed transactions, set status to 'FAILED'. "
                "If the user asks for refunded transactions, set status to 'REFUNDED'. "
                "If the user asks for all or recent transactions without specifying "
                "a status, set status to null. "
                "If the user provides a transaction ID, pass it as transaction_id. "
                "Otherwise, set transaction_id to null. "
                "The customer ID is supplied separately by the application and must "
                "never be selected or changed by the model."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": ["string", "null"],
                        "description": (
                            "Transaction ID such as TXN1001. Use null "
                            "when the user asks for transaction history."
                        ),
                    },
                    "status": {
                        "type": ["string", "null"],
                        "enum": [
                            "PENDING",
                            "COMPLETED",
                            "FAILED",
                            "REFUNDED",
                            None,
                        ],
                        "description": (
                            "Optional transaction status filter. Use null "
                            "if no particular status was requested."
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": (
                            "Maximum number of history records to return, "
                            "from 1 to 10."
                        ),
                    },
                },
                "required": [
                    "transaction_id",
                    "status",
                    "limit",
                ],
                "additionalProperties": False,
            },
        },
    },
]


# --------------------------------------------------
# 4. Tool implementations
# --------------------------------------------------

def search_policies(question):
    results = rag.retrieve(question, k=TOP_K)

    relevant = [
        result
        for result in results
        if result["score"] >= MIN_SIMILARITY
    ]

    if not relevant:
        return {
            "found": False,
            "message": (
                "No sufficiently relevant policy passages were found. "
                "Do not invent a policy answer."
            ),
            "sources": [],
        }

    return {
        "found": True,
        "passages": [
            {
                "text": result["text"],
                "source": result["source"],
                "chunk_id": result["chunk_id"],
                "similarity": round(result["score"], 3),
            }
            for result in relevant
        ],
        "sources": [
            {
                "source": result["source"],
                "chunk_id": result["chunk_id"],
                "similarity": round(result["score"], 3),
            }
            for result in relevant
        ],
    }


def lookup_transactions_tool(
    transaction_id,
    status,
    limit,
    selected_customer_id,
):
    # IMPORTANT: customer identity comes from the UI, not the LLM.
    # The model cannot supply a different customer ID.

    customer_id = selected_customer_id

    if not customer_id:
        return {
            "found": False,
            "message": "No demo customer has been selected.",
        }

    limit = max(1, min(int(limit or 10), 10))

    if transaction_id:
        transaction_id = transaction_id.strip().upper()

        # Accept only IDs in the expected demonstration format.
        if not re.fullmatch(r"TXN\d{4}", transaction_id):
            return {
                "found": False,
                "message": (
                    "Invalid transaction ID format. "
                    "Expected an ID such as TXN1001."
                ),
            }

        transaction = lookup_transaction(
            transaction_id,
            customer_id,
        )

        if transaction is None:
            # Same response regardless of whether the ID does not exist
            # or belongs to a different customer.
            return {
                "found": False,
                "message": (
                    "The transaction could not be found for the selected "
                    "demo customer. Do not disclose whether it belongs "
                    "to another customer."
                ),
            }

        result = {
            "found": True,
            "transaction": transaction,
            "note": "This is a fictional demonstration record.",
        }

        if transaction["status"] == "FAILED":
            result["limitation"] = (
                "No failure reason is stored in the database. "
                "Do not infer or invent one."
            )

        return result

    transactions = get_customer_transactions(
        customer_id,
        status=status,
        limit=limit,
    )

    return {
        "found": bool(transactions),
        "transactions": transactions,
        "message": (
            "These are fictional records for the selected demo customer. "
            "Transaction history alone does not establish why a transaction "
            "succeeded or failed."
        ),
    }


def execute_tool(name, arguments, customer_id):
    if name == "search_policies":
        question = arguments.get("question", "").strip()

        if not question:
            return {"error": "A policy question is required."}

        return search_policies(question)

    if name == "lookup_transactions":
        return lookup_transactions_tool(
            transaction_id=arguments.get("transaction_id"),
            status=arguments.get("status"),
            limit=arguments.get("limit", 10),
            selected_customer_id=customer_id,
        )

    return {"error": "Unknown tool."}


# --------------------------------------------------
# 5. Source formatting
# --------------------------------------------------

def format_sources(sources):
    if not sources:
        return ""

    # Deduplicate citations if the model searches more than once.
    unique_sources = {}

    for source in sources:
        key = (source["source"], source["chunk_id"])
        unique_sources[key] = source

    lines = ["\n\n---\n**Retrieved policy sources**"]

    for source in unique_sources.values():
        lines.append(
            f"- `{source['source']}` "
            f"(chunk {source['chunk_id']}, "
            f"cosine similarity: {source['similarity']:.3f})"
        )

    lines.append(
        "\n*Similarity scores indicate retrieval relevance, "
        "not answer correctness.*"
    )

    return "\n".join(lines)


# --------------------------------------------------
# 6. Agent loop
# --------------------------------------------------


def respond(message, history, customer_id):
    trace = []

    if not message or not message.strip():
        return "Please enter a question.", "No question received."

    question = message.strip()

    # Log safety routing separately from LLM tool calling.
    if is_urgent_security_question(question):
        trace.append("ROUTE: Safety gate")
        trace.append("LLM called: No")
        trace.append("Tools executed: None")
        trace.append("Reason: Urgent security keyword detected.")
        return security_response(), "\n".join(trace)

    if not customer_id:
        trace.append("ROUTE: Blocked")
        trace.append("Reason: No demo customer selected.")
        return "Please select a demo customer first.", "\n".join(trace)

    trace.append(f"Selected demo customer: {customer_id}")
    trace.append("Starting LLM agent loop...")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]

    retrieved_sources = []
    tool_call_count = 0

    try:
        for round_number in range(1, MAX_TOOL_ROUNDS + 1):
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.2,
                max_tokens=1500,
            )

            assistant_message = response.choices[0].message

            trace.append(f"\n--- LLM round {round_number} ---")
            trace.append(f"Finish reason: {response.choices[0].finish_reason}")

            if not assistant_message.tool_calls:
                trace.append("Tool call requested: No")
                trace.append("LLM produced a final answer.")

                answer = assistant_message.content or (
                    "I couldn't generate an answer. Please try again."
                )

                trace.append(f"\nTotal tool calls executed: {tool_call_count}")

                if retrieved_sources:
                    trace.append("\nPolicy chunks retrieved:")
                    for source in retrieved_sources:
                        trace.append(
                            f"- {source['source']} | "
                            f"chunk {source['chunk_id']} | "
                            f"similarity {source['similarity']:.3f}"
                        )
                else:
                    trace.append("Policy retrieval: No policy chunks retrieved.")

                return (
                    answer + format_sources(retrieved_sources),
                    "\n".join(trace),
                )

            messages.append(
                assistant_message.model_dump(exclude_none=True)
            )

            for tool_call in assistant_message.tool_calls:
                tool_call_count += 1
                tool_name = tool_call.function.name
                raw_arguments = tool_call.function.arguments or "{}"

                trace.append(f"\nTOOL CALL #{tool_call_count}")
                trace.append(f"Selected tool: {tool_name}")
                trace.append(f"Raw arguments: {raw_arguments}")

                try:
                    arguments = json.loads(raw_arguments)

                    result = execute_tool(
                        tool_name,
                        arguments,
                        customer_id,
                    )

                    if tool_name == "search_policies":
                        retrieved_sources.extend(result.get("sources", []))

                        if result.get("found"):
                            trace.append("Tool result: SUCCESS")
                            trace.append(
                                f"Passages returned: "
                                f"{len(result.get('passages', []))}"
                            )
                        else:
                            trace.append("Tool result: NO RELEVANT PASSAGES")

                    elif tool_name == "lookup_transactions":
                        if result.get("error"):
                            trace.append("Tool result: ERROR")
                        elif result.get("found"):
                            trace.append("Tool result: MATCH FOUND")
                        else:
                            trace.append("Tool result: NO MATCH")

                        if "transaction" in result:
                            txn = result["transaction"]
                            trace.append(
                                f"Returned transaction ID: "
                                f"{txn['transaction_id']}"
                            )
                            trace.append(f"Status: {txn['status']}")

                        if "transactions" in result:
                            txns = result["transactions"]
                            trace.append(
                                f"Transactions returned: {len(txns)}"
                            )
                            trace.append(
                                "Returned IDs: "
                                + (
                                    ", ".join(
                                        t["transaction_id"] for t in txns
                                    )
                                    if txns else "None"
                                )
                            )
                    else:
                        trace.append("Tool result: UNKNOWN TOOL")

                except (ValueError, TypeError, KeyError) as exc:
                    trace.append(
                        f"Tool argument error: {type(exc).__name__}"
                    )
                    result = {
                        "error": (
                            "Invalid tool arguments. Do not invent results."
                        )
                    }

                except Exception as exc:
                    trace.append(
                        f"Tool execution error: {type(exc).__name__}: {exc}"
                    )
                    result = {
                        "error": (
                            "The tool failed. Explain that the request "
                            "could not be completed."
                        )
                    }

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(
                        result,
                        ensure_ascii=False,
                        default=str,
                    ),
                })

        trace.append("Stopped: Maximum tool-call rounds reached.")
        return (
            "I couldn't complete the request within the tool-call limit. "
            "Please try a more specific question.",
            "\n".join(trace),
        )

    except Exception as exc:
        trace.append(f"AGENT ERROR: {type(exc).__name__}: {exc}")
        print(f"FinAssist error: {type(exc).__name__}: {exc}")

        return (
            "I'm temporarily unable to process your request. "
            "Please try again shortly.",
            "\n".join(trace),
        )



# --------------------------------------------------
# 7. FinAssist UI — polished banking dashboard
# --------------------------------------------------

APP_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,600&display=swap');
 
/* ---------- Colour tokens (also forces readable Gradio defaults) ---------- */
.gradio-container,
.dark .gradio-container {
    --fa-navy: #0e2236;
    --fa-navy-2: #17324b;
    --fa-teal: #0f766e;
    --fa-teal-bright: #5eead4;
    --fa-text: #0f172a;
    --fa-text-soft: #475569;
    --fa-line: #d9e2ea;
 
    --body-text-color: #0f172a;
    --body-text-color-subdued: #475569;
    --body-background-fill: #e8eef3;
    --background-fill-primary: #ffffff;
    --background-fill-secondary: #f1f5f9;
    --block-background-fill: transparent;
    --block-border-color: transparent;
    --block-border-width: 0px;
    --block-shadow: none;
    --block-label-text-color: #334155;
    --block-title-text-color: #334155;
    --block-info-text-color: #475569;
    --input-background-fill: #ffffff;
    --input-border-color: #b8c4d0;
    --input-shadow: none;
    --border-color-primary: #d9e2ea;
    --color-accent: #0f766e;
    --color-accent-soft: #d7f0eb;
    --button-primary-background-fill: #0f766e;
    --button-primary-background-fill-hover: #0b5e57;
    --button-primary-text-color: #ffffff;
    --button-secondary-background-fill: #f1f5f9;
    --button-secondary-background-fill-hover: #e2ebf2;
    --button-secondary-text-color: #0f172a;
    --button-secondary-border-color: #d9e2ea;
 
    /* Examples table */
    --table-even-background-fill: #ffffff;
    --table-odd-background-fill: #f6f9fb;
    --table-row-focus: #d7f0eb;
    --table-border-color: #d9e2ea;
 
    background: #e8eef3 !important;
    color: #0f172a;
    color-scheme: light;
    font-family: "Instrument Sans", system-ui, -apple-system, "Segoe UI", sans-serif !important;
    max-width: 1180px !important;
    margin: 0 auto !important;
}
footer { display: none !important; }
 
/* ---------- The shell: one rounded card that clips its children ---------- */
#fa-shell {
    gap: 0 !important;
    margin-top: 24px;
    background: #ffffff !important;
    border: 1px solid var(--fa-line) !important;
    border-radius: 22px !important;
    overflow: hidden !important;
    box-shadow: 0 18px 40px -24px rgba(14, 34, 54, 0.45) !important;
}
 
/* Make every nested Gradio wrapper invisible so nothing paints a square */
#fa-shell .block,
#fa-shell .form,
#fa-shell .styler,
#fa-shell .gr-group,
#fa-shell .html-container,
#fa-shell .wrap-inner {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
 
/* ---------- Sidebar ---------- */
#fa-rail {
    background: var(--fa-navy) !important;
    padding: 30px 26px !important;
    gap: 22px !important;
    min-width: 290px !important;
    border-radius: 0 !important;
}
#fa-rail .block, #fa-rail .html-container { padding: 0 !important; }
 
.fa-brand { display: flex; align-items: center; gap: 12px; }
.fa-mark {
    width: 40px; height: 40px; border-radius: 12px;
    background: var(--fa-teal-bright); color: var(--fa-navy);
    display: grid; place-items: center;
    font-family: "Newsreader", Georgia, serif;
    font-size: 24px; font-weight: 600;
}
.fa-brand-name {
    font-family: "Newsreader", Georgia, serif;
    font-size: 26px; font-weight: 600; line-height: 1.05;
    color: #ffffff; letter-spacing: -0.3px;
}
.fa-brand-sub { font-size: 13px; color: #b9cadb; margin-top: 3px; }
 
.fa-rail-title { font-size: 14px; font-weight: 600; color: #ffffff; margin: 0 0 4px; }
.fa-rail-note  { font-size: 13px; color: #c3d2e0; line-height: 1.55; margin: 0 0 10px; }
 
/* Dropdown on a dark background: light label text, white input, dark text */
#fa-customer label span,
#fa-customer [data-testid="block-info"],
#fa-customer .block-title {
    color: #ffffff !important;
    background: transparent !important;
    font-weight: 600 !important;
}
#fa-customer .info, #fa-customer span.info { color: #c3d2e0 !important; }
#fa-customer input {
    background: #ffffff !important;
    color: #0f172a !important;
    border: 1px solid #ffffff !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
}
 
.fa-abilities { list-style: none; margin: 0; padding: 0; display: grid; gap: 14px; }
.fa-abilities li { color: #ffffff; font-size: 14px; font-weight: 600; padding-left: 14px; border-left: 3px solid var(--fa-teal-bright); line-height: 1.4; }
.fa-abilities li span { display: block; font-weight: 400; font-size: 13px; color: #c3d2e0; margin-top: 2px; line-height: 1.5; }
 
.fa-limits {
    margin-top: auto;
    background: var(--fa-navy-2);
    border-radius: 14px;
    padding: 14px 16px;
    font-size: 13px; line-height: 1.55; color: #e5edf5;
}
.fa-limits strong { color: #ffffff; }
 
/* ---------- Chat area ---------- */
#fa-main {
    background: #ffffff !important;
    padding: 28px 30px 26px !important;
    gap: 14px !important;
    border-radius: 0 !important;
}
.fa-head h2 {
    font-family: "Newsreader", Georgia, serif !important;
    font-size: 30px; font-weight: 600; letter-spacing: -0.5px;
    color: var(--fa-text); margin: 0 0 6px;
}
.fa-head p { color: var(--fa-text-soft); font-size: 15px; line-height: 1.6; margin: 0; max-width: 560px; }
 
/* Chat history: one clean panel */
#fa-main .bubble-wrap, #fa-main [role="log"] {
    background: #ffffff !important;
    border-radius: 16px !important;
}
#fa-main .message {
    border-radius: 14px !important;
    box-shadow: none !important;
    font-size: 15px; line-height: 1.6;
    color: #0f172a !important;
}
/* Bot = white with border, user = light teal. Both use dark text. */
#fa-main .bot .message, #fa-main .message.bot, #fa-main [data-testid="bot"] {
    background: #F2F0EF !important;
    border: 0px solid #d9e2ea !important;
}
#fa-main .user .message, #fa-main .message.user, #fa-main [data-testid="user"] {
    background: #d7f0eb !important;
    border: 0px solid #a8dcd2 !important;
}
#fa-main .message *, #fa-main .prose, #fa-main .prose * { color: #0f172a; }
#fa-main .message code { background: #eef2f6; color: #0f172a; border-radius: 6px; padding: 1px 5px; }
 
/* Chatbot empty-state text and icon */
#fa-main .placeholder-content,
#fa-main .placeholder-content *,
#fa-main .placeholder,
#fa-main .empty,
#fa-main .empty * {
    color: #334155 !important;
}
#fa-main .placeholder-content svg,
#fa-main .empty svg {
    stroke: #334155 !important;
}
 
/* Input */
#fa-main textarea, #fa-main input[type="text"] {
    background: #ffffff !important;
    color: #0f172a !important;
    border: 1px solid #b8c4d0 !important;
    border-radius: 12px !important;
    box-shadow: none !important;
}
#fa-main textarea::placeholder { color: #64748b !important; }
#fa-main textarea:focus, #fa-main input[type="text"]:focus {
    border-color: var(--fa-teal) !important;
    box-shadow: 0 0 0 3px rgba(15, 118, 110, 0.2) !important;
    outline: none !important;
}
 
/* Buttons */
#fa-main button { border-radius: 10px !important; font-weight: 600 !important; box-shadow: none !important; }
#fa-main button.primary, #fa-main .submit-button {
    background: var(--fa-teal) !important; border: 1px solid var(--fa-teal) !important; color: #ffffff !important;
}
#fa-main button.secondary {
    background: #f1f5f9 !important; border: 1px solid #d9e2ea !important; color: #0f172a !important;
}
#fa-main button.secondary:hover { background: #d7f0eb !important; border-color: #a8dcd2 !important; }
 
/* Example questions table */
#fa-main .table-wrap {
    background: transparent !important;
    border: 1px solid #d9e2ea !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}
#fa-main table { background: #ffffff !important; font-size: 13.5px; }
#fa-main table th {
    background: #e8eef3 !important;
    color: #0f172a !important;
    font-weight: 600 !important;
}
#fa-main table td { background: #ffffff !important; color: #0f172a !important; }
#fa-main table tr:hover td { background: #d7f0eb !important; }
#fa-main .gallery, #fa-main .examples { color: #0f172a !important; }
#fa-main .label-wrap, #fa-main .examples-label { color: #475569 !important; }
 
/* ---------- Developer trace ---------- */
#fa-trace {
    margin-top: 16px;
    background: #ffffff !important;
    border: 1px solid var(--fa-line) !important;
    border-radius: 16px !important;
    overflow: hidden !important;
}
#fa-trace .block, #fa-trace .form { background: transparent !important; border: none !important; box-shadow: none !important; }
#fa-trace button.label-wrap, #fa-trace .label-wrap { color: #0f172a !important; font-weight: 600 !important; }
#fa-trace textarea {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace !important;
    font-size: 12.5px !important; line-height: 1.6 !important;
    background: #f1f5f9 !important; color: #0f172a !important;
    border: 1px solid #d9e2ea !important; border-radius: 10px !important;
}
 
/* ---------- Footer ---------- */
#fa-footer { text-align: center; color: #475569; font-size: 12.5px; line-height: 1.7; padding: 18px 12px 30px; }
 
/* ---------- Keyboard focus ---------- */
.gradio-container button:focus-visible { outline: 2px solid var(--fa-teal) !important; outline-offset: 2px; }
 
/* ---------- Mobile ---------- */
@media (max-width: 860px) {
    #fa-shell { flex-direction: column !important; border-radius: 18px !important; margin-top: 12px; }
    #fa-rail, #fa-main { min-width: 100% !important; padding: 22px 18px !important; }
    .fa-head h2 { font-size: 25px; }
}
"""
 
BRAND_HTML = """
<div class="fa-brand">
    <div class="fa-mark">F</div>
    <div>
        <div class="fa-brand-name">FinAssist</div>
        <div class="fa-brand-sub">Banking support demo</div>
    </div>
</div>
"""
 
CUSTOMER_HTML = """
<div class="fa-rail-title">Choose a demo customer</div>
<p class="fa-rail-note">Transaction lookups only return records for the customer selected here.</p>
"""
 
ABILITIES_HTML = """
<div class="fa-rail-title" style="margin-bottom:12px">What you can ask</div>
<ul class="fa-abilities">
    <li>DBS information
        <span>Selected public information on fees, cards, transfers and disputes.</span></li>
    <li>Transaction lookups
        <span>Search synthetic demo transactions by ID or view recent and pending records.</span></li>
</ul>
"""
 
LIMITS_HTML = """
<div class="fa-limits">
    <strong>Academic prototype.</strong>
    DBS information is based on selected public sources.
    Demo transactions are synthetic. This is not an official DBS service
    and cannot access accounts or perform banking actions.
</div>
"""
 
HEAD_HTML = """
<div class="fa-head">
    <h2>How can we help today?</h2>
    <p>Ask about selected DBS banking information, or look up synthetic
    transactions for the demo customer selected. Try an example below
    to get started.</p>
</div>
"""
 
FOOTER_HTML = """
<div id="fa-footer">
    Independent academic prototype. DBS information is based on selected
    publicly available sources; transaction records are synthetic.
    Not affiliated with DBS and not connected to real bank accounts
    or payment systems.
</div>
"""
 
EXAMPLES = [
    ["What should I do if I shared my banking OTP?", "CUST001"],
    ["How do I block a lost DBS credit card?", "CUST001"],
    ["Can DBS cancel a pending card transaction?", "CUST001"],
    ["What fees apply to overseas DBS debit card transactions?", "CUST001"],
    ["Show my pending transactions.", "CUST001"],
    ["Find transaction TXN1001.", "CUST001"],
]
 
with gr.Blocks(
    title="FinAssist | Banking support demo",
    elem_id="fa-app",
) as demo:
 
    with gr.Row(elem_id="fa-shell", equal_height=True):
 
        # ---------- Sidebar ----------
        with gr.Column(scale=1, min_width=290, elem_id="fa-rail"):
            gr.HTML(BRAND_HTML)
 
            gr.HTML(CUSTOMER_HTML)
            customer_dropdown = gr.Dropdown(
                choices=[
                    ("Demo Customer 1 (CUST001)", "CUST001"),
                    ("Demo Customer 2 (CUST002)", "CUST002"),
                    ("Demo Customer 3 (CUST003)", "CUST003"),
                    ("Demo Customer 4 (CUST004)", "CUST004"),
                    ("Demo Customer 5 (CUST005)", "CUST005"),
                    ("Demo Customer 6 (CUST006)", "CUST006"),
                    ("Demo Customer 7 (CUST007)", "CUST007"),
                    ("Demo Customer 8 (CUST008)", "CUST008"),
                    ("Demo Customer 9 (CUST009)", "CUST009"),
                    ("Demo Customer 10 (CUST010)", "CUST010"),
                ],
                value="CUST001",
                label="Active customer",
                interactive=True,
                elem_id="fa-customer",
            )
 
            gr.HTML(ABILITIES_HTML)
            gr.HTML(LIMITS_HTML)
 
        # ---------- Chat ----------
        with gr.Column(scale=2, min_width=420, elem_id="fa-main"):
            gr.HTML(HEAD_HTML)
 
            # Defined before ChatInterface so it can receive the trace.
            # It is rendered inside the accordion further down.
            trace_box = gr.Textbox(
                label="Tool calls, lookups and retrieved chunks",
                lines=12,
                max_lines=24,
                interactive=False,
                render=False,
            )
 
            gr.ChatInterface(
                fn=respond,
                chatbot=gr.Chatbot(
                    height=440,
                    placeholder="Your conversation will appear here.",
                ),
                additional_inputs=[customer_dropdown],
                additional_outputs=[trace_box],
                examples=EXAMPLES,
                cache_examples=False,
            )
 
    with gr.Accordion(
        "Developer view: agent trace",
        open=False,
        elem_id="fa-trace",
    ):
        trace_box.render()
 
    gr.HTML(FOOTER_HTML)
 
    # Keep the page in light mode so text colours stay readable.
    demo.load(
        fn=None,
        js="() => { document.body.classList.remove('dark'); }",
    )
 
 
if __name__ == "__main__":
    demo.launch(
        theme=gr.themes.Base(
            primary_hue="teal",
            secondary_hue="slate",
            neutral_hue="slate",
            font=[
                gr.themes.GoogleFont("Instrument Sans"),
                "system-ui",
                "sans-serif",
            ],
        ),
        css=APP_CSS,
    )