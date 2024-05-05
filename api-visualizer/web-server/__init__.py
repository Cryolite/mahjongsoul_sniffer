#!/usr/bin/env python3
# ruff: noqa: N999

import base64
import os
import subprocess
from typing import TYPE_CHECKING, Any

import flask
from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.message import DecodeError, Message
from google.protobuf.message_factory import GetMessageClass

if TYPE_CHECKING:
    from google.protobuf.descriptor import Descriptor

import mahjongsoul_sniffer.redis as redis_
from mahjongsoul_sniffer import mahjongsoul_pb2

app = flask.Flask(
    __name__,
    static_folder="vue/dist/assets",
    template_folder="vue/dist",
    static_url_path="/assets",
)


_redis = redis_.Redis(module_name="api_visualizer")


@app.route("/")
def top_page() -> flask.Response:
    return flask.send_from_directory(
        app.template_folder,
        "index.html",
        mimetype="text/html",
    )


@app.route("/<path:path>")
def assets(path: os.PathLike[str] | str) -> flask.Response:
    return flask.send_from_directory(app.static_folder, path)


@app.route("/mitmproxy-ca-cert.crt")
def mitmproxy_certificate() -> flask.Response:
    response = flask.send_from_directory(
        app.template_folder,
        "mitmproxy-ca-cert.crt",
        mimetype="application/x-x509-ca-cert",
    )
    response.cache_control.max_age = 0
    return response


_MESSAGE_TYPE_MAP = {}
for sdesc in mahjongsoul_pb2.DESCRIPTOR.services_by_name.values():
    for mdesc in sdesc.methods:
        _MESSAGE_TYPE_MAP["." + mdesc.full_name] = (
            GetMessageClass(mdesc.input_type),
            GetMessageClass(mdesc.output_type),
        )
for tdesc in mahjongsoul_pb2.DESCRIPTOR.message_types_by_name.values():
    _MESSAGE_TYPE_MAP["." + tdesc.full_name] = (GetMessageClass(tdesc), None)


_SCALAR_VALUE_TYPE_NAME_MAP = {
    FieldDescriptor.TYPE_BOOL: "bool",
    FieldDescriptor.TYPE_BYTES: "bytes",
    FieldDescriptor.TYPE_DOUBLE: "double",
    FieldDescriptor.TYPE_ENUM: "enum",
    FieldDescriptor.TYPE_FIXED32: "fixed32",
    FieldDescriptor.TYPE_FIXED64: "fixed64",
    FieldDescriptor.TYPE_FLOAT: "float",
    FieldDescriptor.TYPE_INT32: "int32",
    FieldDescriptor.TYPE_INT64: "int64",
    FieldDescriptor.TYPE_SFIXED32: "sfixed32",
    FieldDescriptor.TYPE_SFIXED64: "sfixed64",
    FieldDescriptor.TYPE_SINT32: "sint32",
    FieldDescriptor.TYPE_SINT64: "sint64",
    FieldDescriptor.TYPE_STRING: "string",
    FieldDescriptor.TYPE_UINT32: "uint32",
    FieldDescriptor.TYPE_UINT64: "uint64",
}


def _unwrap(data: bytes) -> tuple[str, bytes]:
    parse = mahjongsoul_pb2.Wrapper()
    parse.ParseFromString(data)
    return (parse.name, parse.data)


def _get_field_type_name(desc: FieldDescriptor) -> str:
    mdesc = desc.message_type
    if mdesc is not None:
        return mdesc.name

    if desc.type not in _SCALAR_VALUE_TYPE_NAME_MAP:
        msg = f"""{desc.type}: An unknown field type."""
        raise RuntimeError(msg)

    return _SCALAR_VALUE_TYPE_NAME_MAP[desc.type]


def _message_to_fields(msg: Message) -> dict:
    fields = {}
    for fdesc, fval in msg.ListFields():
        fname = fdesc.name
        if fdesc.label == FieldDescriptor.LABEL_REPEATED:
            fields[fname] = {
                "wrapped": False,
                "type": _get_field_type_name(fdesc),
                "value": [_parse_impl(fdesc, e)["value"] for e in fval],
            }
        else:
            fields[fname] = _parse_impl(fdesc, fval)
    return fields


def _decode_bytes(buf: bytes) -> bytes:
    keys = [132, 94, 78, 66, 57, 162, 31, 96, 28]
    decode = bytearray()
    for i, _byte in enumerate(buf):
        mask = ((23 ^ len(buf)) + 5 * i + keys[i % len(keys)]) & 255
        _byte ^= mask
        decode += _byte.to_bytes(1, "little")
    return bytes(decode)


def _parse_action_prototype(msg: Message) -> Message | dict[str, Any]:
    if not isinstance(msg, mahjongsoul_pb2.ActionPrototype):
        return msg

    wrapped_msg: Message = getattr(mahjongsoul_pb2, msg.name)()
    try:
        wrapped_msg.ParseFromString(msg.data)
    except DecodeError:
        wrapped_msg.ParseFromString(_decode_bytes(msg.data))

    fields = _message_to_fields(wrapped_msg)

    return {
        "wrapped": False,
        "type": "ActionPrototype",
        "value": {
            "step": {
                "wrapped": False,
                "type": "uint32",
                "value": msg.step,
            },
            "name": {
                "wrapped": False,
                "type": "string",
                "value": msg.name,
            },
            "data": {
                "wrapped": True,
                "type": wrapped_msg.DESCRIPTOR.name,
                "value": fields,
            },
        },
    }


