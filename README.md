
# Larsvlaar.nl

This is the repo for [https://larsvlaar.nl](larsvlaar.nl)


## Installation
##### You need to have python installed on you machine [https://www.python.org/downloads/](https://www.python.org/downloads/)!


1. Download the zip and unzip it.
2. Create a config.json file using the template below.
3. Open a terminal and run these commands.
4. Go to [http://127.0.0.1:5100](http://127.0.0.1:5100)

```bash
  cd "location/of/the/files"
  pip install -r requirements.txt
  cd src
  python main.py
```

config.json template:
```
{
  "db_password": "<Password>",
  "secret_key": "<Secret_key>"
}

```

### Note:
If you don't have a mysql database to connect to you will see "An error occurred" when you go to [http://127.0.0.1:5100/flappy](http://127.0.0.1:5100/flappy)!

## Issues

If you have found any issue please open a Issue using the github feature.

## Contributing

Contributions are always welcome!

If you want to contribute you can always open a pull request.

## Contact

If you have any questions you can always send me an email at ```franssenward3@gmail.com```.
