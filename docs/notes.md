# UUID must be kept secret

- UUID cannot be broadcast publicly since they allow for hijacking of sessions
  - Identification when reconnecting is done through UUID
  - If another user finds out another users UUID they can potentially reconnect as that user
    - Currently if an already connecting user attempts to the reconnect, the reconnect fails however if for some reason that player disconnects, their session could be hijacked
- Usernames should be used for identification, hence they must be unique
  - Backend should guarantee this

# Reconnection is not allowed in lobby

- If it is allowed it begs the question, how long before you are kicked
  - If the host leaves, it's annoying
- No reason to allow reconnection, no progress can be lost

# Message vs Broadcast

- Messages should be sent to one client
- Broadcast are intended to be sent to all clients or more than one client
