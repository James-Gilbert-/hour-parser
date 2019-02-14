# HourParser
HourParser is a Python module that will load a textfile containing store hour information into a database. For large files, an intermediate file is created and loaded directly from disk. Smaller files can be loaded directly.

### Features 
* Times are reported with a 24-hour clock
* Support for large files
### Assumptions
* If a store is open from 5:00pm to 2:00am on Monday, two records will be created. One record for 17:00 to 24:00 on Monday, and another for 00:00 to 02:00 on Tuesday.
* Formats of datetimes will be those encountered in the sample of store hours provided
* Memory and I/O bottlenecks were assumed to be client hardware dependent. If a large textfile needs to be loaded that cannot fit in memory, the records can be processed in batches. 

## Installation

Required Python 3.6 packages may be installed with the requirements.txt file. 

For the purposes of the exercise, MySQL was used as the database of choice. I created a database called "simplerose" and connected
on localhost. The table name is
hardcoded as "store_hours".
```bash
pip install -r requirements.txt
```

## Usage

```python
import hourparser as hp

# loads using intermediate file
hp.process_file("store_hours.txt",large_file=True,db_uri='mysql://root:root@localhost/simplerose') 

# loads without using intermediate file
hp.process_file("store_hours.txt",large_file=False,db_uri='mysql://root:root@localhost/simplerose') 

# loads without using intermediate file, also prints results before attempting to load into DB
hp.process_file("store_hours.txt",large_file=False,debug=True,db_uri='mysql://root:root@localhost/simplerose') 

```
An example intermediate file "temp.txt" is included in the directory. 
## Follow-up

If the stores were in different timezones, all the time information would be stored in GMT. I would include an additional column to store timezone information, assuming that the information is available. 

Store open/close hours would then be loaded into the database after being converted to GMT. An ORM Python module using SQLAlchemy could be implemented to accept queries with a timezone specified, to convert the query into GMT.