def _parse_impl(
    desc: FieldDescriptor,
    val: bytes | Message,
) -> Message | dict[str, Any]:
    if desc.message_type is not None:
        tdesc: Descriptor = desc.message_type
        if tdesc.full_name == "lq.ActionPrototype":
            return _parse_action_prototype(val)

    if isinstance(val, bytes):
        msg = mahjongsoul_pb2.Wrapper()
        try:
            msg.ParseFromString(val)
        except DecodeError:
            return {
                "wrapped": False,
                "type": "bytes",
                "value": base64.b64encode(val).decode("UTF-8"),
            }

        name = msg.name
        data = msg.data

        if name in _MESSAGE_TYPE_MAP:
            wrapped_msg: Message = _MESSAGE_TYPE_MAP[name][0]()
        else:
            return {
                "wrapped": False,
                "type": "bytes",
                "value": base64.b64encode(val).decode("UTF-8"),
            }

        wrapped_msg.ParseFromString(data)

        fields = _message_to_fields(wrapped_msg)

        return {
            "wrapped": False,
            "type": "Wrapper",
            "value": {
                "name": {
                    "wrapped": False,
                    "type": "string",
                    "value": name,
                },
                "data": {
                    "wrapped": True,
                    "type": wrapped_msg.DESCRIPTOR.name,
                    "value": fields,
                },
            },
        }

    if desc.type == FieldDescriptor.TYPE_MESSAGE:
        fields = _message_to_fields(val)

        return {
            "wrapped": False,
            "type": desc.message_type.name,
            "value": fields,
        }

    if desc.type not in _SCALAR_VALUE_TYPE_NAME_MAP:
        msg = f"""{desc.type}: An unknown field type."""
        raise RuntimeError(msg)

    return {
        "wrapped": False,
        "type": _SCALAR_VALUE_TYPE_NAME_MAP[desc.type],
        "value": val,
    }


def _parse_top_level(
    name: str,
    data: bytes,
    *,
    is_response: bool,
) -> Message | dict[str, Any]:
    if not is_response:
        msg: Message = _MESSAGE_TYPE_MAP[name][0]()
    else:
        msg: Message = _MESSAGE_TYPE_MAP[name][1]()

    try:
        msg.ParseFromString(data)
    except DecodeError as e:
        proc = subprocess.run(
            ["protoc", "--decode_raw"],  # noqa: S603, S607
            input=data,
            capture_output=True,
            check=False,
        )
        rc = proc.returncode
        stdout = proc.stdout.decode("UTF-8")
        stderr = proc.stderr.decode("UTF-8")
        error_msg = f"""name: {name}
is_response: {is_response}
returncode: {rc}
stdout: {stdout}
stderr: {stderr}"""
        raise RuntimeError(error_msg) from e

    if msg.DESCRIPTOR.full_name == "lq.ActionPrototype":
        return _parse_action_prototype(msg)

    fields = _message_to_fields(msg)

    return {
        "wrapped": False,
        "type": "Wrapper",
        "value": {
            "name": {
                "wrapped": False,
                "type": "string",
                "value": "" if is_response else name,
            },
            "data": {
                "wrapped": True,
                "type": msg.DESCRIPTOR.name,
                "value": fields,
            },
        },
    }


@app.route("/api-calls.json")
def fetch_api_calls() -> flask.Response:
    api_calls = []
    while True:
        api_call = _redis.lpop_websocket_message("api-call-queue")
        if api_call is None:
            break

        request_direction = api_call["request_direction"]
        timestamp = api_call["timestamp"]

        request = api_call["request"]
        if request[0] == 1:
            name, request_data = _unwrap(request[1:])
        elif request[0] == 2:
            name, request_data = _unwrap(request[3:])
        else:
            msg = f"""{request[0]}: An unknown type in a request."""
            raise RuntimeError(msg)
        request_parse = _parse_top_level(name, request_data, is_response=False)

        response = api_call["response"]
        response_parse = None
        if response is not None:
            if response[0] != 3:
                msg = f"""{response[0]}: An unknown type in a response."""
                raise RuntimeError(msg)
            _, response_data = _unwrap(response[3:])
            if _ != "":
                msg = f"""{_}: A response has a name."""
                raise RuntimeError(msg)
            response_parse = _parse_top_level(
                name,
                response_data,
                is_response=True,
            )
        elif request[0] != 1:
            msg = """A request does not expect any response but has one."""
            raise RuntimeError(msg)

        api_call = {
            "name": name,
            "request_direction": request_direction,
            "timestamp": int(timestamp.timestamp()),
            "request": request_parse,
            "response": response_parse,
        }
        api_calls.append(api_call)

    return flask.json.jsonify(api_calls)
