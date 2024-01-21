# Tim's Fast Endpoint + Website Template

TADA! Some basic info here?...

## The Project

- **Language:** Python
- **Server:** FastAPI and Uvicorn
- **Database:** MongoDB (supports local, remote, and Atlas setups)
- **User Authentication:** Token Auth + Github Auth (w/ Refresh Token)
  - _Both stored as Secure Cookies_
- **Frontend/Backend Connection:** HTMX, Hyperscript, and the Jinja2 Template Engine
- **UI/UX:** Tailwind CSS + Flowbite Components

## TODOs To Complete

- [ ] Now that Github Auth is working, find a way to link it into our system (create/assign it a user in the db) and generate one of OUR Tokens (JWT) that we will then handle normally. This way all of our verification logic stays the same.
  - Alternatively: update the verify logic to detect if we are using OUR Tokens or the Github token and implement more logic to verify Github token (::sad-panda::)
- [ ] We need to track our JWT tokens and store them in the database. When we verify token, they have to be able to be decoded successfully AND they must still be in the dB. That way, on logout, we can erase token from dB and (even if Token is valid, in itself) then we can invalidate the tokens.
  - A "logout every session" function would just remove ALL the tokens from dB and user will have to login, again.
- [ ] x
