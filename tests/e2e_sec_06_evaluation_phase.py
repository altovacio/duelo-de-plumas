        vote_payload = {
            "text_id": text_id_to_vote_on,
            "text_place": 1, # Attempting to give 1st place
            "comment": "User 1 (not a judge) trying to vote on their own text in contest1."
        }
        response = await client.post(
            f"/contests/{test_data['contest1_id']}/votes", # REVERTED: REMOVE TRAILING SLASH
            json=[vote_payload],  # Wrap in array since API expects List[VoteCreate]
            headers=test_data["user1_headers"]
        ) 