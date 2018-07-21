DROP TABLE IF EXISTS music;
CREATE TABLE music (
    name TEXT,
    bpm FLOAT
);

CREATE INDEX bpm ON music(bpm);

.mode tabs
.import "bpm_list.tsv" music