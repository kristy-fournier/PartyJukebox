## Wishlist
*Features I would like to add, will be completed in any order*
- [ ] Loading indicator while awaiting server stuff
- [ ] Refactoring existing code
    - [x] Remove old comments
    - [ ] Update the SQL -> Server -> Client pipeline when searching and building playlist
    - [ ] Verify all if-else sequences are correct and not redundant
- [ ] Security Updates
    - [x] `.env` file for the api keys and other runtime info to be set, rather than in the `.py` files
    - [x] Hashing rather than plaintext sending passwords (that way at least the password text itself isn't transmitted over the network)
    - [ ] Actually use SSL, for posting (CORS seems like an issue)
- [ ] Accessibility
    - [ ] Better use of semantic HTML tags
    - [ ] Full keyboard control (tab, enter to select, tab between control buttons)
- [ ] GUI update for client
    - [x] Playlist items look cleaner
    - [x] Dark mode
    - [ ] New Icons
    - [ ] Google material design (Not sure I want this anymore)
- [ ] "Credit" system so each client can only add a set number of songs
    - Based on time period, number in queue, other possible ideas for credits
    - Without a login system there's no easy way to give credits to specific clients (and a login is beyond scope of what I want to do)
        - Potentially a "redemption code" system, which can be tracked client side
    - All of this is very hackable without a server-side login.
- [ ] Websockets / some method of updating the time remaining to any client on the playlist screen
    * This is implemented in a very broken way right now
    - [x] Set a timeout to change the time (to start)
    - [x] Send updates to the playlist in real time when songs are added
        * This is only kind of done, still needs work
        - [x] Update the playlist's html without destroying it (create 1 new element)
    - [x] Tell clients looking at the playlist when the song has been paused (so they can pause the local timers)