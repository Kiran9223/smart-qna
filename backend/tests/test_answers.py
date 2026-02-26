import pytest


@pytest.mark.asyncio
async def test_submit_answer(client, auth_headers):
    post = await client.post("/api/v1/posts", json={
        "title": "Answer test question",
        "body": "Please answer this.",
        "tag_ids": [],
    }, headers=auth_headers)
    post_id = post.json()["post_id"]

    resp = await client.post(f"/api/v1/posts/{post_id}/answers",
                             json={"body": "Here is my answer."}, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["body"] == "Here is my answer."
    assert data["is_accepted"] is False


@pytest.mark.asyncio
async def test_accept_answer(client, auth_headers):
    post = await client.post("/api/v1/posts", json={
        "title": "Accept answer question",
        "body": "Accept this answer.",
        "tag_ids": [],
    }, headers=auth_headers)
    post_id = post.json()["post_id"]

    answer = await client.post(f"/api/v1/posts/{post_id}/answers",
                               json={"body": "My answer."}, headers=auth_headers)
    answer_id = answer.json()["answer_id"]

    resp = await client.patch(f"/api/v1/answers/{answer_id}/accept", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["is_accepted"] is True
