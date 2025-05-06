# keelson-connector-ais

Multiple co-hosted connectors towards ais data flows:

* `ais2keelson` - reads binary AIS messages encoded in NMEA0183 sentences from STDIN and puts to zenoh
* `digitraffic2keelson` - reads JSON encoded AIS from the digitraffic mqtt websocket api and puts to zenoh

Packaged as a docker container available from: https://github.com/RISE-Maritime/keelson-connector-ais/pkgs/container/keelson-connector-ais. NOTE: This container has [porla](https://github.com/RISE-Maritime/porla) as its base container and thus also includes all the binaries provided by porla.

## Usage

### `ais2keelson`
```
usage: ais2keelson [-h] [--log-level LOG_LEVEL] [--mode {peer,client}] [--connect CONNECT] -r REALM -e ENTITY_ID -s SOURCE_ID [--publish-raw] [--publish-json] [--publish-fields]

options:
  -h, --help            show this help message and exit
  --log-level LOG_LEVEL
  --mode {peer,client}, -m {peer,client}
                        The zenoh session mode. (default: None)
  --connect CONNECT     Endpoints to connect to, in case multicast is not working. ex. tcp/localhost:7447 (default: None)
  -r REALM, --realm REALM
  -e ENTITY_ID, --entity-id ENTITY_ID
  -s SOURCE_ID, --source-id SOURCE_ID
  --publish-raw
  --publish-json
  --publish-fields
```

### `digitraffic2keelson`
```
usage: digitraffic2keelson [-h] [--log-level LOG_LEVEL] [--mode {peer,client}] [--connect CONNECT] -r REALM -e ENTITY_ID -s SOURCE_ID [--publish-raw] [--publish-fields]

options:
  -h, --help            show this help message and exit
  --log-level LOG_LEVEL
  --mode {peer,client}, -m {peer,client}
                        The zenoh session mode. (default: None)
  --connect CONNECT     Endpoints to connect to, in case multicast is not working. ex. tcp/localhost:7447 (default: None)
  -r REALM, --realm REALM
  -e ENTITY_ID, --entity-id ENTITY_ID
  -s SOURCE_ID, --source-id SOURCE_ID
  --publish-raw
  --publish-fields
```

### docker-compose example setup
```yaml
services:

  source-onboard-transponder:
    image: ghcr.io/rise-maritime/keelson-connector-ais:v0.1.8
    restart: unless-stopped
    network_mode: "host"
    command:
      [
        "socat TCP4-CONNECT:<IP>:<PORT> STDOUT | ais2keelson -r <realm> -e <entity> -s <source> --publish-raw --publish-fields"
      ]

  source-digitraffic:
    image: ghcr.io/rise-maritime/keelson-connector-ais:v0.1.8
    restart: unless-stopped
    network_mode: "host"
    command:
      [
        "digitraffic2keelson -r <realm> -e <entity> -s digitraffic --publish-raw --publish-fields"
      ]
```
