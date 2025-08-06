# Helper functions that should be moved to keelson-sdk?
import json
import time
import logging
from typing import Callable, Sequence

import zenoh

from keelson import enclose, construct_pubsub_key, construct_rpc_key
from keelson.payloads.Primitives_pb2 import (
    TimestampedBytes,
    TimestampedInt,
    TimestampedFloat,
    TimestampedString,
)
import skarv
import keelson
from keelson.payloads.Primitives_pb2 import TimestampedString
from keelson.payloads.foxglove.LocationFix_pb2 import LocationFix
from keelson.interfaces.Configurable_pb2 import ConfigurableSuccessResponse
from keelson.interfaces.ErrorResponse_pb2 import ErrorResponse

logger = logging.getLogger("utils")


class Configurable:
    def __init__(
        self,
        session: zenoh.Session,
        base_path: str,
        entity_id: str,
        responder_id: str,
        get_config_cb: Callable[[], dict],
        set_config_cb: Callable[[dict], None],
    ):
        self._session = session
        self._get_config_cb = get_config_cb
        self._set_config_cb = set_config_cb

        self._get_config_key = construct_rpc_key(
            base_path, entity_id, "get_config", responder_id
        )

        session.declare_queryable(self._get_config_key, self._get_config, complete=True)
        self._set_config_key = construct_rpc_key(
            base_path, entity_id, "set_config", responder_id
        )

        session.declare_queryable(self._set_config_key, self._set_config, complete=True)

        self._publisher = session.declare_publisher(
            construct_pubsub_key(base_path, entity_id, "configuration", responder_id)
        )

    # Config callbacks

    def _get_config(self, query: zenoh.Query):
        logger.debug("Received query on: %s", query.key_expr)
        logger.debug("Returning current config on key: %s", self._get_config_key)
        query.reply(self._get_config_key, json.dumps(self._get_config_cb()))

    def _set_config(self, query: zenoh.Query):
        try:
            logger.debug("Received query on: %s", query.key_expr)
            logger.debug("Replying on key: %s", self._set_config_key)

            logger.debug("Calling `set_config_cb`")
            self._set_config_cb(json.loads(query.payload.to_bytes()))

            query.reply(
                self._set_config_key, ConfigurableSuccessResponse().SerializeToString()
            )

        except Exception as exc:
            logger.exception(
                "Failed to respond to query with payload: %s", query.payload
            )
            query.reply_err(
                ErrorResponse(error_description=str(exc)).SerializeToString()
            )

        finally:
            # Publish updated config to ensure we log it
            payload = TimestampedString()
            payload.timestamp.FromNanoseconds(time.time_ns())
            payload.value = json.dumps(self._get_config_cb())
            logger.debug("Publishing new configuration to %s", self._publisher.key_expr)
            logger.debug(payload)
            self._publisher.put(enclose(payload.SerializeToString()))


def enclose_from_bytes(value: bytes, timestamp: int = None) -> bytes:
    payload = TimestampedBytes()
    payload.timestamp.FromNanoseconds(timestamp or time.time_ns())
    payload.value = value

    return enclose(payload.SerializeToString())


def enclose_from_integer(value: int, timestamp: int = None) -> bytes:
    payload = TimestampedInt()
    payload.timestamp.FromNanoseconds(timestamp or time.time_ns())
    payload.value = value

    return enclose(payload.SerializeToString())


def enclose_from_float(value: float, timestamp: int = None) -> bytes:
    payload = TimestampedFloat()
    payload.timestamp.FromNanoseconds(timestamp or time.time_ns())
    payload.value = value

    return enclose(payload.SerializeToString())


def enclose_from_string(value: str, timestamp: int = None) -> bytes:
    payload = TimestampedString()
    payload.timestamp.FromNanoseconds(timestamp or time.time_ns())
    payload.value = value

    return enclose(payload.SerializeToString())


def enclose_from_lon_lat(
    longitude: float, latitude: float, timestamp: int = None
) -> bytes:
    payload = LocationFix()
    payload.timestamp.FromNanoseconds(timestamp or time.time_ns())
    payload.latitude = latitude
    payload.longitude = longitude

    return enclose(payload.SerializeToString())


def get_first(items: Sequence):
    """
    Returns the first item in a list or None if the list is empty.
    """
    return next(iter(items), None)


def unpack(sample: skarv.Sample):
    """
    Unpacks a skarv sample into a keelson message.
    """
    subject = sample.key_expr
    _, _, payload = keelson.uncover(sample.payload.to_bytes())
    return keelson.decode_protobuf_payload_from_type_name(
        payload, keelson.get_subject_schema(subject)
    )


def mirror(zenoh_session: zenoh.Session, zenoh_key: str, skarv_key: str):
    # Subscribe to the key expression and put the received value into skarv
    zenoh_session.declare_subscriber(
        zenoh_key, lambda sample: skarv.put(skarv_key, sample.payload)
    )

    # If the key expression already has a value, we fetch it and put it into skarv
    for response in zenoh_session.get(zenoh_key):
        if response := response.ok and not skarv.get(skarv_key):
            skarv.put(skarv_key, response.payload)
