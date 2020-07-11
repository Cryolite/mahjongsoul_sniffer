import re
import inspect
import sys
import os
import logging
import mitmproxy.http
import mitmproxy.websocket

# This file is executed by `mitmdump' with `execfile'. Therefore, in order to
# import submodules under the directory where this file exists, we need some
# tricks. See http://stackoverflow.com/questions/3718657 for the details of
# the tricks used in the following lines.
THIS_FILENAME = inspect.getframeinfo(inspect.currentframe()).filename
THIS_DIR_PATH = os.path.dirname(os.path.abspath(THIS_FILENAME))
sys.path.append(THIS_DIR_PATH)
import mahjongsoul_sniffer.logging
import mahjongsoul_sniffer.sniffer.websocket


def ignore_http_flow(flow: mitmproxy.http.HTTPFlow) -> None:
    logging.info(f"Ignore an HTTP flow to `{flow.request.url}'.")


def on_websocket_handshake(flow: mitmproxy.http.HTTPFlow) -> None:
    logging.info(f"Websocket handshake to `{flow.request.url}'.")


__http_dispatcher = [
    (re.compile('^https://game\\.mahjongsoul\\.com/$'), ignore_http_flow),
    (re.compile('^https://game\\.mahjongsoul\\.com/version\\.json\\?'), ignore_http_flow),
    (re.compile('^https://game\\.mahjongsoul\\.com/favicon_en\\.ico$'), ignore_http_flow),
    (re.compile('^https://game\\.mahjongsoul\\.com/resversion\\d+\\.\\d+\\.\\d+\\.w\\.json$'), ignore_http_flow),
    (re.compile('^https://game\\.mahjongsoul\\.com/v\\d+\\.\\d+\\.\\d+\\.w/res/'), ignore_http_flow),
    (re.compile('^https://game\\.mahjongsoul\\.com/v\\d+\\.\\d+\\.\\d+\\.w/shader/'), ignore_http_flow),
    (re.compile('^https://game\\.mahjongsoul\\.com/v\\d+\\.\\d+\\.\\d+\\.w/bitmapfont/'), ignore_http_flow),
    (re.compile('^https://game\\.mahjongsoul\\.com/v\\d+\\.\\d+\\.\\d+\\.w/config\\.json$'), ignore_http_flow),
    (re.compile('^https://game\\.mahjongsoul\\.com/v\\d+\\.\\d+\\.\\d+\\.w/uiconfig/'), ignore_http_flow),
    (re.compile('^https://passport\\.mahjongsoul\\.com/js/'), ignore_http_flow),
    (re.compile('^https://game\\.mahjongsoul\\.com/v\\d+\\.\\d+\\.\\d+\\.w/jp/extendRes/'), ignore_http_flow),
    (re.compile('^https://game\\.mahjongsoul\\.com/v\\d+\\.\\d+\\.\\d+\\.w/audio/'), ignore_http_flow),
    (re.compile('^https://mjjpgs\\.mahjongsoul\\.com:8443/api/v0/recommend_list\\?'), ignore_http_flow),
    (re.compile('^https://game\\.mahjongsoul\\.com/v\\d+\\.\\d+\\.\\d+\\.w/scene/'), ignore_http_flow),
    (re.compile('^https://mjjpgs\\.mahjongsoul\\.com:9663/$'), on_websocket_handshake),
    (re.compile('^https://game\\.mahjongsoul\\.com/v\\d+\\.\\d+\\.\\d+\\.w/code\\.js$'), ignore_http_flow),
    (re.compile('^https://game\\.mahjongsoul\\.com/client_language\\.txt$'), ignore_http_flow),
    (re.compile('^https://game\\.mahjongsoul\\.com/v\\d+\\.\\d+\\.\\d+\\.w/user_xieyi/'), ignore_http_flow),
    (re.compile('^https://game\\.mahjongsoul\\.com/v\\d+\\.\\d+\\.\\d+\\.w/d3_prefab\\.json$'), ignore_http_flow),
    (re.compile('^https://passport\\.mahjongsoul\\.com/user/login$'), ignore_http_flow),
    (re.compile('^https://game\\.mahjongsoul\\.com/v\\d+\\.\\d+\\.\\d+\\.w/jp/myres2/'), ignore_http_flow)
]


