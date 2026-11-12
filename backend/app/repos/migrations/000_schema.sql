CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL COLLATE NOCASE UNIQUE,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user','organizer')),
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS venues (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  layout_config TEXT NOT NULL DEFAULT '{}',
  capacity INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS seats (
  id INTEGER PRIMARY KEY,
  venue_id INTEGER NOT NULL REFERENCES venues(id),
  row_number INTEGER NOT NULL,
  seat_number INTEGER NOT NULL,
  x REAL NOT NULL, y REAL NOT NULL, z REAL NOT NULL,
  seat_type TEXT NOT NULL DEFAULT 'standard' CHECK (seat_type IN ('standard')),
  UNIQUE (venue_id, row_number, seat_number)
);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  start_time TEXT NOT NULL,
  end_time TEXT NOT NULL,
  organizer_id INTEGER NOT NULL REFERENCES users(id),
  venue_id INTEGER NOT NULL REFERENCES venues(id),
  status TEXT NOT NULL DEFAULT 'draft'
    CHECK (status IN ('draft','published','closed','cancelled')),
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS event_seats (
  id INTEGER PRIMARY KEY,
  event_id INTEGER NOT NULL REFERENCES events(id),
  seat_id INTEGER NOT NULL REFERENCES seats(id),
  status TEXT NOT NULL DEFAULT 'available'
    CHECK (status IN ('available','locked','sold')),
  version INTEGER NOT NULL DEFAULT 0,
  UNIQUE (event_id, seat_id)
);

CREATE TABLE IF NOT EXISTS bookings (
  id INTEGER PRIMARY KEY,
  event_id INTEGER NOT NULL REFERENCES events(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  status TEXT NOT NULL DEFAULT 'reserved'
    CHECK (status IN ('reserved','cancelled','used')),
  created_at TEXT NOT NULL,
  cancelled_at TEXT
);

CREATE TABLE IF NOT EXISTS booking_seats (
  id INTEGER PRIMARY KEY,
  booking_id INTEGER NOT NULL REFERENCES bookings(id),
  event_id INTEGER NOT NULL REFERENCES events(id),
  seat_id INTEGER NOT NULL REFERENCES seats(id),
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1))
);

-- 关键：只对“有效”的预约座位做唯一约束，取消后（is_active=0）才能重订
CREATE UNIQUE INDEX IF NOT EXISTS ux_booking_seats_active
  ON booking_seats (event_id, seat_id) WHERE is_active = 1;

CREATE TABLE IF NOT EXISTS tickets (
  id INTEGER PRIMARY KEY,
  booking_id INTEGER NOT NULL UNIQUE REFERENCES bookings(id),
  ticket_code TEXT NOT NULL UNIQUE,
  verified_at TEXT,
  verified_by INTEGER REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS ix_bookings_user
  ON bookings (user_id, created_at DESC, id DESC);
CREATE INDEX IF NOT EXISTS ix_event_seats_event
  ON event_seats (event_id, status);
CREATE INDEX IF NOT EXISTS ix_booking_seats_booking
  ON booking_seats (booking_id);
