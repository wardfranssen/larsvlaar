# Documentation for main.py

## /db_export
### Description
The /db_export endpoint is used to export data from the database, with certain restrictions. It allows for the export of specific tables or columns, while ensuring sensitive information such as passwords and restricted tables are not included in the export.

### Method
GET

### Rate limiting
This endpoint is rate limited to 1 requests per 10 seconds per session.

### Parameters
table (optional): Specifies the table to export data from. If not provided, the entire database is exported with certain restrictions.  

columns (optional): Specifies the columns to export from the specified table. If not provided, all columns except restricted ones are exported.  

username (optional): If provided, the export is limited to data related to the specified user. There is no need to provide a table parameter when using this.  

### Restrictions
Certain tables and columns are restricted from being exported because they either contain sensitive information or are in development.  

Not allowed tables: clans, transactions

Not allowed columns: password, email, clan, jwt

### Responses
#### Success Response  
Status Code: 200 OK  
Response Format:  
```
{
    "status": "Success",
    "data": {
        "table_name": [
            {
                "column1": "value1",
                "column2": "value2",
                ...
            },
            ...
        ],
        ...
    }
}
```
#### Failure Responses
Unauthorized Table Export:  

Status Code: 401 Unauthorized
Response Format:
```
{
    "status": "Failed",
    "message": "Not allowed to export this table"
}
```
Unauthorized Column Export:  

Status Code: 401 Unauthorized  
Response Format:  
```
{
    "status": "Failed",
    "message": "Not allowed to export these columns"
}
```
Missing Table Parameter when Columns are Provided:

Status Code: 400 Bad Request
Response Format:
```
{
    "status": "Failed",
    "message": "Table is required"
}
```
Server Error:

Status Code: 500 Internal Server Error
```
{
    "status": "Failed",
    "message": "A server error occurred"
}
```
### Usage Examples  
#### Exporting the Entire Database  
Request:

GET /db_export

Response:

```
{
    "status": "Success",
    "data": {
        "users": [
            {
                "username": "user1",
                "highscore": 100,
                "coins": 50,
                "backgrounds": "background1",
                "skins": "skin1",
                "pipeskins": "pipeskin1"
            },
            ...
        ],
        ...
    }
}
```
#### Exporting Specific Table  
Request:

GET /db_export?table=users

Response:

```
{
    "status": "Success",
    "data": [
        {
            "username": "user1",
            "highscore": 100,
            "coins": 50,
            "backgrounds": "background1",
            "skins": "skin1",
            "pipeskins": "pipeskin1"
        },
        ...
    ]
}
```
#### Exporting Specific Columns from a Table
Request:

GET /db_export?table=users&columns=username,highscore

Response:

```
{
    "status": "Success",
    "data": [
        {
            "username": "user1",
            "highscore": 100
        },
        ...
    ]
}
```
Exporting Data for a Specific User
Request:

GET /db_export?username=user1

Response:

```
{
    "status": "Success",
    "data": [
        {
            "username": "user1",
            "highscore": 100,
            "coins": 50,
            "backgrounds": "background1",
            "skins": "skin1",
            "pipeskins": "pipeskin1"
        }
    ]
}
```


## /db_ddl
### Description
The /db_ddl endpoint exports the database schema, providing the Data Definition Language (DDL) statements for tables in the database. Certain tables are excluded from the export for security reasons.

### Method
GET

### Rate Limiting
This endpoint is rate-limited to 1 request per 10 seconds.

### Parameters
None.

### Restrictions
The following tables are excluded from the schema export: clans, transactions

### Responses
#### Success Response
Status Code: 200 OK  
Response Format:
```
{
    "status": "Success",
    "data": {
        "table_name": "CREATE TABLE statement",
        ...
    }
}
```
#### Failure Responses
##### Server Error:
Status Code: 500 Internal Server Error  
Response Format:
```
{
    "status": "Failed",
    "message": "A server error occurred"
}
```
### Usage Examples  
#### Exporting the Database Schema
Request:

GET /db_ddl

Response:

```
{
    "status": "Success",
    "data": {
        "lootboxes": "CREATE TABLE `lootboxes` (\n  `name` text,\n  `odds` json DEFAULT NULL,\n  `price` int DEFAULT NULL\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci",
        ...
    }
}
```
