# Domain Glossary

This file defines the core domain concepts for the tennis tournament web application.

---

## Concepts

### 1. User

A registered person who can access the website.

A user may only browse the website after completing their profile. On first login, they are redirected to the profile page and must fill in required fields before accessing other content.

A user is not always a competition participant. A user becomes a participant only after applying to a specific event.

Required profile fields: full name, username, approximate skill level (0–10), gender.

Main rules:
- A logged-in user with an incomplete profile cannot browse other content.
- A user with a complete profile can browse public website content.
- A user can view other user profiles in read-only mode.
- A user can apply to events or withdraw from them, depending on event rules and status.

---

### 2. User Profile

Describes the person behind the user account. Used for browsing, competition participation, event organization, sorting, and balancing players or teams.

Typical data: full name, username, gender, approximate skill level, photo/avatar (optional), short description (optional), contact visibility settings (optional).

Main rules:
- Profile completion is mandatory before using the main website.
- Skill level is simple and approximate, not a strict official ranking.
- Profile data may be used when creating singles or doubles sorting.
- Other users can view profiles but cannot edit them.

---

### 3. User Roles

Roles define what a user is allowed to do in the system.

Main roles:
- **Website Admin** — full control over users and website management.
- **Regular User** — can browse content and participate in events.
- **Event Moderator** — can manage competition-related data for assigned events; has no access to user management.

A user may have more than one role if needed.

---

### 4. Website Admin

Manages the website globally.

Main permissions: manage users, manage website content, assign Regular User and Event Moderator roles, manage events if needed, view and control all major website data.

Important restrictions:
- The Website Admin role cannot be assigned from the website UI.
- It can only be assigned manually through a configuration file or another protected system-level mechanism.
- Website admins cannot create another Website Admin through the normal application UI.

---

### 5. Regular User

A normal website user.

Main permissions: browse content after completing their profile, view other user profiles (read-only), view events and competitions, apply to events, withdraw from events if allowed, view event participants and results depending on event visibility.

Main restrictions: cannot modify events, cannot manage other participants, cannot run sorting or draw generation, cannot assign roles.

---

### 6. Event Moderator

A user assigned to manage a specific event or competition.

Main permissions: edit assigned events, manage event participants, approve/reject/remove participants, run sorting or draw generation, manage teams or pairs, update event status, record or adjust results.

Main restrictions:
- Manages only assigned events; no global admin rights.
- Cannot access the Users management page or modify any user account data.
- Cannot assign roles to other users.
- Cannot assign the Website Admin role.
- Cannot modify unrelated events.

---

### 7. Event / Competition

A named tennis activity organized through the website.

An event may be:
- **Singles**: one person versus one person
- **Doubles**: pair versus pair

The event type defines how participants are managed and how sorting is performed.

Typical data: event name, description, event type, date and time, location, registration period, maximum participants, event status, assigned moderators, list of participants, sorting or draw results.

Main rules:
- Event type should not be changed after participants or sorting already exist, unless the system explicitly supports rebuilding them.
- Only website admins or assigned moderators can modify an event.
- Regular users can apply to participate but cannot modify the event itself.

---

### 8. Event Status

Describes the current lifecycle stage of an event.

| Status | Meaning |
|---|---|
| Draft | Being prepared; not visible or not open yet |
| Published | Visible to users |
| Registration Open | Users can apply |
| Registration Closed | Users can no longer apply |
| Sorting Ready | Participants are finalized; sorting can be generated |
| In Progress | Event is active |
| Completed | Event is finished |
| Cancelled | Event was cancelled |

Main rules:
- Users can apply only when registration is open.
- Sorting should normally happen after registration is closed.
- Completed or cancelled events should not allow participant changes unless explicitly reopened by an admin or moderator.

---

### 9. Participant

A user who applied to a specific competition. A participant is a role of a user inside a specific event, not a separate person in the system.

Typical data: user reference, event reference, application status, skill level snapshot (optional), registration timestamp, withdrawal timestamp (optional).

Participant statuses: Applied, Approved, Rejected, Withdrawn, Removed, Confirmed.

Main rules:
- A user can become a participant by applying to an event.
- A user can withdraw from an event if the event allows it.
- Moderators can manage participant status.
- For singles events, participants are sorted as individual players.
- For doubles events, participants are grouped into pairs before or during sorting.

---

