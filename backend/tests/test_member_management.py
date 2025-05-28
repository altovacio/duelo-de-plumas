import pytest
from httpx import AsyncClient
from app.schemas.contest import ContestCreate, ContestDetailResponse, ContestMemberResponse
from tests.shared_test_state import test_data

async def test_member_management_basic_flow(client: AsyncClient):
    """Test basic member management functionality to ensure ContestDetailResponse works correctly."""
    # This test assumes we have admin and user tokens from previous tests
    if "admin_headers" not in test_data or "user1_headers" not in test_data:
        pytest.skip("Admin and user1 tokens not available")
    
    # Create a non-publicly listed contest for member testing
    contest_data = ContestCreate(
        title="Member Test Contest",
        description="Testing member management",
        password_protected=False,
        publicly_listed=False,  # Non-public contest requires member management
        judge_restrictions=False,
        author_restrictions=False
    )
    
    # Admin creates the contest
    response = await client.post(
        "/contests/",
        json=contest_data.model_dump(),
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 201, f"Failed to create contest: {response.text}"
    contest_id = response.json()["id"]
    
    # Get contest details to verify empty members list
    response = await client.get(
        f"/contests/{contest_id}",
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 200, f"Failed to get contest details: {response.text}"
    
    # This should not fail with Pydantic validation error
    contest_details = ContestDetailResponse(**response.json())
    assert contest_details.members == [], "New contest should have empty members list"
    assert hasattr(contest_details, 'members'), "ContestDetailResponse should have members field"
    
    # Add user1 as a member
    if "user1_id" in test_data:
        member_data = {"user_id": test_data["user1_id"]}
        response = await client.post(
            f"/contests/{contest_id}/members",
            json=member_data,
            headers=test_data["admin_headers"]
        )
        assert response.status_code in [200, 201], f"Failed to add member: {response.text}"
        
        # Verify member was added
        member_response = ContestMemberResponse(**response.json())
        assert member_response.user_id == test_data["user1_id"]
        assert hasattr(member_response, 'username'), "ContestMemberResponse should have username field"
        
        # Get contest details again to verify member is in the list
        response = await client.get(
            f"/contests/{contest_id}",
            headers=test_data["admin_headers"]
        )
        assert response.status_code == 200, f"Failed to get contest details after adding member: {response.text}"
        
        # This should not fail with Pydantic validation error
        contest_details = ContestDetailResponse(**response.json())
        assert len(contest_details.members) == 1, "Contest should have 1 member"
        assert contest_details.members[0].user_id == test_data["user1_id"]
        assert hasattr(contest_details.members[0], 'username'), "Member should have username field"
    
    # Clean up - delete the test contest
    response = await client.delete(
        f"/contests/{contest_id}",
        headers=test_data["admin_headers"]
    )
    assert response.status_code == 204, f"Failed to delete test contest: {response.text}"
    
    print("Member management test completed successfully") 