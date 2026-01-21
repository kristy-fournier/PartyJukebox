## Wishlist
*Features I would like to add, will be completed in any order*
- [x] Admin password
    * Allows restricting certain features and changing permissions on the fly on the client
- [ ] Refactoring existing code
    - [ ] Update the SQL -> Server -> Client pipeline when searching and building playlist
    - [ ] Verify all if-else sequences are correct and not redundant
    - [x] Remove old comments
- [ ] Security Updates
    - [ ] `.env` file for the api keys and other runtime info to be set, rather than in the `.py` files
    - [ ] Hashing rather than plaintext sending (that way at least the password text itself stays private)
    - [ ] Actually use SSL, for posting (CORS seems like an issue)
- [ ] GUI update for client
    - [x] Playlist items look cleaner
    - [x] Dark mode
    - [ ] Google material design (Not sure I want this anymore)
    - [ ] New Icons
- [ ] "Credit" system so each client can only add a set number of songs
    - Based on time period, number in queue, other possible ideas for credits
    - Without a login system there's no easy way to give credits to specific clients (and a login is beyond scope of what I want to do)
        - Potentially a "redemption code" system, which can be tracked client side
    - All of this is very hackable without a server-side login.