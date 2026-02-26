import pytest


@pytest.mark.asyncio
async def test_vote_on_post(client, auth_headers):
    create = await client.post("/api/v1/posts", json={
        "title": "Vote test post",
        "body": "Vote on this.",
        "tag_ids": [],
    }, headers=auth_headers)
    post_id = create.json()["post_id"]

    resp = await client.post(f"/api/v1/posts/{post_id}/vote",
                             json={"type": "UP"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["vote_count"] == 1
    assert data["user_vote"] == "UP"


@pytest.mark.asyncio
async def test_vote_toggle(client, auth_headers):
    create = await client.post("/api/v1/posts", json={
        "title": "Toggle vote post",
        "body": "Toggle vote test.",
        "tag_ids": [],
    }, headers=auth_headers)
    post_id = create.json()["post_id"]

    await client.post(f"/api/v1/posts/{post_id}/vote",
                      json={"type": "UP"}, headers=auth_headers)
    resp = await client.post(f"/api/v1/posts/{post_id}/vote",
                             json={"type": "UP"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["vote_count"] == 0
    assert data["user_vote"] is None


@pytest.mark.asyncio
async def test_vote_switch(client, auth_headers):
    create = await client.post("/api/v1/posts", json={
        "title": "Switch vote post",
        "body": "Switch vote test.",
        "tag_ids": [],
    }, headers=auth_headers)
    post_id = create.json()["post_id"]

    await client.post(f"/api/v1/posts/{post_id}/vote",
                      json={"type": "UP"}, headers=auth_headers)
    resp = await client.post(f"/api/v1/posts/{post_id}/vote",
                             json={"type": "DOWN"}, headers=auth_headers)
    data = resp.json()
    assert data["vote_count"] == -1
    assert data["user_vote"] == "DOWN"
