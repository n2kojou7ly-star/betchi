DELETE FROM match_request_slots;
DELETE FROM match_requests;
DELETE FROM messages;
DELETE FROM chat_rooms;
UPDATE availabilities SET status = '空き';