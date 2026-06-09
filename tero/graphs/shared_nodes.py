from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
import json

def summarize_conversation(summary, messages) -> dict:
    """
    Update the conversation summary:
    - Takes old summary if any
    - Adds in the last few human + AI messages
    - Produces a concise new summary
    """

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a summarizer that maintains a running digest of the discussion."),
        ("system", "Existing summary (may be empty): {existing_summary}"),
        MessagesPlaceholder("recent_msgs"),
        ("system", "Update the summary to include the new details from recent messages. "
                   "Keep it concise, factual, and cumulative.")
    ])

    chain = prompt | llm | RunnableLambda(lambda out: {"output": out.content})

    result = chain.invoke({"existing_summary": summary, "recent_msgs": messages})
    new_summary = result["output"]

    return new_summary

# Prompt template for generating JSON reflections of prior conversations
reflection_prompt_template = """
You are analyzing conversations about research papers to create memories that will help guide future interactions. Your task is to extract key elements that would be most helpful when encountering similar academic discussions in the future.

Review the conversation and create a memory reflection following these rules:

1. For any field where you don't have enough information or the field isn't relevant, use "N/A"
2. Be extremely concise - each string should be one clear, actionable sentence
3. Focus only on information that would be useful for handling similar future conversations
4. Context_tags should be specific enough to match similar situations but general enough to be reusable

Output valid JSON in exactly this format:
{
    "context_tags": [              // 2-4 keywords that would help identify similar future conversations
        string,                    // Use field-specific terms like "deep_learning", "methodology_question", "results_interpretation"
        ...
    ],
    "conversation_summary": string, // One sentence describing what the conversation accomplished
    "what_worked": string,         // Most effective approach or strategy used in this conversation
    "what_to_avoid": string        // Most important pitfall or ineffective approach to avoid
}

Examples:
- Good context_tags: ["transformer_architecture", "attention_mechanism", "methodology_comparison"]
- Bad context_tags: ["machine_learning", "paper_discussion", "questions"]

- Good conversation_summary: "Explained how the attention mechanism in the BERT paper differs from traditional transformer architectures"
- Bad conversation_summary: "Discussed a machine learning paper"

- Good what_worked: "Using analogies from matrix multiplication to explain attention score calculations"
- Bad what_worked: "Explained the technical concepts well"

- Good what_to_avoid: "Diving into mathematical formulas before establishing user's familiarity with linear algebra fundamentals"
- Bad what_to_avoid: "Used complicated language"

Additional examples for different research scenarios:

Context tags examples:
- ["experimental_design", "control_groups", "methodology_critique"]
- ["statistical_significance", "p_value_interpretation", "sample_size"]
- ["research_limitations", "future_work", "methodology_gaps"]

Conversation summary examples:
- "Clarified why the paper's cross-validation approach was more robust than traditional hold-out methods"
- "Helped identify potential confounding variables in the study's experimental design"

What worked examples:
- "Breaking down complex statistical concepts using visual analogies and real-world examples"
- "Connecting the paper's methodology to similar approaches in related seminal papers"

What to avoid examples:
- "Assuming familiarity with domain-specific jargon without first checking understanding"
- "Over-focusing on mathematical proofs when the user needed intuitive understanding"

Do not include any text outside the JSON object in your response.

Here is the prior conversation:

{conversation}
"""


def _stringify_conversation(conversation):
    """Turn a list of LangChain messages or a raw string into a plain text transcript.
    Roles are uppercased (HUMAN/AI/SYSTEM/etc.)."""
    if isinstance(conversation, str):
        return conversation
    parts = []
    try:
        for m in conversation:
            role = getattr(m, "type", None) or getattr(m, "role", None) or m.__class__.__name__
            content = getattr(m, "content", str(m))
            parts.append(f"{str(role).upper()}: {content}")
    except Exception:
        # Fallback to a direct str() if we can't iterate messages cleanly
        return str(conversation)
    return "\n\n".join(parts)


def reflect_conversation(conversation, messages, prompt_template: str = reflection_prompt_template) -> dict:
    """Generate a compact JSON reflection of a prior conversation.

    Args:
        conversation: Either a list of LangChain BaseMessage objects or a raw string transcript.
        prompt_template: System prompt that enforces a strict JSON schema.

    Returns:
        dict: Parsed JSON with keys: context_tags, conversation_summary, what_worked, what_to_avoid.
              If parsing fails, returns a minimal schema with "N/A" defaults.
    """
    transcript = _stringify_conversation(conversation)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_messages([
        ("system", prompt_template),
        ("human", "{conversation}")
    ])

    # Run the LLM and capture the raw JSON string
    chain = prompt | llm | RunnableLambda(lambda out: out.content)
    raw_output = chain.invoke({"conversation": transcript})

    # Robust JSON parsing with fallback to extract the first JSON block
    def _parse_json(s: str) -> dict:
        try:
            return json.loads(s)
        except Exception:
            start = s.find("{")
            end = s.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(s[start:end + 1])
                except Exception:
                    pass
            # Fallback schema if the model adds extra text despite instructions
            return {
                "context_tags": [],
                "conversation_summary": "N/A",
                "what_worked": "N/A",
                "what_to_avoid": "N/A",
            }

    return _parse_json(raw_output)