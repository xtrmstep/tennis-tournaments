# Competition Management — Improvement TODO

## Main area: Competition Management

### 1. Creation and sorting of pairs
- [ ] Allow admins/moderators to create pairs manually within a competition
- [ ] Support re-sorting / re-generating pairs after initial creation
- [ ] Expose pair management through the API and UI

### 2. Self-registration of pairs by participants
- [ ] Allow authenticated participants to form their own pairs before sorting
- [ ] Add a pair-request flow (propose partner, partner confirms)
- [ ] Moderator can review and approve/reject self-formed pairs before the competition starts

### 3. Graphical court presentation during a match
- [ ] Display active matches grouped by court (not by time slot)
- [ ] Show a visual court layout with player/team names on each court
- [ ] Real-time or polling-based refresh of court status

### 4. Score input during a match
- [ ] Add score entry UI for each active match (set scores, games, or points)
- [ ] Restrict score entry to moderators or designated scorekeepers
- [ ] Validate scores against the competition format (sets, tie-break rules, etc.)
- [ ] Persist scores to the database and reflect them in the match state

### 5. Player scoring / leaderboard
- [ ] Calculate and store individual player ratings or points after each competition
- [ ] Show a leaderboard / standings view per competition
- [ ] Accumulate scores across multiple competitions for an overall ranking
