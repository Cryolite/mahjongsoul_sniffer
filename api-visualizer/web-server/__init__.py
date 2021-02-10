#!/usr/bin/env python3

import pathlib
import subprocess
import base64
from google.protobuf.message import DecodeError
from google.protobuf.descriptor import FieldDescriptor
from google.protobuf.message_factory import MessageFactory
import flask
from mahjongsoul_sniffer import mahjongsoul_pb2
import mahjongsoul_sniffer.redis as redis_


app = flask.Flask(__name__)


_HTML_PREFIX = pathlib.Path(
    '/opt/mahjongsoul-sniffer/api-visualizer/web-server/vue/dist')


_LOG_PREFIX = pathlib.Path(
    '/var/log/mahjongsoul-sniffer/api-visualizer')


_redis = redis_.Redis(module_name='api_visualizer')


@app.route('/')
def top_page():
    return flask.send_from_directory(
        _HTML_PREFIX, 'index.html', mimetype='text/html')


@app.route('/css/<path:filename>')
def css(filename):
    return flask.send_from_directory(
        _HTML_PREFIX / 'css', filename, mimetype='text/css')


@app.route('/img/<path:filename>')
def img(filename):
    return flask.send_from_directory(_HTML_PREFIX / 'img', filename)


@app.route('/js/<path:filename>')
def js(filename):
    return flask.send_from_directory(
        _HTML_PREFIX / 'js', filename, mimetype='text/javascript')


@app.route('/mitmproxy-ca-cert.crt')
def mitmproxy_certificate():
    response = flask.send_from_directory(
        _HTML_PREFIX, 'mitmproxy-ca-cert.crt',
        mimetype='application/x-x509-ca-cert')
    response.cache_control.max_age = 0
    return response


_MESSAGE_TYPE_MAP = {}
for sdesc in mahjongsoul_pb2.DESCRIPTOR.services_by_name.values():
    for mdesc in sdesc.methods:
        _MESSAGE_TYPE_MAP['.' + mdesc.full_name] \
            = (MessageFactory().GetPrototype(mdesc.input_type),
               MessageFactory().GetPrototype(mdesc.output_type))
for tdesc in mahjongsoul_pb2.DESCRIPTOR.message_types_by_name.values():
    _MESSAGE_TYPE_MAP['.' + tdesc.full_name] \
        = (MessageFactory().GetPrototype(tdesc), None)


_SCALAR_VALUE_TYPE_NAME_MAP = {
    FieldDescriptor.TYPE_BOOL: 'bool',
    FieldDescriptor.TYPE_BYTES: 'bytes',
    FieldDescriptor.TYPE_DOUBLE: 'double',
    FieldDescriptor.TYPE_ENUM: 'enum',
    FieldDescriptor.TYPE_FIXED32: 'fixed32',
    FieldDescriptor.TYPE_FIXED64: 'fixed64',
    FieldDescriptor.TYPE_FLOAT: 'float',
    FieldDescriptor.TYPE_INT32: 'int32',
    FieldDescriptor.TYPE_INT64: 'int64',
    FieldDescriptor.TYPE_SFIXED32: 'sfixed32',
    FieldDescriptor.TYPE_SFIXED64: 'sfixed64',
    FieldDescriptor.TYPE_SINT32: 'sint32',
    FieldDescriptor.TYPE_SINT64: 'sint64',
    FieldDescriptor.TYPE_STRING: 'string',
    FieldDescriptor.TYPE_UINT32: 'uint32',
    FieldDescriptor.TYPE_UINT64: 'uint64'
}


