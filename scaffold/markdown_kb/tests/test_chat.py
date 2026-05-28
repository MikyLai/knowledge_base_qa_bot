import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import indexer

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def build_index():
    """Build the index once before all tests in this module."""
    client.post("/index")


class TestChatGrounded:
    def test_refund_question_cites_correct_source(self):
        response = client.post("/chat", json={"query": "How long do refunds take?"})

        assert response.status_code == 200
        body = response.json()
        source_ids = [s["source"] for s in body["sources"]]
        assert any("refund_policy.md" in sid for sid in source_ids), (
            f"Expected refund_policy.md in sources, got: {source_ids}"
        )
        assert "refund_policy.md#refund-timeline" in source_ids, (
            f"Expected refund_policy.md#refund-timeline in sources, got: {source_ids}"
        )

    def test_email_question_cites_correct_source(self):
        response = client.post("/chat", json={"query": "Can I change my email address?"})

        assert response.status_code == 200
        body = response.json()
        source_ids = [s["source"] for s in body["sources"]]
        assert any("account_help.md" in sid for sid in source_ids), (
            f"Expected account_help.md in sources, got: {source_ids}"
        )
        assert "account_help.md#change-email-address" in source_ids, (
            f"Expected account_help.md#change-email-address in sources, got: {source_ids}"
        )


class TestChatOutOfScope:
    def test_out_of_scope_question_returns_cannot_confirm(self):
        response = client.post("/chat", json={"query": "Which restaurants are nearby?"})

        assert response.status_code == 200
        body = response.json()
        answer = body["answer"].lower()
        assert "cannot confirm" in answer, (
            f"Expected 'cannot confirm' in answer, got: {body['answer']}"
        )