def _do_response(flow: mitmproxy.http.HTTPFlow) -> None:
    request = flow.request

    if not request.host.endswith('.mahjongsoul.com'):
        return

    if False:
        # request.anticache: A method.
        # request.anticomp: A method.
        # request.constrain_encoding: A method.
        print(f'request.content = {request.content}')
        print(f'request.cookies = {request.cookies}')
        # request.copy: A method.
        print(f'request.data = {request.data}')
        # request.decode: A method.
        # request.encode: A method.
        print(f'request.first_line_format = {request.first_line_format}')
        # request.from_state(state): A method.
        print(f'request.get_state() = {request.get_state()}')
        print(f'request.get_text() = {request.get_text()}')
        print(f'request.headers = {request.headers}')
        print(f'request.host = {request.host}')
        print(f'request.host_header = {request.host_header}')
        print(f'request.http_version = {request.http_version}')
        print(f'request.is_replay = {request.is_replay}')
        # request.make: A method.
        print(f'request.method = {request.method}')
        print(f'request.multipart_form = {request.multipart_form}')
        print(f'request.path = {request.path}')
        print(f'request.path_components = {request.path_components}')
        print(f'request.port = {request.port}')
        print(f'request.pretty_host = {request.pretty_host}')
        print(f'request.pretty_url = {request.pretty_url}')
        print(f'request.query = {request.query}')
        print(f'request.raw_content = {request.raw_content}')
        # request.replace: A method.
        print(f'request.scheme = {request.scheme}')
        # request.set_content: A method.
        # request.set_state: A method.
        # request.set_text: A method.
        print(f'request.stream = {request.stream}')
        print(f'request.text = {request.text}')
        print(f'request.timestamp_end = {request.timestamp_end}')
        print(f'request.timestamp_start = {request.timestamp_start}')
        print(f'request.url = {request.url}')
        print(f'request.urlencoded_form = {request.urlencoded_form}')
        # request.wrap: A method.

    url = request.url
    default = True
    for pattern, target in __http_dispatcher:
        if pattern.search(url) is not None:
            target(flow)
            default = False
            break
    if default:
        raise RuntimeError(f"An HTTP flow to an unknown URL `{url}'.")


def response(flow: mitmproxy.http.HTTPFlow) -> None:
    try:
        _do_response(flow)
    except Exception:
        logging.exception('An exception was thrown while sniffering an HTTP'
                          f' flow to {flow.request.url}.')
        raise


__websocket_request_queue = {}


