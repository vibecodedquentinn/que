from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI

from app.config import settings
from app.fallback import fallback_reply
from app.memory import append_message, get_recent_messages
from app.prompts import system_prompt
from app.intent_router import route_intent
from app.quick_replies import try_quick_reply
from app.response_style import format_tool_turn
from app.tools.registry import get_tool_definitions, run_tool

MAX_TOOL_ROUNDS = 6

_FACTUAL = re.compile(
    r"\b(uhr|zeit|wetter|temperatur|gerät|licht|schalt|grad|erinner|notiz|"
    r"spät|datum|regen|warm|kalt)\b",
    re.I,
)


def _client() -> AsyncOpenAI | None:
    if not settings.llm_configured:
        return None
    api_key = settings.effective_llm_api_key or "ollama-local"
    return AsyncOpenAI(
        api_key=api_key,
        base_url=settings.effective_llm_base_url or None,
    )


def _llm_kwargs() -> dict[str, Any]:
    kw: dict[str, Any] = {
        "temperature": settings.llm_temperature,
    }
    if settings.llm_max_tokens:
        kw["max_tokens"] = settings.llm_max_tokens
    return kw


async def _synthesize_from_tool(
    client: AsyncOpenAI,
    user_message: str,
    tool_name: str,
    tool_result: str,
) -> str:
    prompt = (
        "Formuliere die Antwort für den Nutzer in 1–3 Sätzen auf Deutsch, "
        "Jürgen-Stil (ruhig, trocken, präzise). Nur Fakten aus dem Tool-Ergebnis."
    )
    resp = await client.chat.completions.create(
        model=settings.effective_llm_model,
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"Nutzer: {user_message}\nTool: {tool_name}\nErgebnis:\n{tool_result}",
            },
        ],
        stream=False,
        **_llm_kwargs(),
    )
    text = (resp.choices[0].message.content or "").strip()
    return text or "Erledigt."


async def chat_once(session_id: str, user_message: str) -> str:
    chunks: list[str] = []
    async for part in chat_stream(session_id, user_message):
        if part["type"] == "text":
            chunks.append(part["content"])
        elif part["type"] == "error":
            return part["content"]
    return "".join(chunks)


async def chat_stream(session_id: str, user_message: str) -> AsyncIterator[dict[str, Any]]:
    await append_message(session_id, "user", user_message)

    routed = await route_intent(session_id, user_message)
    if routed:
        await append_message(session_id, "assistant", routed)
        yield {"type": "text", "content": routed}
        yield {"type": "done"}
        return

    quick = await try_quick_reply(user_message)
    if quick:
        await append_message(session_id, "assistant", quick)
        yield {"type": "text", "content": quick}
        yield {"type": "done"}
        return

    client = _client()
    if client is None:
        reply = await fallback_reply(session_id, user_message)
        await append_message(session_id, "assistant", reply)
        yield {"type": "text", "content": reply}
        yield {"type": "done"}
        return

    history = await get_recent_messages(session_id, limit=24)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system_prompt()},
        *history,
    ]

    tools = get_tool_definitions()
    tool_choice: Any = "auto"
    if _FACTUAL.search(user_message):
        tool_choice = "required"

    for _ in range(MAX_TOOL_ROUNDS):
        stream = await client.chat.completions.create(
            model=settings.effective_llm_model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            stream=True,
            **_llm_kwargs(),
        )
        tool_choice = "auto"

        tool_calls: dict[int, dict[str, Any]] = {}
        assistant_text = ""

        async for chunk in stream:
            choice = chunk.choices[0]
            delta = choice.delta

            if delta.content:
                assistant_text += delta.content
                yield {"type": "text", "content": delta.content}

            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index
                    if idx not in tool_calls:
                        tool_calls[idx] = {
                            "id": tc.id or "",
                            "name": "",
                            "arguments": "",
                        }
                    if tc.id:
                        tool_calls[idx]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            tool_calls[idx]["name"] = tc.function.name
                        if tc.function.arguments:
                            tool_calls[idx]["arguments"] += tc.function.arguments

            if choice.finish_reason == "tool_calls":
                ordered = [tool_calls[i] for i in sorted(tool_calls.keys())]
                assistant_msg: dict[str, Any] = {
                    "role": "assistant",
                    "content": assistant_text or None,
                    "tool_calls": [
                        {
                            "id": t["id"],
                            "type": "function",
                            "function": {
                                "name": t["name"],
                                "arguments": t["arguments"] or "{}",
                            },
                        }
                        for t in ordered
                    ],
                }
                messages.append(assistant_msg)
                if assistant_text:
                    await append_message(session_id, "assistant", assistant_text)

                last_result = ""
                last_name = ""
                guest_action = ""
                for t in ordered:
                    yield {
                        "type": "tool_start",
                        "name": t["name"],
                    }
                    result = await run_tool(t["name"], t["arguments"] or "{}")
                    last_name = t["name"]
                    last_result = result
                    if last_name == "fritz_guest_wifi":
                        try:
                            args = json.loads(t["arguments"] or "{}")
                            guest_action = args.get("action", "on")
                        except json.JSONDecodeError:
                            guest_action = "on"
                    yield {"type": "tool_end", "name": t["name"], "result": result}
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": t["id"],
                            "content": result,
                        }
                    )

                formatted = format_tool_turn(
                    last_name, last_result, guest_action=guest_action
                )
                if not formatted:
                    formatted = await _synthesize_from_tool(
                        client, user_message, last_name, last_result
                    )
                await append_message(session_id, "assistant", formatted)
                yield {"type": "text", "content": formatted}
                yield {"type": "done"}
                return

            if choice.finish_reason == "stop":
                final = assistant_text.strip()
                if not final:
                    fb = await fallback_reply(session_id, user_message)
                    if fb:
                        final = fb
                        yield {"type": "text", "content": fb}
                if final:
                    await append_message(session_id, "assistant", final)
                yield {"type": "done"}
                return

        else:
            continue
        continue

    yield {
        "type": "error",
        "content": "Zu viele Tool-Schritte — bitte Anfrage vereinfachen.",
    }
    yield {"type": "done"}