@app.route('/api-calls.json')
def fetch_api_calls():
    api_calls = []
    while True:
        api_call = _redis.lpop_websocket_message('api-call-queue')
        if api_call is None:
            break

        request_direction = api_call['request_direction']
        timestamp = api_call['timestamp']

        def unwrap(data: bytes):
            parse = mahjongsoul_pb2.Wrapper()
            parse.ParseFromString(data)
            return (parse.name, parse.data)

        def get_field_type_name(desc: FieldDescriptor) -> str:
            mdesc = desc.message_type
            if mdesc is not None:
                return mdesc.name

            if desc.type not in _SCALAR_VALUE_TYPE_NAME_MAP:
                raise RuntimeError(
                    f'''{desc.type}: An unknown field type.''')

            return _SCALAR_VALUE_TYPE_NAME_MAP[desc.type]

        def parse_action_prototype(msg: mahjongsoul_pb2.ActionPrototype):
            if not hasattr(mahjongsoul_pb2, msg.name):
                return msg

            wrapped_msg = getattr(mahjongsoul_pb2, msg.name)()
            wrapped_msg.ParseFromString(msg.data)

            fields = {}
            for fdesc, fval in wrapped_msg.ListFields():
                fname = fdesc.name
                if fdesc.label == FieldDescriptor.LABEL_REPEATED:
                    fields[fname] = {
                        'wrapped': False,
                        'type': get_field_type_name(fdesc),
                        'value': [
                            parse_impl(fdesc, e)['value'] for e in fval]
                    }
                else:
                    fields[fname] = parse_impl(fdesc, fval)

            return {
                'wrapped': False,
                'type': 'ActionPrototype',
                'value': {
                    'step': {
                        'wrapped': False,
                        'type': 'uint32',
                        'value': msg.step
                    },
                    'name': {
                        'wrapped': False,
                        'type': 'string',
                        'value': msg.name
                    },
                    'data': {
                        'wrapped': True,
                        'type': wrapped_msg.DESCRIPTOR.name,
                        'value': fields
                    }
                }
            }

        def parse_impl(desc, val):
            if desc.message_type is not None:
                tdesc = desc.message_type
                if tdesc.full_name == 'lq.ActionPrototype':
                    return parse_action_prototype(val)

            if isinstance(val, bytes):
                msg = mahjongsoul_pb2.Wrapper()
                try:
                    msg.ParseFromString(val)
                except DecodeError:
                    return {
                        'wrapped': False,
                        'type': 'bytes',
                        'value': base64.b64encode(val).decode('UTF-8')
                    }

                name = msg.name
                data = msg.data

                if name in _MESSAGE_TYPE_MAP:
                    wrapped_msg = _MESSAGE_TYPE_MAP[name][0]()
                else:
                    return {
                        'wrapped': False,
                        'type': 'bytes',
                        'value': base64.b64encode(val).decode('UTF-8')
                    }

                wrapped_msg.ParseFromString(data)

                fields = {}
                for fdesc, fval in wrapped_msg.ListFields():
                    fname = fdesc.name
                    if fdesc.label == FieldDescriptor.LABEL_REPEATED:
                        fields[fname] = {
                            'wrapped': False,
                            'type': get_field_type_name(fdesc),
                            'value': [
                                parse_impl(fdesc, e)['value'] for e in fval]
                        }
                    else:
                        fields[fname] = parse_impl(fdesc, fval)

                return {
                    'wrapped': False,
                    'type': 'Wrapper',
                    'value': {
                        'name': {
                            'wrapped': False,
                            'type': 'string',
                            'value': name
                        },
                        'data': {
                            'wrapped': True,
                            'type': wrapped_msg.DESCRIPTOR.name,
                            'value': fields
                        }
                    }
                }

            if desc.type == FieldDescriptor.TYPE_MESSAGE:
                fields = {}
                for fdesc, fval in val.ListFields():
                    fname = fdesc.name
                    if fdesc.label == FieldDescriptor.LABEL_REPEATED:
                        fields[fname] = {
                            'wrapped': False,
                            'type': get_field_type_name(fdesc),
                            'value': [
                                parse_impl(fdesc, e)['value'] for e in fval]
                        }
                    else:
                        fields[fname] = parse_impl(fdesc, fval)

                return {
                    'wrapped': False,
                    'type': desc.message_type.name,
                    'value': fields
                }

            if desc.type not in _SCALAR_VALUE_TYPE_NAME_MAP:
                raise RuntimeError(
                    f'''{desc.type}: An unknown field type.''')

            return {
                'wrapped': False,
                'type': _SCALAR_VALUE_TYPE_NAME_MAP[desc.type],
                'value': val
            }

        def parse_top_level(name: str, data: bytes, is_response: bool):
            if not is_response:
                msg = _MESSAGE_TYPE_MAP[name][0]()
            else:
                msg = _MESSAGE_TYPE_MAP[name][1]()

            try:
                msg.ParseFromString(data)
            except DecodeError as e:
                proc = subprocess.run(['protoc', '--decode_raw'],
                                      input=data, capture_output=True)
                rc = proc.returncode
                stdout = proc.stdout.decode('UTF-8')
                stderr = proc.stderr.decode('UTF-8')
                raise RuntimeError(f'''name: {name}
is_response: {is_response}
returncode: {rc}
stdout: {stdout}
stderr: {stderr}''')

            if msg.DESCRIPTOR.full_name == 'lq.ActionPrototype':
                return parse_action_prototype(msg)

            fields = {}
            for fdesc, fval in msg.ListFields():
                fname = fdesc.name
                if fdesc.label == FieldDescriptor.LABEL_REPEATED:
                    fields[fname] = {
                        'wrapped': False,
                        'type': get_field_type_name(fdesc),
                        'value': [
                            parse_impl(fdesc, e)['value'] for e in fval]
                    }
                else:
                    fields[fname] = parse_impl(fdesc, fval)

            return {
                'wrapped': False,
                'type': 'Wrapper',
                'value': {
                    'name': {
                        'wrapped': False,
                        'type': 'string',
                        'value': '' if is_response else name
                    },
                    'data': {
                        'wrapped': True,
                        'type': msg.DESCRIPTOR.name,
                        'value': fields
                    }
                }
            }

        request = api_call['request']
        if request[0] == 1:
            name, request_data = unwrap(request[1:])
        elif request[0] == 2:
            name, request_data = unwrap(request[3:])
        else:
            raise RuntimeError(
                f'''{request[0]}: An unknown type in a request.''')
        request_parse = parse_top_level(name, request_data, False)

        response = api_call['response']
        response_parse = None
        if response is not None:
            if response[0] != 3:
                raise RuntimeError(
                    f'''{response[0]}: An unknown type in a response.''')
            _, response_data = unwrap(response[3:])
            if _ != '':
                raise RuntimeError(f'''{_}: A response has a name.''')
            response_parse = parse_top_level(name, response_data, True)
        else:
            if request[0] != 1:
                raise RuntimeError(
                    f'''A request does not expect any response but has\
 one.''')

        api_call = {
            'name': name,
            'request_direction': request_direction,
            'timestamp': int(timestamp.timestamp()),
            'request': request_parse,
            'response': response_parse
        }
        api_calls.append(api_call)

    return flask.json.jsonify(api_calls)
