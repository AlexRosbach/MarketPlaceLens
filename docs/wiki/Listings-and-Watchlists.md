# Listings and Watchlists

Listings are normalized results imported from job runs.

Listing cards use Kramlet-inspired product motion: cards enter with a short stagger, lift subtly on hover, and keep image zoom contained inside the card frame. The swipe card follows horizontal drag movement before either settling back or marking the listing seen.

## Listing Status

- `new`: active listing
- `seen`: reviewed and dismissed from the active list
- `hidden`: manually or locally filtered out
- `notified`: delivered through a configured channel

## Listing Actions

Users can:

- open the original marketplace listing
- save to a watchlist
- mark seen
- hide
- mark contacted
- generate inquiry text
- generate an AI assessment
- open the listing location on a map

Marking a listing as contacted automatically adds it to the user's default watchlist.

## Watchlists

Each user can choose a default watchlist. The normal Watch action saves to that list. The watchlist dropdown allows choosing another list or creating a new list from the listing card.

## Review Mode

Review mode shows one listing at a time with image, price, location, source, watchlist state, contacted state, and core actions. On mobile, the card is optimized so the main information and actions fit in a compact flow.
