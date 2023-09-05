"""
This class should be responsible for the following:
- checks docker file monitor and natmap service (if neccessary) for changes
- listens to ws events from those services as well
- whenever there is an event (be it from ws or from polling)
    - pull info from dns and mc-router
    - checks if server_list from dns matches the ones from mc-router
    - also checks if there is any change
    - if there is a change, call the callback function

Specifically, when initializing, it should check for changes once 
    and call the callback function if there is any change (indefinitely retrying if there is an error)

I think there should also be a queue for events that are not yet processed
"""
