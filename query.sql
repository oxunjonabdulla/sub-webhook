-- Users with an ACTIVE subscription who have had NO attendance
-- records in meetings_attendance during the last 30 days.

SELECT u.id, u.email
from users u
JOIN subscriptions s ON s.user_id = u.id
WHERE s.status = "active"
    AND s.expires_at > now()
    AND NOT EXISTS(
    SELECT 1
       FROM meetings_attendance ma
       WHERE ma.user_id = u.id
         AND ma.date >= current_data - INTERVAL "30 days"
                                                );
