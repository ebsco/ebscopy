# How to Use

## Import
```python
import ebscopy
```

## Credentials and Parameters
The API requires some credentials and parameters to accept connections. These can be defined in environment variables or explicitly passed to the relevant functions.

* Implicit credentials:
```python
s = Session()
```

* Explicit credentials:
```python
s = Session(user_id="user", password="pass", profile="profile", org="org", guest="n")
```


## Sessions
Sessions are the main interface to the API. Creating a Session will implicitly make a Connection, or you can get a Connection from the POOL first and pass it to the Session.

* Session with implicit Connection:
```python
s = Session()
```

* Session with explicit Connection:
```python
c = POOL.get()
s = Session(connection=c)
```

## Search Results
Performing a search in a Session will return a Results object. This contains the raw data from the API, as well as some simplified data structures and functions.

* Searching
```python
s = Session()
r = s.search("blue")
```

* Pretty printing
```python
r.pprint()
```

* Accessing raw data
```python
print r.records_raw[0]
```

* Accessing simple data
```python
print r.records_simple[0]
```

## Retrieving Records
The search results contain only basic information on each Record; for more, call the retrieve function of the Result object.

* Retrieve a record
```python
rec = s.retrieve(r.record[0])
```

* Pretty print a record
```python
rec.pprint()
```

* Print simple information
```python
print rec.simple_title
```

## Ending a Session
You should end Sessions when you are done with them.

```python
s.end()
```