__websocket_dispatcher = [
    (re.compile(b'^\x02..\n\x12\\.lq\\.Lobby\\.heatbeat\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_heatbeat),
    (re.compile(b'^\x02..\n\x14\\.lq\\.Lobby\\.oauth2Auth\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_oauth2_auth),
    (re.compile(b'^\x02..\n\x15\\.lq\\.Lobby\\.oauth2Check\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_oauth2_check),
    (re.compile(b'^\x02..\n\x15\\.lq\\.Lobby\\.oauth2Login\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_oauth2_login),
    (re.compile(b'^\x02..\n\x19\\.lq\\.Lobby\\.fetchServerTime\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_server_time),
    (re.compile(b'^\x02..\n\x1d\\.lq\\.Lobby\\.fetchServerSettings\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_server_settings),
    (re.compile(b'^\x02..\n\x1d\\.lq\\.Lobby\\.fetchConnectionInfo\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_connection_info),
    (re.compile(b'^\x02..\n\x1d\\.lq\\.Lobby\\.fetchPhoneLoginBind\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_phone_login_bind),
    (re.compile(b'^\x02..\n\x1a\\.lq\\.Lobby\\.fetchClientValue\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_client_value),
    (re.compile(b'^\x02..\n\x19\\.lq\\.Lobby\\.fetchFriendList\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_friend_list),
    (re.compile(b'^\x02..\n\x1e\\.lq\\.Lobby\\.fetchFriendApplyList\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_friend_apply_list),
    (re.compile(b'^\x02..\n\x17\\.lq\\.Lobby\\.fetchMailInfo\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_mail_info),
    (re.compile(b'^\x02..\n\x18\\.lq\\.Lobby\\.fetchDailyTask\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_daily_task),
    (re.compile(b'^\x02..\n\x1d\\.lq\\.Lobby\\.fetchReviveCoinInfo\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_revive_coin_info),
    (re.compile(b'^\x02..\n\x18\\.lq\\.Lobby\\.fetchTitleList\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_title_list),
    (re.compile(b'^\x02..\n\x16\\.lq\\.Lobby\\.fetchBagInfo\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_bag_info),
    (re.compile(b'^\x02..\n\x17\\.lq\\.Lobby\\.fetchShopInfo\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_shop_info),
    (re.compile(b'^\x02..\n\x1b\\.lq\\.Lobby\\.fetchActivityList\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_activity_list),
    (re.compile(b'^\x02..\n\x22\\.lq\\.Lobby\\.fetchAccountActivityData\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_account_activity_data),
    (re.compile(b'^\x02..\n\x18\\.lq\\.Lobby\\.fetchVipReward\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_vip_reward),
    (re.compile(b'^\x02..\n\x1e\\.lq\\.Lobby\\.fetchMonthTicketInfo\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_month_ticket_info),
    (re.compile(b'^\x02..\n\x1d\\.lq\\.Lobby\\.fetchCommentSetting\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_comment_setting),
    (re.compile(b'^\x02..\n\x1e\\.lq\\.Lobby\\.fetchAccountSettings\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_account_settings),
    (re.compile(b'^\x02..\n\x1e\\.lq\\.Lobby\\.fetchModNicknameTime\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_mod_nickname_time),
    (re.compile(b'^\x02..\n\x13\\.lq\\.Lobby\\.fetchMisc\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_misc),
    (re.compile(b'^\x02..\n\x1b\\.lq\\.Lobby\\.fetchAnnouncement\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_announcement),
    (re.compile(b'^\x02..\n\x1c\\.lq\\.Lobby\\.fetchRollingNotice\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_rolling_notice),
    (re.compile(b'^\x02..\n\x1c\\.lq\\.Lobby\\.fetchCharacterInfo\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_character_info),
    (re.compile(b'^\x02..\n\x1d\\.lq\\.Lobby\\.fetchAllCommonViews\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_all_common_views),
    (re.compile(b'^\x02..\n\x26\\.lq\\.Lobby\\.fetchCollectedGameRecordList\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_collected_game_record_list),
    (re.compile(b'^\x02..\n\x13\\.lq\\.Lobby\\.loginBeat\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_login_beat),
    (re.compile(b'^\x02..\n\x1b\\.lq\\.Lobby\\.fetchGameLiveList\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_game_live_list),
    (re.compile(b'^\x02..\n\x1d\\.lq\\.Lobby\\.fetchGameRecordList\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_game_record_list),
    (re.compile(b'^\x02..\n\x19\\.lq\\.Lobby\\.fetchGameRecord\x12', flags=re.DOTALL), mahjongsoul_sniffer.sniffer.websocket.on_fetch_game_record)
]


def _do_websocket_message(flow: mitmproxy.websocket.WebSocketFlow) -> None:
    if False:
        # flow.backup: A method.
        print(f'flow.client_conn = {flow.client_conn}')
        print(f'flow.client_extensions = {flow.client_extensions}')
        print(f'flow.client_key = {flow.client_key}')
        print(f'flow.client_protocol = {flow.client_protocol}')
        print(f'flow.close_code = {flow.close_code}')
        print(f'flow.close_message = {flow.close_message}')
        print(f'flow.close_reason = {flow.close_reason}')
        print(f'flow.close_sender = {flow.close_sender}')
        # flow.copy: A method.
        print(f'flow.ended = {flow.ended}')
        print(f'flow.error = {flow.error}')
        # flow.from_state: A method.
        print(f'flow.get_state() = {flow.get_state()}')
        print(f'flow.handshake_flow = {flow.handshake_flow}')
        print(f'flow.id = {flow.id}')
        # flow.inject_message: A method.
        # flow.intercept: A method.
        print(f'flow.intercepted = {flow.intercepted}')
        # flow.kill: A method.
        print(f'flow.killable = {flow.killable}')
        print(f'flow.live = {flow.live}')
        print(f'flow.marked = {flow.marked}')
        # flow.message_info: A method.
        # print(f'flow.messages = {flow.messages}')
        print(f'flow.metadata = {flow.metadata}')
        print(f'flow.modified = {flow.modified}')
        print(f'flow.reply = {flow.reply}')
        # flow.resume: A method.
        # flow.revert: A method.
        print(f'flow.server_accept = {flow.server_accept}')
        print(f'flow.server_conn = {flow.server_conn}')
        print(f'flow.server_extensions = {flow.server_extensions}')
        print(f'flow.server_protocol = {flow.server_protocol}')
        # flow.set_state: A method.
        print(f'flow.stream = {flow.stream}')
        print(f'flow.type = {flow.type}')
        handshake_flow = flow.handshake_flow

    message = flow.messages[-1]
    if False:
        print(f'message.content = {message.content}')
        # message.copy: A method.
        print(f'message.from_client = {message.from_client}')
        # message.from_state: A method.
        print(f'message.get_state() = {message.get_state()}')
        # message.kill: A method.
        print(f'message.killed = {message.killed}')
        # message.set_state: A method.
        print(f'message.timestamp = {message.timestamp}')
        print(f'message.type = {message.type}')

    if type(message.content) != bytes:
        raise RuntimeError(f'An unknown WebSocket message: {message.content}')

    if len(message.content) < 3:
        raise RuntimeError(f'An unknown WebSocket message: {message.content}')

    message_type = message.content[0]
    message_number = int.from_bytes(message.content[1:3], byteorder='little')

    if message_type == 2:
        if not message.from_client:
            raise RuntimeError('An unknown WebSocket message from the server:'
                               f' {message.content}')

        if message_number in __websocket_request_queue:
            old_message = __websocket_request_queue[message_number]
            raise RuntimeError(f'''Two WebSocket messages of the same number.
Old message: {old_message.content}
New message: {message.content}''')

        __websocket_request_queue[message_number] = message
        return

    if message_type == 3:
        if message.from_client:
            raise RuntimeError('An unknown WebSocket message from the client:'
                               f' {message.content}')

        if message_number not in __websocket_request_queue:
            raise RuntimeError('No matching WebSocket request message is'
                               f' found: {message.content}')

        request_message = __websocket_request_queue[message_number]
        response_message = message
        del __websocket_request_queue[message_number]

        default = True
        for pattern, target in __websocket_dispatcher:
            if pattern.search(request_message.content) is not None:
                target(request_message, response_message)
                default = False
                break
        if default:
            raise RuntimeError(f'''Unknown WebSocket messages.
Request: {request_message.content}
Response: {response_message.content}''')


def websocket_message(flow: mitmproxy.websocket.WebSocketFlow) -> None:
    try:
        _do_websocket_message(flow)
    except Exception:
        handshake_flow = flow.handshake_flow
        handshake_request = handshake_flow.request
        handshake_url = handshake_request.url
        logging.exception('An exception was thrown while sniffering WebSocket '
                          f"messages from/to `{handshake_url}'.")
        raise
