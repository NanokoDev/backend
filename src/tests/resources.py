import json
from httpx import Response, Request


format_response = Response(
    status_code=200,
    headers={
        "apim-request-id": "REDACTED",
        "azureml-model-session": "mock-session-id",
        "azureml-served-by-cluster": "mock-cluster",
        "cmp-upstream-response-duration": "1234",
        "content-type": "application/json",
        "date": "Tue, 01 Jan 2030 00:00:00 GMT",
        "ms-azureml-model-time": "1234",
        "request-context": "appId=",
        "server": "mock-server",
        "strict-transport-security": "max-age=31536000; includeSubDomains; preload",
        "vary": "Origin, Accept-Encoding",
        "x-content-type-options": "nosniff",
        "x-ms-client-request-id": "Not-Set",
        "x-ms-deployment-name": "mock-deployment",
        "x-ms-rai-invoked": "true",
        "x-ms-region": "mock-region",
        "x-ratelimit-limit-requests": "1000",
        "x-ratelimit-limit-tokens": "1000000",
        "x-ratelimit-remaining-requests": "999",
        "x-ratelimit-remaining-tokens": "999999",
        "x-request-id": "REDACTED",
        "x-request-time": "1.234",
        "content-length": "1234",
        "x-github-backend": "mock-backend",
        "x-github-request-id": "REDACTED",
    },
    json={
        "choices": [
            {
                "content_filter_results": {
                    "hate": {"filtered": False, "severity": "safe"},
                    "self_harm": {"filtered": False, "severity": "safe"},
                    "sexual": {"filtered": False, "severity": "safe"},
                    "violence": {"filtered": False, "severity": "safe"},
                },
                "finish_reason": "stop",
                "index": 0,
                "logprobs": None,
                "message": {
                    "annotations": [],
                    "content": '{"comment":"Great job! You correctly identified that 2 + 2 equals 4.","performance":4}',
                    "refusal": None,
                    "role": "assistant",
                },
            }
        ],
        "created": 9999999999,
        "id": "chatcmpl-REDACTED",
        "model": "gpt-mock-model",
        "object": "chat.completion",
        "prompt_filter_results": [
            {
                "prompt_index": 0,
                "content_filter_results": {
                    "hate": {"filtered": False, "severity": "safe"},
                    "jailbreak": {"filtered": False, "detected": False},
                    "self_harm": {"filtered": False, "severity": "safe"},
                    "sexual": {"filtered": False, "severity": "safe"},
                    "violence": {"filtered": False, "severity": "safe"},
                },
            }
        ],
        "system_fingerprint": "mock-fingerprint",
        "usage": {
            "completion_tokens": 32,
            "completion_tokens_details": {
                "accepted_prediction_tokens": 0,
                "audio_tokens": 0,
                "reasoning_tokens": 0,
                "rejected_prediction_tokens": 0,
            },
            "prompt_tokens": 230,
            "prompt_tokens_details": {"audio_tokens": 0, "cached_tokens": 0},
            "total_tokens": 262,
        },
    },
)

text_response = Response(
    status_code=200,
    headers={
        "apim-request-id": "REDACTED",
        "azureml-model-session": "mock-session-id",
        "azureml-served-by-cluster": "mock-cluster",
        "cmp-upstream-response-duration": "567",
        "content-type": "application/json",
        "date": "Tue, 01 Jan 2030 00:00:00 GMT",
        "ms-azureml-model-time": "567",
        "request-context": "appId=",
        "server": "mock-server",
        "strict-transport-security": "max-age=31536000; includeSubDomains; preload",
        "vary": "Origin, Accept-Encoding",
        "x-content-type-options": "nosniff",
        "x-ms-client-request-id": "Not-Set",
        "x-ms-deployment-name": "mock-deployment",
        "x-ms-rai-invoked": "true",
        "x-ms-region": "mock-region",
        "x-ratelimit-limit-requests": "1000",
        "x-ratelimit-limit-tokens": "1000000",
        "x-ratelimit-remaining-requests": "998",
        "x-ratelimit-remaining-tokens": "999000",
        "x-request-id": "REDACTED",
        "x-request-time": "0.567",
        "content-length": "1234",
        "x-github-backend": "mock-backend",
        "x-github-request-id": "REDACTED",
    },
    json={
        "choices": [
            {
                "content_filter_results": {
                    "hate": {"filtered": False, "severity": "safe"},
                    "self_harm": {"filtered": False, "severity": "safe"},
                    "sexual": {"filtered": False, "severity": "safe"},
                    "violence": {"filtered": False, "severity": "safe"},
                },
                "finish_reason": "stop",
                "index": 0,
                "logprobs": None,
                "message": {
                    "annotations": [],
                    "content": "Think about what it means to put two groups of things together and count how many there are in total.",
                    "refusal": None,
                    "role": "assistant",
                },
            }
        ],
        "created": 9999999999,
        "id": "chatcmpl-REDACTED",
        "model": "gpt-mock-model",
        "object": "chat.completion",
        "prompt_filter_results": [
            {
                "prompt_index": 0,
                "content_filter_results": {
                    "hate": {"filtered": False, "severity": "safe"},
                    "jailbreak": {"filtered": False, "detected": False},
                    "self_harm": {"filtered": False, "severity": "safe"},
                    "sexual": {"filtered": False, "severity": "safe"},
                    "violence": {"filtered": False, "severity": "safe"},
                },
            }
        ],
        "system_fingerprint": "mock-fingerprint",
        "usage": {
            "completion_tokens": 22,
            "completion_tokens_details": {
                "accepted_prediction_tokens": 0,
                "audio_tokens": 0,
                "reasoning_tokens": 0,
                "rejected_prediction_tokens": 0,
            },
            "prompt_tokens": 197,
            "prompt_tokens_details": {"audio_tokens": 0, "cached_tokens": 0},
            "total_tokens": 219,
        },
    },
)


def llm_api_callback(request: Request):
    """Callback for the LLM API mock"""
    data = json.loads(request.content)

    if data.get("response_format", {}).get("type") == "json_schema":
        return format_response
    else:
        return text_response
