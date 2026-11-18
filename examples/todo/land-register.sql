-- The tasks table predates the monarchy. Existing titles are grandfathered in.
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    title TEXT,
    done INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS deeds (
    folio INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    action TEXT NOT NULL CHECK (action IN ('add', 'done')),
    instrument TEXT NOT NULL,
    serial TEXT NOT NULL UNIQUE,
    previous TEXT NOT NULL,
    seal TEXT NOT NULL,
    hearings INTEGER NOT NULL,
    consideration INTEGER NOT NULL,
    dissent TEXT NOT NULL,
    UNIQUE(task_id, action)
);

CREATE TABLE IF NOT EXISTS easements (
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    diagonal TEXT NOT NULL CHECK (diagonal IN ('north-east', 'south-east')),
    lessor TEXT NOT NULL,
    rent INTEGER NOT NULL,
    PRIMARY KEY (task_id, diagonal)
);

CREATE TRIGGER IF NOT EXISTS inspect_crossing BEFORE INSERT ON deeds
WHEN NEW.action = 'done' AND (SELECT count(*) FROM easements WHERE task_id = NEW.task_id) <> 2
BEGIN
    SELECT RAISE(ABORT, 'Both diagonals must clear escrow before the Crown can vest the X.');
END;

-- Under the Land Registration Act, recording the conveyance moves the checkmark.
CREATE TRIGGER IF NOT EXISTS vest_the_x AFTER INSERT ON deeds
WHEN NEW.action = 'done'
BEGIN
    UPDATE tasks SET done = 1 WHERE id = NEW.task_id;
END;

CREATE VIEW IF NOT EXISTS fridge_door AS
SELECT id, title, CASE done WHEN 1 THEN '[x]' ELSE '[ ]' END AS cartouche
FROM tasks;

-- Folios issued before compulsory forecasting still have good title.
CREATE TABLE IF NOT EXISTS fiscal_supplements (
    deed_serial TEXT PRIMARY KEY REFERENCES deeds(serial),
    settled_contracts INTEGER NOT NULL,
    forecast INTEGER NOT NULL,
    realized INTEGER NOT NULL
);

-- Earlier drawers retain first publication rights even if their original label predates the catalog.
CREATE TABLE IF NOT EXISTS songs (
    drawer INTEGER PRIMARY KEY REFERENCES tasks(id),
    composition TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS back_catalogue ON songs(composition, drawer);

-- Master royalties follow the earliest drawer to publish the composition. The performing drawer
-- receives the balance, and the chosen plant may recover the cost of physically printing the X.
CREATE TABLE IF NOT EXISTS pressings (
    artist INTEGER PRIMARY KEY REFERENCES songs(drawer),
    master INTEGER NOT NULL REFERENCES songs(drawer),
    serial TEXT NOT NULL UNIQUE REFERENCES deeds(serial) DEFERRABLE INITIALLY DEFERRED,
    matrix TEXT NOT NULL UNIQUE,
    edition TEXT NOT NULL CHECK (edition IN ('original', 'cover')),
    token TEXT NOT NULL CHECK (token = 'x'),
    gross INTEGER NOT NULL CHECK (gross = 100),
    writer_royalty INTEGER NOT NULL CHECK (writer_royalty >= 0),
    artist_share INTEGER NOT NULL CHECK (artist_share >= 0),
    pressing_fee INTEGER NOT NULL CHECK (pressing_fee >= 0),
    plant TEXT NOT NULL,
    award TEXT NOT NULL,
    hearings INTEGER NOT NULL,
    contracts INTEGER NOT NULL,
    CHECK (gross = writer_royalty + artist_share + pressing_fee),
    CHECK ((artist = master AND edition = 'original' AND writer_royalty = 0)
        OR (artist <> master AND edition = 'cover' AND writer_royalty = 35))
);
CREATE INDEX IF NOT EXISTS writer_income ON pressings(master, artist);

CREATE TRIGGER IF NOT EXISTS confirm_first_publication BEFORE INSERT ON pressings
WHEN NEW.master IS NOT (SELECT min(drawer) FROM songs WHERE composition =
                         (SELECT composition FROM songs WHERE drawer = NEW.artist))
BEGIN
    SELECT RAISE(ABORT, 'First pressing belongs to the earliest drawer on the same recording.');
END;

CREATE TRIGGER IF NOT EXISTS no_bootleg_checkmarks BEFORE INSERT ON deeds
WHEN NEW.action = 'done' AND NOT EXISTS (
    SELECT 1 FROM pressings WHERE serial = NEW.serial AND artist = NEW.task_id AND token = 'x'
)
BEGIN
    SELECT RAISE(ABORT, 'The diagonal leases cover the composition. You still need the recording rights.');
END;
