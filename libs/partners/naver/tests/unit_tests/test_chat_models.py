"""Test chat model integration."""
import json
import os
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic.v1 import SecretStr

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)

from langchain_naver import ChatNaver
from langchain_naver.chat_models import (
    _convert_naver_chat_message_to_message,
    _convert_message_to_naver_chat_message
)

os.environ["NCP_CLOVASTUDIO_API_KEY"] = "test_api_key"
os.environ["NCP_APIGW_API_KEY"] = "test_gw_key"


def test_initialization_api_key() -> None:
    """Test chat model initialization."""
    chat_model = ChatNaver(clovastudio_api_key="foo", apigw_api_key="bar")
    assert cast(SecretStr, chat_model.ncp_clovastudio_api_key).get_secret_value() == "foo"
    assert cast(SecretStr, chat_model.ncp_apigw_api_key).get_secret_value() == "bar"


def test_initialization_model_name() -> None:
    llm = ChatNaver(model="HCX-DASH-001")
    assert llm.model_name == "HCX-DASH-001"
    llm = ChatNaver(model_name="HCX-DASH-001")
    assert llm.model_name == "HCX-DASH-001"


def test_convert_dict_to_message_human() -> None:
    message = {"role": "user", "content": "foo"}
    result = _convert_naver_chat_message_to_message(message)
    expected_output = HumanMessage(content="foo")
    assert result == expected_output
    assert _convert_message_to_naver_chat_message(expected_output) == message


def test_convert_dict_to_message_ai() -> None:
    message = {"role": "assistant", "content": "foo"}
    result = _convert_naver_chat_message_to_message(message)
    expected_output = AIMessage(content="foo")
    assert result == expected_output
    assert _convert_message_to_naver_chat_message(expected_output) == message


def test_convert_dict_to_message_system() -> None:
    message = {"role": "system", "content": "foo"}
    result = _convert_naver_chat_message_to_message(message)
    expected_output = SystemMessage(content="foo")
    assert result == expected_output
    assert _convert_message_to_naver_chat_message(expected_output) == message


@pytest.fixture
def mock_chat_completion_response() -> dict:
    return {
        "status": {
            "code": "20000",
            "message": "OK"
        },
        "result": {
            "message": {
                "role": "assistant",
                "content": "Phrases: Record what happened today and prepare for tomorrow. "
                           "The diary will make your life richer."
            },
            "stopReason": "LENGTH",
            "inputLength": 100,
            "outputLength": 10,
            "aiFilter": [
                {
                    "groupName": "curse",
                    "name": "insult",
                    "score": "1"
                },
                {
                    "groupName": "curse",
                    "name": "discrimination",
                    "score": "0"
                },
                {
                    "groupName": "unsafeContents",
                    "name": "sexualHarassment",
                    "score": "2"
                }
            ]
        }
    }


def test_naver_invoke(mock_chat_completion_response: dict) -> None:
    llm = ChatNaver()
    completed = False

    def mock_completion_with_retry(*args: Any, **kwargs: Any) -> Any:
        nonlocal completed
        completed = True
        return mock_chat_completion_response

    with (patch.object(ChatNaver, '_completion_with_retry', mock_completion_with_retry)):
        res = llm.invoke("Let's test it.")
        assert res.content == \
               "Phrases: Record what happened today and prepare for tomorrow. The diary will make your life richer."
    assert completed


async def test_naver_ainvoke(mock_chat_completion_response: dict) -> None:
    llm = ChatNaver()
    completed = False

    async def mock_acompletion_with_retry(*args: Any, **kwargs: Any) -> Any:
        nonlocal completed
        completed = True
        return mock_chat_completion_response

    with patch.object(ChatNaver, "_acompletion_with_retry", mock_acompletion_with_retry):
        res = await llm.ainvoke("Let's test it.")
        assert res.content == \
               "Phrases: Record what happened today and prepare for tomorrow. The diary will make your life richer."
    assert completed