### 10. Team / Pair

Used in doubles events. A pair consists of two participants who compete together against another pair.

Typical data: event reference, first participant, second participant, team name (optional), combined or average skill level (optional), sorting position (optional).

Main rules:
- Teams are required for doubles events; not required for singles.
- A participant can belong to only one team in the same event.
- Teams may be created manually by a moderator or automatically by sorting logic.

---

### 11. Sorting / Draw

The process of organizing participants or teams for a competition.

- Singles events: sorting works with individual participants.
- Doubles events: sorting works with teams or pairs.

Main sorting goals: organize participants fairly, balance skill levels, prepare matchups or competition structure, reduce manual work for moderators.

Main rules:
- Sorting should not modify unrelated profile or event data.
- Sorting should be repeatable or auditable if moderators rerun it.
- Sorting behavior depends on event type.
- Singles sorting must not force people into pairs.
- Doubles sorting must produce valid pairs before pair-versus-pair competition can happen.

---

### 12. Match

A concrete game between competitors inside an event.

- Singles: player versus player
- Doubles: pair versus pair

Typical data: event reference, match number or round, player/team A, player/team B, scheduled time (optional), court (optional), score/result, winner, match status.

Match statuses: Planned, Scheduled, In Progress, Completed, Cancelled.

Main rules:
- Matches are generated from sorting/draw results or created manually.
- Match competitors must match the event type.
- A singles match cannot contain pairs.
- A doubles match cannot contain individual players unless they are part of a pair.

---

### 13. Application / Registration

The action of a user requesting to participate in an event. Useful when the system needs an approval flow.

Main rules:
- A user applies to an event.
- The application can be automatically accepted or manually reviewed.
- Moderators can approve or reject applications.
- A rejected or withdrawn user should not be included in sorting.
- Registration should respect event limits and deadlines.

---

### 14. Skill Level

An approximate value from 0 to 10 describing the user's tennis ability. Used for profile display, filtering, balancing, and sorting.

Main rules:
- Skill level is self-declared unless the system later introduces moderator validation.
- Skill level is required in the profile.
- Sorting may use skill level to balance players or teams.
- Skill level is approximate and should not be treated as an official ranking.

---

### 15. Gender

Part of the user profile. May be used for event rules, filtering, or sorting.

Main rules:
- Gender is required in the profile.
- Some events may be open to all genders; others may define eligibility rules based on gender.
- Gender should not affect sorting unless the event rules explicitly require it.

---

### 16. Event Eligibility Rules

Define who can apply to an event.

Examples: minimum/maximum skill level, gender restriction, maximum participants count, registration deadline, invite-only, approval required.

Main rules:
- Eligibility rules should be visible to users before they apply.
- The system should prevent invalid applications where possible.
- Moderators should be able to manage participants within event rules.

---

### 17. Content

Website information that is not directly a competition object.

Examples: home page text, announcements, rules, news, static pages, event descriptions.

Main rules:
- Regular users can browse content.
- Website admins can manage content.
- Event moderators may manage only content related to their assigned events, if allowed.

---

### 18. Audit / Change History

Records important changes made by admins and moderators.

Events to track: role assignment, event creation or update, participant approval/rejection/removal, sorting generation or regeneration, match result update, manual team changes.

Main rules:
- Admin and moderator actions should be traceable.
- Sorting changes should be recorded because they affect competition fairness.
- Role changes should always be auditable.

---

## Main Relationships

- A user has one profile.
- A user can have one or more roles.
- A user can apply to many events.
- An event has many participants.
- A participant belongs to one user and one event.
- A singles event uses participants directly as competitors.
- A doubles event groups participants into teams/pairs.
- A team belongs to one doubles event and contains two participants.
- A match belongs to one event.
- A match contains either two individual participants or two teams, depending on event type.
- A moderator can manage one or more assigned events.
- A website admin can manage global website data and assign non-admin roles.

---

## Important Boundaries

- A **user** is not the same as a **participant**. A user becomes a participant only inside a specific event.
- A **participant** is not the same as a **team**. A team exists only for doubles events and contains two participants.
- A **regular user** can participate in events but cannot manage them.
- An **event moderator** can manage assigned events but does not have global admin power.
- The **website admin** role must stay protected and must not be assignable from the normal UI.
- Singles and doubles share common event concepts, but their participant/team management and sorting rules are different.
