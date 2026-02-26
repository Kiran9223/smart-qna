import pytest


@pytest.mark.asyncio
async def test_create_post(client, auth_headers):
    resp = await client.post("/api/v1/posts", json={
        "title": "How do I set up Docker?",
        "body": "I'm trying to get Docker running locally.",
        "tag_ids": [],
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "How do I set up Docker?"
    assert data["status"] == "OPEN"


@pytest.mark.asyncio
async def test_list_posts(client, auth_headers):
    await client.post("/api/v1/posts", json={
        "title": "Test post for listing",
        "body": "Body content here.",
        "tag_ids": [],
    }, headers=auth_headers)
    resp = await client.get("/api/v1/posts")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_post(client, auth_headers):
    create = await client.post("/api/v1/posts", json={
        "title": "Specific post",
        "body": "Body here.",
        "tag_ids": [],
    }, headers=auth_headers)
    post_id = create.json()["post_id"]

    resp = await client.get(f"/api/v1/posts/{post_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["post_id"] == post_id


@pytest.mark.asyncio
async def test_create_post_requires_auth(client):
    resp = await client.post("/api/v1/posts", json={
        "title": "Unauthorized",
        "body": "Should fail.",
        "tag_ids": [],
    })
    assert resp.status_code == 403
