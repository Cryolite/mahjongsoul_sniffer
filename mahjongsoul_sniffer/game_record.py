import datetime


class GameRecordPlaceholder:
    def __init__(self, *, uuid: str, start_time: datetime.datetime) -> None:
        self._uuid = (uuid,)
        self._start_time = start_time

    @property
    def uuid(self) -> str:
        return self._uuid

    @property
    def start_time(self) -> datetime.datetime:
        return self._start_time

    def to_json(self) -> object:
        return {
            "uuid": self._uuid,
            "start_time": self._start_time,
        }


class AccountLevel:
    def __init__(self, *, title: str, level: int, grading_point: int) -> None:
        if title not in ["初心", "雀士", "雀傑", "雀豪", "雀聖", "魂天"]:
            msg = (
                "`title` must be equal to either `初心`, `雀士`,"
                " `雀傑`, `雀豪`, `雀聖`, or `魂天`."
            )
            raise ValueError(msg)
        self._title = title

        if level < 1 or level > 3:
            msg = "`level` must be equal to either `1`, `2`, or `3`."
            raise ValueError(msg)
        self._level = level

        if grading_point < 0:
            msg = "`grading_point` must be a non-negative integer."
            raise ValueError(msg)
        self._grading_point = grading_point

    def to_json(self) -> object:
        return {
            "title": self._title,
            "level": self._level,
            "grading_point": self._grading_point,
        }


class Account:
    def __init__(
        self,
        *,
        id: int,
        nickname: str,
        level4: AccountLevel,
        level3: AccountLevel,
        final_base_score: int,
        final_total_score: int,
        delta_grading_point: int,
        delta_coin: int,
    ) -> None:
        if id < 0:
            msg = "`id` must be a non-negative integer"
            raise ValueError(msg)
        self._id = id

        self._nickname = nickname

        self._level4 = level4

        self._level3 = level3

        self._final_base_score = final_base_score

        self._final_total_score = final_total_score

        self._delta_grading_point = delta_grading_point

        self._delta_coin = delta_coin

    def to_json(self) -> object:
        return {
            "id": self._id,
            "nickname": self._nickname,
            "level4": self._level4.to_json(),
            "level3": self._level3.to_json(),
            "final_base_score": self._final_base_score,
            "final_total_score": self._final_total_score,
            "delta_grading_point": self._delta_grading_point,
            "delta_coin": self._delta_coin,
        }


class Seat:
    def __init__(self, index: int) -> None:
        if index < 0 or 4 <= index:
            msg = "`index` must be equal to either `0`, `1`, `2`, or `3`."
            raise ValueError(msg)
        self._index = index

    def __repr__(self) -> str:
        return str(self._index)

    def __eq__(self, other: int) -> bool:
        return self._index == other

    def to_json(self) -> int:
        return self._index


class Tile:
    def __init__(self, code: str) -> None:
        if code not in [
            "0m", "1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m",
            "0p", "1p", "2p", "3p", "4p", "5p", "6p", "7p", "8p", "9p",
            "0s", "1s", "2s", "3s", "4s", "5s", "6s", "7s", "8s", "9s",
            "1z", "2z", "3z", "4z", "5z", "6z", "7z",
        ]:  # fmt: skip
            msg = f"An invalid tile code `{code}`."
            raise ValueError(msg)
        self._code = code

    def __repr__(self) -> str:
        return self._code

    def __eq__(self, other: str) -> bool:
        return self._code == other

    def to_json(self) -> str:
        return self._code


class TingpaiInfo:
    def __init__(
        self,
        *,
        tile: Tile,
        has_yifan: bool,
        fu_zimo: int,
        fan_zimo: int,
        damanguan_zimo: bool,
        fu_rong: int,
        fan_rong: int,
        damanguan_rong: bool,
        biao_dora_count: int,
    ) -> None:
        self._tile = tile
        self._has_yifan = has_yifan

        if fu_zimo < 20:
            msg = f"{fu_zimo}: An invalid value for `fu_zimo`."
            raise ValueError(msg)
        self._fu_zimo = fu_zimo

        if fan_zimo < 0:
            msg = "`fan_zimo` must be a non-negative integer."
            raise ValueError(msg)
        self._fan_zimo = fan_zimo

        self._damanguan_zimo = damanguan_zimo

        if fu_rong < 25:
            msg = f"{fu_rong}: An invalid value for `fu_rong`."
            raise ValueError(msg)
        self._fu_rong = fu_rong

        if fan_rong < 0:
            msg = "`fan_rong` must be a non-negative integer."
            raise ValueError(msg)
        self._fan_rong = fan_rong

        self._damanguan_rong = damanguan_rong

        if biao_dora_count < 0:
            msg = "`biao_dora_count` must be a non-negative integer."
            raise ValueError(msg)
        self._biao_dora_count = biao_dora_count

    def to_json(self) -> object:
        return {
            "tile": self._tile.to_json(),
            "has_yifan": self._has_yifan,
            "fu_zimo": self._fu_zimo,
            "fan_zimo": self._fan_zimo,
            "damanguan_zimo": self._damanguan_zimo,
            "fu_rong": self._fu_rong,
            "fan_rong": self._fan_rong,
            "damanguan_rong": self._damanguan_rong,
            "biao_dora_count": self._biao_dora_count,
        }


class ZimoDapaiOption:
    def __init__(self, tiles: list[Tile]) -> None:
        self._tiles = tiles

    def to_json(self) -> object:
        return {"type": "打牌", "tiles": [t.to_json() for t in self._tiles]}


class ZimoAngangOption:
    def __init__(self, tiles: list[Tile]) -> None:
        if len(tiles) != 4:
            msg = "The length of `tiles` must be equal to 4."
            raise ValueError(msg)
        if tiles not in (
            ["0m", "0m", "0m", "0m"],
            ["1m", "1m", "1m", "1m"],
            ["2m", "2m", "2m", "2m"],
            ["3m", "3m", "3m", "3m"],
            ["4m", "4m", "4m", "4m"],
            ["0m", "5m", "5m", "5m"],
            ["5m", "5m", "5m", "0m"],
            ["6m", "6m", "6m", "6m"],
            ["7m", "7m", "7m", "7m"],
            ["8m", "8m", "8m", "8m"],
            ["9m", "9m", "9m", "9m"],
            ["0p", "0p", "0p", "0p"],
            ["1p", "1p", "1p", "1p"],
            ["2p", "2p", "2p", "2p"],
            ["3p", "3p", "3p", "3p"],
            ["4p", "4p", "4p", "4p"],
            ["0p", "5p", "5p", "5p"],
            ["5p", "5p", "5p", "0p"],
            ["6p", "6p", "6p", "6p"],
            ["7p", "7p", "7p", "7p"],
            ["8p", "8p", "8p", "8p"],
            ["9p", "9p", "9p", "9p"],
            ["0s", "0s", "0s", "0s"],
            ["1s", "1s", "1s", "1s"],
            ["2s", "2s", "2s", "2s"],
            ["3s", "3s", "3s", "3s"],
            ["4s", "4s", "4s", "4s"],
            ["0s", "5s", "5s", "5s"],
            ["5s", "5s", "5s", "0s"],
            ["6s", "6s", "6s", "6s"],
            ["7s", "7s", "7s", "7s"],
            ["8s", "8s", "8s", "8s"],
            ["9s", "9s", "9s", "9s"],
            ["1z", "1z", "1z", "1z"],
            ["2z", "2z", "2z", "2z"],
            ["3z", "3z", "3z", "3z"],
            ["4z", "4z", "4z", "4z"],
            ["5z", "5z", "5z", "5z"],
            ["6z", "6z", "6z", "6z"],
            ["7z", "7z", "7z", "7z"],
        ):
            msg = f"{tiles}: An invalid combination for Angang."
            raise ValueError(msg)
        self._tiles = tiles

    def to_json(self) -> object:
        return {
            "type": "暗槓",
            "tiles": [tile.to_json() for tile in self._tiles],
        }


class ZimoJiagangOption:
    def __init__(self, tiles: list[Tile]) -> None:
        if len(tiles) != 4:
            msg = "The length of `tiles` must be equal to 4."
            raise ValueError(msg)
        if tiles not in (
            ["0m", "0m", "0m", "0m"],
            ["1m", "1m", "1m", "1m"],
            ["2m", "2m", "2m", "2m"],
            ["3m", "3m", "3m", "3m"],
            ["4m", "4m", "4m", "4m"],
            ["0m", "5m", "5m", "5m"],
            ["5m", "5m", "5m", "0m"],
            ["6m", "6m", "6m", "6m"],
            ["7m", "7m", "7m", "7m"],
            ["8m", "8m", "8m", "8m"],
            ["9m", "9m", "9m", "9m"],
            ["0p", "0p", "0p", "0p"],
            ["1p", "1p", "1p", "1p"],
            ["2p", "2p", "2p", "2p"],
            ["3p", "3p", "3p", "3p"],
            ["4p", "4p", "4p", "4p"],
            ["0p", "5p", "5p", "5p"],
            ["5p", "5p", "5p", "0p"],
            ["6p", "6p", "6p", "6p"],
            ["7p", "7p", "7p", "7p"],
            ["8p", "8p", "8p", "8p"],
            ["9p", "9p", "9p", "9p"],
            ["0s", "0s", "0s", "0s"],
            ["1s", "1s", "1s", "1s"],
            ["2s", "2s", "2s", "2s"],
            ["3s", "3s", "3s", "3s"],
            ["4s", "4s", "4s", "4s"],
            ["0s", "5s", "5s", "5s"],
            ["5s", "5s", "5s", "0s"],
            ["6s", "6s", "6s", "6s"],
            ["7s", "7s", "7s", "7s"],
            ["8s", "8s", "8s", "8s"],
            ["9s", "9s", "9s", "9s"],
            ["1z", "1z", "1z", "1z"],
            ["2z", "2z", "2z", "2z"],
            ["3z", "3z", "3z", "3z"],
            ["4z", "4z", "4z", "4z"],
            ["5z", "5z", "5z", "5z"],
            ["6z", "6z", "6z", "6z"],
            ["7z", "7z", "7z", "7z"],
        ):
            msg = f"{tiles}: An invalid combination for Jiagang."
            raise ValueError(msg)
        self._tiles = tiles

    def to_json(self) -> object:
        return {
            "type": "加槓",
            "tiles": [tile.to_json() for tile in self._tiles],
        }


class ZimoLizhiOption:
    def __init__(self, tiles: list[Tile]) -> None:
        self._tiles = tiles

    def to_json(self) -> object:
        return {
            "type": "立直",
            "tiles": [tile.to_json() for tile in self._tiles],
        }


class ZimoHuOption:
    def __init__(self) -> None:
        pass

    def to_json(self) -> object:
        return {
            "type": "自摸和",
        }


class ZimoKyushukyuhaiOption:
    def __init__(self) -> None:
        pass

    def to_json(self) -> object:
        return {
            "type": "九種九牌",
        }


class ZimoOption:
    def __init__(
        self,
        option: ZimoDapaiOption
        | ZimoAngangOption
        | ZimoJiagangOption
        | ZimoLizhiOption
        | ZimoHuOption
        | ZimoKyushukyuhaiOption,
    ) -> None:
        self._option = option

    def to_json(self) -> object:
        return self._option.to_json()


class ZimoOptionPresence:
    def __init__(
        self,
        seat: Seat,
        options: list[ZimoOption],
        main_time: int,
        overtime: int,
    ) -> None:
        self._seat = seat
        self._options = options

        if main_time <= 0:
            msg = "`main_time` must be a positive integer."
            raise ValueError(msg)
        self._main_time = main_time

        if overtime < 0:
            msg = "`overtime` must be a non-negative integer."
            raise ValueError(msg)
        self._overtime = overtime

    def to_json(self) -> object:
        return {
            "seat": self._seat.to_json(),
            "options": [option.to_json() for option in self._options],
            "main_time": self._main_time,
            "overtime": self._overtime,
        }


class ZhentingInfo:
    def __init__(self, flags: list[bool]) -> None:
        if len(flags) != 4:
            msg = "The length of `flags` must be equal to 4."
            raise ValueError(msg)
        self._flags = flags

    def to_json(self) -> list[bool]:
        return self._flags


class Zimo:
    def __init__(
        self,
        *,
        seat: Seat,
        doras: list[Tile],
        tile: Tile,
        left_tile_count: int,
        option_presence: ZimoOptionPresence,
        zhenting: ZhentingInfo,
    ) -> None:
        self._seat = seat

        self._doras = doras

        self._tile = tile

        if left_tile_count < 0:
            msg = "`left_tile_count` must be a non-negative integer."
            raise ValueError(msg)
        self._left_tile_count = left_tile_count

        self._option_presence = option_presence

        self._zhenting = zhenting

    def to_json(self) -> object:
        result = {
            "type": "自摸",
            "seat": self._seat.to_json(),
            "tile": self._tile.to_json(),
            "left_tile_count": self._left_tile_count,
            "option_presence": self._option_presence.to_json(),
            "zhenting": self._zhenting.to_json(),
        }

        if len(self._doras) > 0:
            result["doras"] = [dora.to_json() for dora in self._doras]

        return result


class Chi:
    def __init__(
        self,
        *,
        seat: Seat,
        tiles: list[Tile],
        froms: list[Seat],
        zhenting: ZhentingInfo,
        option_presence: ZimoOptionPresence,
    ) -> None:
        self._seat = seat

        if len(tiles) != 3:
            msg = "The length of `tiles` must be equal to 3."
            raise ValueError(msg)
        if tiles not in (
            ["2m", "3m", "1m"],
            ["1m", "3m", "2m"],
            ["3m", "4m", "2m"],
            ["1m", "2m", "3m"],
            ["2m", "4m", "3m"],
            ["4m", "5m", "3m"],
            ["4m", "0m", "3m"],
            ["2m", "3m", "4m"],
            ["3m", "5m", "4m"],
            ["3m", "0m", "4m"],
            ["5m", "6m", "4m"],
            ["0m", "6m", "4m"],
            ["3m", "4m", "5m"],
            ["3m", "4m", "0m"],
            ["4m", "6m", "5m"],
            ["4m", "6m", "0m"],
            ["6m", "7m", "5m"],
            ["6m", "7m", "0m"],
            ["4m", "5m", "6m"],
            ["4m", "0m", "6m"],
            ["5m", "7m", "6m"],
            ["0m", "7m", "6m"],
            ["7m", "8m", "6m"],
            ["5m", "6m", "7m"],
            ["0m", "6m", "7m"],
            ["6m", "8m", "7m"],
            ["8m", "9m", "7m"],
            ["6m", "7m", "8m"],
            ["7m", "9m", "8m"],
            ["7m", "8m", "9m"],
            ["2p", "3p", "1p"],
            ["1p", "3p", "2p"],
            ["3p", "4p", "2p"],
            ["1p", "2p", "3p"],
            ["2p", "4p", "3p"],
            ["4p", "5p", "3p"],
            ["4p", "0p", "3p"],
            ["2p", "3p", "4p"],
            ["3p", "5p", "4p"],
            ["3p", "0p", "4p"],
            ["5p", "6p", "4p"],
            ["0p", "6p", "4p"],
            ["3p", "4p", "5p"],
            ["3p", "4p", "0p"],
            ["4p", "6p", "5p"],
            ["4p", "6p", "0p"],
            ["6p", "7p", "5p"],
            ["6p", "7p", "0p"],
            ["4p", "5p", "6p"],
            ["4p", "0p", "6p"],
            ["5p", "7p", "6p"],
            ["0p", "7p", "6p"],
            ["7p", "8p", "6p"],
            ["5p", "6p", "7p"],
            ["0p", "6p", "7p"],
            ["6p", "8p", "7p"],
            ["8p", "9p", "7p"],
            ["6p", "7p", "8p"],
            ["7p", "9p", "8p"],
            ["7p", "8p", "9p"],
            ["2s", "3s", "1s"],
            ["1s", "3s", "2s"],
            ["3s", "4s", "2s"],
            ["1s", "2s", "3s"],
            ["2s", "4s", "3s"],
            ["4s", "5s", "3s"],
            ["4s", "0s", "3s"],
            ["2s", "3s", "4s"],
            ["3s", "5s", "4s"],
            ["3s", "0s", "4s"],
            ["5s", "6s", "4s"],
            ["0s", "6s", "4s"],
            ["3s", "4s", "5s"],
            ["3s", "4s", "0s"],
            ["4s", "6s", "5s"],
            ["4s", "6s", "0s"],
            ["6s", "7s", "5s"],
            ["6s", "7s", "0s"],
            ["4s", "5s", "6s"],
            ["4s", "0s", "6s"],
            ["5s", "7s", "6s"],
            ["0s", "7s", "6s"],
            ["7s", "8s", "6s"],
            ["5s", "6s", "7s"],
            ["0s", "6s", "7s"],
            ["6s", "8s", "7s"],
            ["8s", "9s", "7s"],
            ["6s", "7s", "8s"],
            ["7s", "9s", "8s"],
            ["7s", "8s", "9s"],
        ):
            msg = f"{tiles}: An invalid tile combination for Chi."
            raise ValueError(msg)
        self._tiles = tiles

        if len(froms) != 3:
            msg = "The length of `froms` must be equal to 3."
            raise ValueError(msg)
        if froms not in ([0, 0, 3], [1, 1, 0], [2, 2, 1], [3, 3, 2]):
            msg = f"{froms}: An invalid seat combination for Chi."
            raise ValueError(msg)
        self._froms = froms

        self._zhenting = zhenting

        self._option_presence = option_presence

    def to_json(self) -> object:
        return {
            "type": "チー",
            "seat": self._seat.to_json(),
            "tiles": [tile.to_json() for tile in self._tiles],
            "froms": [s.to_json() for s in self._froms],
            "zhenting": self._zhenting.to_json(),
            "option_presence": self._option_presence.to_json(),
        }


class Peng:
    def __init__(
        self,
        *,
        seat: Seat,
        tiles: list[Tile],
        froms: list[Seat],
        zhenting: ZhentingInfo,
        option_presence: ZimoOptionPresence,
    ) -> None:
        self._seat = seat

        if len(tiles) != 3:
            msg = "The length of `tiles` must be equal to 3."
            raise ValueError(msg)
        if tiles not in (
            ["1m", "1m", "1m"],
            ["2m", "2m", "2m"],
            ["3m", "3m", "3m"],
            ["4m", "4m", "4m"],
            ["5m", "5m", "5m"],
            ["0m", "5m", "5m"],
            ["5m", "5m", "0m"],
            ["6m", "6m", "6m"],
            ["7m", "7m", "7m"],
            ["8m", "8m", "8m"],
            ["9m", "9m", "9m"],
            ["1p", "1p", "1p"],
            ["2p", "2p", "2p"],
            ["3p", "3p", "3p"],
            ["4p", "4p", "4p"],
            ["5p", "5p", "5p"],
            ["0p", "5p", "5p"],
            ["5p", "5p", "0p"],
            ["6p", "6p", "6p"],
            ["7p", "7p", "7p"],
            ["8p", "8p", "8p"],
            ["9p", "9p", "9p"],
            ["1s", "1s", "1s"],
            ["2s", "2s", "2s"],
            ["3s", "3s", "3s"],
            ["4s", "4s", "4s"],
            ["5s", "5s", "5s"],
            ["0s", "5s", "5s"],
            ["5s", "5s", "0s"],
            ["6s", "6s", "6s"],
            ["7s", "7s", "7s"],
            ["8s", "8s", "8s"],
            ["9s", "9s", "9s"],
            ["1z", "1z", "1z"],
            ["2z", "2z", "2z"],
            ["3z", "3z", "3z"],
            ["4z", "4z", "4z"],
            ["5z", "5z", "5z"],
            ["6z", "6z", "6z"],
            ["7z", "7z", "7z"],
        ):
            msg = f"{tiles}: An invalid tile combination for Peng."
            raise ValueError(msg)
        self._tiles = tiles

        if len(froms) != 3:
            msg = "The length of `froms` must be equal to 3."
            raise ValueError(msg)
        if froms not in (
            [0, 0, 1], [0, 0, 2], [0, 0, 3],
            [1, 1, 0], [1, 1, 2], [1, 1, 3],
            [2, 2, 0], [2, 2, 1], [2, 2, 3],
            [3, 3, 0], [3, 3, 1], [3, 3, 2],
        ):  # fmt: skip
            msg = f"{froms}: An invalid seat combination for Chi."
            raise ValueError(msg)
        self._froms = froms

        self._zhenting = zhenting

        self._option_presence = option_presence

    def to_json(self) -> object:
        return {
            "type": "ポン",
            "seat": self._seat.to_json(),
            "tiles": [tile.to_json() for tile in self._tiles],
            "froms": [s.to_json() for s in self._froms],
            "zhenting": self._zhenting.to_json(),
            "option_presence": self._option_presence.to_json(),
        }


class Daminggang:
    def __init__(
        self,
        seat: Seat,
        tiles: list[Tile],
        froms: list[Seat],
        zhenting: ZhentingInfo,
    ) -> None:
        self._seat = seat

        if len(tiles) != 4:
            msg = "The length of `tiles` must be equal to 4."
            raise ValueError(msg)
        if tiles not in (
            ["1m", "1m", "1m", "1m"],
            ["2m", "2m", "2m", "2m"],
            ["3m", "3m", "3m", "3m"],
            ["4m", "4m", "4m", "4m"],
            ["0m", "5m", "5m", "5m"],
            ["5m", "5m", "5m", "0m"],
            ["6m", "6m", "6m", "6m"],
            ["7m", "7m", "7m", "7m"],
            ["8m", "8m", "8m", "8m"],
            ["9m", "9m", "9m", "9m"],
            ["1p", "1p", "1p", "1p"],
            ["2p", "2p", "2p", "2p"],
            ["3p", "3p", "3p", "3p"],
            ["4p", "4p", "4p", "4p"],
            ["0p", "5p", "5p", "5p"],
            ["5p", "5p", "5p", "0p"],
            ["6p", "6p", "6p", "6p"],
            ["7p", "7p", "7p", "7p"],
            ["8p", "8p", "8p", "8p"],
            ["9p", "9p", "9p", "9p"],
            ["1s", "1s", "1s", "1s"],
            ["2s", "2s", "2s", "2s"],
            ["3s", "3s", "3s", "3s"],
            ["4s", "4s", "4s", "4s"],
            ["0s", "5s", "5s", "5s"],
            ["5s", "5s", "5s", "0s"],
            ["6s", "6s", "6s", "6s"],
            ["7s", "7s", "7s", "7s"],
            ["8s", "8s", "8s", "8s"],
            ["9s", "9s", "9s", "9s"],
            ["1z", "1z", "1z", "1z"],
            ["2z", "2z", "2z", "2z"],
            ["3z", "3z", "3z", "3z"],
            ["4z", "4z", "4z", "4z"],
            ["5z", "5z", "5z", "5z"],
            ["6z", "6z", "6z", "6z"],
            ["7z", "7z", "7z", "7z"],
        ):
            msg = f"{tiles}: An invalid tile combination for Gang."
            raise ValueError(msg)
        self._tiles = tiles

        if len(froms) != 4:
            msg = "The length of `froms` must be equal to 4."
            raise ValueError(msg)
        if froms not in (
            [0, 0, 0, 1], [0, 0, 0, 2], [0, 0, 0, 3],
            [1, 1, 1, 0], [1, 1, 1, 2], [1, 1, 1, 3],
            [2, 2, 2, 0], [2, 2, 2, 1], [2, 2, 2, 3],
            [3, 3, 3, 0], [3, 3, 3, 1], [3, 3, 3, 2],
        ):  # fmt: skip
            msg = f"{froms}: An invalid seat combination for Gang."
            raise ValueError(msg)
        self._froms = froms

        self._zhenting = zhenting

    def to_json(self) -> object:
        return {
            "type": "大明槓",
            "seat": self._seat.to_json(),
            "tiles": [tile.to_json() for tile in self._tiles],
            "froms": [s.to_json() for s in self._froms],
            "zhenting": self._zhenting.to_json(),
        }


class Angang:
    def __init__(self, *, seat: Seat, tile: Tile) -> None:
        self._seat = seat

        self._tile = tile

    def to_json(self) -> object:
        return {
            "type": "暗槓",
            "seat": self._seat.to_json(),
            "tile": self._tile.to_json(),
        }


class Jiagang:
    def __init__(self, *, seat: Seat, tile: Tile) -> None:
        self._seat = seat

        self._tile = tile

    def to_json(self) -> object:
        return {
            "type": "加槓",
            "seat": self._seat.to_json(),
            "tile": self._tile.to_json(),
        }


class DapaiChiOption:
    def __init__(self, tiles_list: list[list[Tile]]) -> None:
        for tiles in tiles_list:
            if len(tiles) != 2:
                msg = "The length of `tiles` must be equal to 2."
                raise ValueError(msg)
            if tiles not in (
                ["2m", "3m"],
                ["1m", "3m"], ["3m", "4m"],
                ["1m", "2m"], ["2m", "4m"], ["4m", "5m"], ["4m", "0m"],
                ["2m", "3m"], ["3m", "5m"], ["3m", "0m"], ["5m", "6m"], ["0m", "6m"],  # noqa: E501
                ["3m", "4m"], ["4m", "6m"], ["6m", "7m"],
                ["4m", "5m"], ["4m", "0m"], ["5m", "7m"], ["0m", "7m"], ["7m", "8m"],  # noqa: E501
                ["5m", "6m"], ["0m", "6m"], ["6m", "8m"], ["8m", "9m"],
                ["6m", "7m"], ["7m", "9m"],
                ["7m", "8m"],
                ["2p", "3p"],
                ["1p", "3p"], ["3p", "4p"],
                ["1p", "2p"], ["2p", "4p"], ["4p", "5p"], ["4p", "0p"],
                ["2p", "3p"], ["3p", "5p"], ["3p", "0p"], ["5p", "6p"], ["0p", "6p"],  # noqa: E501
                ["3p", "4p"], ["4p", "6p"], ["6p", "7p"],
                ["4p", "5p"], ["4p", "0p"], ["5p", "7p"], ["0p", "7p"], ["7p", "8p"],  # noqa: E501
                ["5p", "6p"], ["0p", "6p"], ["6p", "8p"], ["8p", "9p"],
                ["6p", "7p"], ["7p", "9p"],
                ["7p", "8p"],
                ["2s", "3s"],
                ["1s", "3s"], ["3s", "4s"],
                ["1s", "2s"], ["2s", "4s"], ["4s", "5s"], ["4s", "0s"],
                ["2s", "3s"], ["3s", "5s"], ["3s", "0s"], ["5s", "6s"], ["0s", "6s"],  # noqa: E501
                ["3s", "4s"], ["4s", "6s"], ["6s", "7s"],
                ["4s", "5s"], ["4s", "0s"], ["5s", "7s"], ["0s", "7s"], ["7s", "8s"],  # noqa: E501
                ["5s", "6s"], ["0s", "6s"], ["6s", "8s"], ["8s", "9s"],
                ["6s", "7s"], ["7s", "9s"],
                ["7s", "8s"],
            ):  # fmt: skip
                msg = f"{tiles}: An invalid tile combination for Chi."
                raise ValueError(msg)
        self._tiles_list = tiles_list

    def to_json(self) -> object:
        tiles_list = []
        for e in self._tiles_list:
            tiles = [tile.to_json() for tile in e]
            tiles_list.append(tiles)

        return {
            "type": "チー",
            "tiles_list": tiles_list,
        }


class DapaiPengOption:
    def __init__(self, tiles_list: list[list[Tile]]) -> None:
        for tiles in tiles_list:
            if len(tiles) != 2:
                msg = "The length of `tiles` must be equal to 2."
                raise ValueError(msg)
            if tiles not in (
                ["1m", "1m"],
                ["2m", "2m"],
                ["3m", "3m"],
                ["4m", "4m"],
                ["5m", "5m"], ["0m", "5m"],
                ["6m", "6m"],
                ["7m", "7m"],
                ["8m", "8m"],
                ["9m", "9m"],
                ["1p", "1p"],
                ["2p", "2p"],
                ["3p", "3p"],
                ["4p", "4p"],
                ["5p", "5p"], ["0p", "5p"],
                ["6p", "6p"],
                ["7p", "7p"],
                ["8p", "8p"],
                ["9p", "9p"],
                ["1s", "1s"],
                ["2s", "2s"],
                ["3s", "3s"],
                ["4s", "4s"],
                ["5s", "5s"], ["0s", "5s"],
                ["6s", "6s"],
                ["7s", "7s"],
                ["8s", "8s"],
                ["9s", "9s"],
                ["1z", "1z"],
                ["2z", "2z"],
                ["3z", "3z"],
                ["4z", "4z"],
                ["5z", "5z"],
                ["6z", "6z"],
                ["7z", "7z"],
            ):  # fmt: skip
                msg = f"{tiles}: An invalid tile combination for Peng."
                raise ValueError(msg)
        self._tiles_list = tiles_list

    def to_json(self) -> object:
        tiles_list = []
        for e in self._tiles_list:
            tiles = [tile.to_json() for tile in e]
            tiles_list.append(tiles)

        return {
            "type": "ポン",
            "tiles": tiles_list,
        }


class DapaiDaminggangOption:
    def __init__(self, tiles: list[Tile]) -> None:
        if len(tiles) != 3:
            msg = "The length of `tiles` must be equal to 2."
            raise ValueError(msg)
        if tiles not in (
            ["1m", "1m", "1m"],
            ["2m", "2m", "2m"],
            ["3m", "3m", "3m"],
            ["4m", "4m", "4m"],
            ["5m", "5m", "5m"],
            ["0m", "5m", "5m"],
            ["6m", "6m", "6m"],
            ["7m", "7m", "7m"],
            ["8m", "8m", "8m"],
            ["9m", "9m", "9m"],
            ["1p", "1p", "1p"],
            ["2p", "2p", "2p"],
            ["3p", "3p", "3p"],
            ["4p", "4p", "4p"],
            ["5p", "5p", "5p"],
            ["0p", "5p", "5p"],
            ["6p", "6p", "6p"],
            ["7p", "7p", "7p"],
            ["8p", "8p", "8p"],
            ["9p", "9p", "9p"],
            ["1s", "1s", "1s"],
            ["2s", "2s", "2s"],
            ["3s", "3s", "3s"],
            ["4s", "4s", "4s"],
            ["5s", "5s", "5s"],
            ["0s", "5s", "5s"],
            ["6s", "6s", "6s"],
            ["7s", "7s", "7s"],
            ["8s", "8s", "8s"],
            ["9s", "9s", "9s"],
            ["1z", "1z", "1z"],
            ["2z", "2z", "2z"],
            ["3z", "3z", "3z"],
            ["4z", "4z", "4z"],
            ["5z", "5z", "5z"],
            ["6z", "6z", "6z"],
            ["7z", "7z", "7z"],
        ):
            msg = f"{tiles}: An invalid tile combination for Peng."
            raise ValueError(msg)
        self._tiles = tiles

    def to_json(self) -> object:
        return {
            "type": "大明槓",
            "tiles": [tile.to_json() for tile in self._tiles],
        }


class DapaiRongOption:
    def __init__(self) -> None:
        pass

    def to_json(self) -> object:
        return {
            "type": "栄和",
        }


class DapaiOption:
    def __init__(
        self,
        option: DapaiChiOption
        | DapaiPengOption
        | DapaiDaminggangOption
        | DapaiRongOption,
    ) -> None:
        self._option = option

    def to_json(self) -> object:
        return self._option.to_json()


class DapaiOptionPresence:
    def __init__(
        self,
        *,
        seat: Seat,
        options: list[DapaiOption],
        main_time: int,
        overtime: int,
    ) -> None:
        self._seat = seat

        self._options = options

        if main_time <= 0:
            msg = "`main_time` must be a positive integer."
            raise ValueError(msg)
        self._main_time = main_time

        if overtime < 0:
            msg = "`overtime` must be a non-positive integer."
            raise ValueError(msg)
        self._overtime = overtime

    def to_json(self) -> object:
        return {
            "seat": self._seat.to_json(),
            "options": [option.to_json() for option in self._options],
            "main_time": self._main_time,
            "overtime": self._overtime,
        }


class Dapai:
    def __init__(
        self,
        *,
        seat: Seat,
        tile: Tile,
        moqie: bool,
        lizhi: bool,
        double_lizhi: bool,
        tingpai_list: list[TingpaiInfo],
        zhenting: ZhentingInfo,
        option_presence_list: list[DapaiOptionPresence],
        doras: list[Tile],
    ) -> None:
        self._seat = seat
        self._tile = tile
        self._moqie = moqie
        self._lizhi = lizhi
        self._double_lizhi = double_lizhi
        self._tingpai_list = tingpai_list
        self._zhenting = zhenting
        self._option_presence_list = option_presence_list
        self._doras = doras

    def to_json(self) -> object:
        result = {
            "type": "打牌",
            "tile": self._tile.to_json(),
            "moqie": self._moqie,
            "lizhi": self._lizhi,
            "double_lizhi": self._double_lizhi,
            "tingpai_list": [
                tingpai.to_json() for tingpai in self._tingpai_list
            ],
            "zhenting": self._zhenting.to_json(),
            "option_presence_list": [
                e.to_json() for e in self._option_presence_list
            ],
        }

        if len(self._doras) > 0:
            result["doras"] = [t.to_json() for t in self._doras]

        return result


class Shunzi:
    def __init__(self, tiles: list[Tile]) -> None:
        if len(tiles) != 3:
            msg = "The length of `tiles` must be equal to 3."
            raise ValueError(msg)
        if tiles not in (
            ["2m", "3m", "1m"],
            ["1m", "3m", "2m"],
            ["3m", "4m", "2m"],
            ["1m", "2m", "3m"],
            ["2m", "4m", "3m"],
            ["4m", "5m", "3m"],
            ["4m", "0m", "3m"],
            ["2m", "3m", "4m"],
            ["3m", "5m", "4m"],
            ["3m", "0m", "4m"],
            ["5m", "6m", "4m"],
            ["0m", "6m", "4m"],
            ["3m", "4m", "5m"],
            ["3m", "4m", "0m"],
            ["4m", "6m", "5m"],
            ["4m", "6m", "0m"],
            ["6m", "7m", "5m"],
            ["6m", "7m", "0m"],
            ["4m", "5m", "6m"],
            ["4m", "0m", "6m"],
            ["5m", "7m", "6m"],
            ["0m", "7m", "6m"],
            ["7m", "8m", "6m"],
            ["5m", "6m", "7m"],
            ["0m", "6m", "7m"],
            ["6m", "8m", "7m"],
            ["8m", "9m", "7m"],
            ["6m", "7m", "8m"],
            ["7m", "9m", "8m"],
            ["7m", "8m", "9m"],
            ["2p", "3p", "1p"],
            ["1p", "3p", "2p"],
            ["3p", "4p", "2p"],
            ["1p", "2p", "3p"],
            ["2p", "4p", "3p"],
            ["4p", "5p", "3p"],
            ["4p", "0p", "3p"],
            ["2p", "3p", "4p"],
            ["3p", "5p", "4p"],
            ["3p", "0p", "4p"],
            ["5p", "6p", "4p"],
            ["0p", "6p", "4p"],
            ["3p", "4p", "5p"],
            ["3p", "4p", "0p"],
            ["4p", "6p", "5p"],
            ["4p", "6p", "0p"],
            ["6p", "7p", "5p"],
            ["6p", "7p", "0p"],
            ["4p", "5p", "6p"],
            ["4p", "0p", "6p"],
            ["5p", "7p", "6p"],
            ["0p", "7p", "6p"],
            ["7p", "8p", "6p"],
            ["5p", "6p", "7p"],
            ["0p", "6p", "7p"],
            ["6p", "8p", "7p"],
            ["8p", "9p", "7p"],
            ["6p", "7p", "8p"],
            ["7p", "9p", "8p"],
            ["7p", "8p", "9p"],
            ["2s", "3s", "1s"],
            ["1s", "3s", "2s"],
            ["3s", "4s", "2s"],
            ["1s", "2s", "3s"],
            ["2s", "4s", "3s"],
            ["4s", "5s", "3s"],
            ["4s", "0s", "3s"],
            ["2s", "3s", "4s"],
            ["3s", "5s", "4s"],
            ["3s", "0s", "4s"],
            ["5s", "6s", "4s"],
            ["0s", "6s", "4s"],
            ["3s", "4s", "5s"],
            ["3s", "4s", "0s"],
            ["4s", "6s", "5s"],
            ["4s", "6s", "0s"],
            ["6s", "7s", "5s"],
            ["6s", "7s", "0s"],
            ["4s", "5s", "6s"],
            ["4s", "0s", "6s"],
            ["5s", "7s", "6s"],
            ["0s", "7s", "6s"],
            ["7s", "8s", "6s"],
            ["5s", "6s", "7s"],
            ["0s", "6s", "7s"],
            ["6s", "8s", "7s"],
            ["8s", "9s", "7s"],
            ["6s", "7s", "8s"],
            ["7s", "9s", "8s"],
            ["7s", "8s", "9s"],
        ):
            msg = f"{tiles}: An invalid combination for Shunzi."
            raise ValueError(msg)
        self._tiles = tiles

    def to_json(self) -> object:
        return {
            "type": "順子",
            "tiles": [tile.to_json() for tile in self._tiles],
        }


class Kezi:
    def __init__(self, tiles: list[Tile]) -> None:
        if len(tiles) != 3:
            msg = "The length of `tiles` must be equal to 3."
            raise ValueError(msg)
        if tiles not in (
            ["1m", "1m", "1m"],
            ["2m", "2m", "2m"],
            ["3m", "3m", "3m"],
            ["4m", "4m", "4m"],
            ["5m", "5m", "5m"],
            ["0m", "5m", "5m"],
            ["5m", "5m", "0m"],
            ["6m", "6m", "6m"],
            ["7m", "7m", "7m"],
            ["8m", "8m", "8m"],
            ["9m", "9m", "9m"],
            ["1p", "1p", "1p"],
            ["2p", "2p", "2p"],
            ["3p", "3p", "3p"],
            ["4p", "4p", "4p"],
            ["5p", "5p", "5p"],
            ["0p", "5p", "5p"],
            ["5p", "5p", "0p"],
            ["6p", "6p", "6p"],
            ["7p", "7p", "7p"],
            ["8p", "8p", "8p"],
            ["9p", "9p", "9p"],
            ["1s", "1s", "1s"],
            ["2s", "2s", "2s"],
            ["3s", "3s", "3s"],
            ["4s", "4s", "4s"],
            ["5s", "5s", "5s"],
            ["0s", "5s", "5s"],
            ["5s", "5s", "0s"],
            ["6s", "6s", "6s"],
            ["7s", "7s", "7s"],
            ["8s", "8s", "8s"],
            ["9s", "9s", "9s"],
            ["1z", "1z", "1z"],
            ["2z", "2z", "2z"],
            ["3z", "3z", "3z"],
            ["4z", "4z", "4z"],
            ["5z", "5z", "5z"],
            ["6z", "6z", "6z"],
            ["7z", "7z", "7z"],
        ):
            msg = f"{tiles}: An invalid combination for Kezi."
            raise ValueError(msg)
        self._tiles = tiles

    def to_json(self) -> object:
        return {
            "type": "刻子",
            "tiles": [tile.to_json() for tile in self._tiles],
        }


class Minggangzi:
    def __init__(self, tiles: list[Tile]) -> None:
        if len(tiles) != 4:
            msg = "The length of `tiles` must be equal to 4."
            raise ValueError(msg)
        if tiles not in (
            ["1m", "1m", "1m", "1m"],
            ["2m", "2m", "2m", "2m"],
            ["3m", "3m", "3m", "3m"],
            ["4m", "4m", "4m", "4m"],
            ["5m", "5m", "5m", "5m"],
            ["0m", "5m", "5m", "5m"],
            ["6m", "6m", "6m", "6m"],
            ["7m", "7m", "7m", "7m"],
            ["8m", "8m", "8m", "8m"],
            ["9m", "9m", "9m", "9m"],
            ["1p", "1p", "1p", "1p"],
            ["2p", "2p", "2p", "2p"],
            ["3p", "3p", "3p", "3p"],
            ["4p", "4p", "4p", "4p"],
            ["5p", "5p", "5p", "5p"],
            ["0p", "5p", "5p", "5p"],
            ["6p", "6p", "6p", "6p"],
            ["7p", "7p", "7p", "7p"],
            ["8p", "8p", "8p", "8p"],
            ["9p", "9p", "9p", "9p"],
            ["1s", "1s", "1s", "1s"],
            ["2s", "2s", "2s", "2s"],
            ["3s", "3s", "3s", "3s"],
            ["4s", "4s", "4s", "4s"],
            ["5s", "5s", "5s", "5s"],
            ["0s", "5s", "5s", "5s"],
            ["6s", "6s", "6s", "6s"],
            ["7s", "7s", "7s", "7s"],
            ["8s", "8s", "8s", "8s"],
            ["9s", "9s", "9s", "9s"],
            ["1z", "1z", "1z", "1z"],
            ["2z", "2z", "2z", "2z"],
            ["3z", "3z", "3z", "3z"],
            ["4z", "4z", "4z", "4z"],
            ["5z", "5z", "5z", "5z"],
            ["6z", "6z", "6z", "6z"],
            ["7z", "7z", "7z", "7z"],
        ):
            msg = f"{tiles}: An invalid combination for Minggangzi."
            raise ValueError(msg)
        self._tiles = tiles

    def to_json(self) -> object:
        return {
            "type": "明槓子",
            "tiles": [tile.to_json() for tile in self._tiles],
        }


class Angangzi:
    def __init__(self, tiles: list[Tile]) -> None:
        if len(tiles) != 4:
            msg = "The length of `tiles` must be equal to 4."
            raise ValueError(msg)
        if tiles not in (
            ["1m", "1m", "1m", "1m"],
            ["2m", "2m", "2m", "2m"],
            ["3m", "3m", "3m", "3m"],
            ["4m", "4m", "4m", "4m"],
            ["5m", "5m", "5m", "5m"],
            ["0m", "5m", "5m", "5m"],
            ["6m", "6m", "6m", "6m"],
            ["7m", "7m", "7m", "7m"],
            ["8m", "8m", "8m", "8m"],
            ["9m", "9m", "9m", "9m"],
            ["1p", "1p", "1p", "1p"],
            ["2p", "2p", "2p", "2p"],
            ["3p", "3p", "3p", "3p"],
            ["4p", "4p", "4p", "4p"],
            ["5p", "5p", "5p", "5p"],
            ["0p", "5p", "5p", "5p"],
            ["6p", "6p", "6p", "6p"],
            ["7p", "7p", "7p", "7p"],
            ["8p", "8p", "8p", "8p"],
            ["9p", "9p", "9p", "9p"],
            ["1s", "1s", "1s", "1s"],
            ["2s", "2s", "2s", "2s"],
            ["3s", "3s", "3s", "3s"],
            ["4s", "4s", "4s", "4s"],
            ["5s", "5s", "5s", "5s"],
            ["0s", "5s", "5s", "5s"],
            ["6s", "6s", "6s", "6s"],
            ["7s", "7s", "7s", "7s"],
            ["8s", "8s", "8s", "8s"],
            ["9s", "9s", "9s", "9s"],
            ["1z", "1z", "1z", "1z"],
            ["2z", "2z", "2z", "2z"],
            ["3z", "3z", "3z", "3z"],
            ["4z", "4z", "4z", "4z"],
            ["5z", "5z", "5z", "5z"],
            ["6z", "6z", "6z", "6z"],
            ["7z", "7z", "7z", "7z"],
        ):
            msg = f"{tiles}: An invalid combination for Angangzi."
            raise ValueError(msg)
        self._tiles = tiles

    def to_json(self) -> object:
        return {
            "type": "暗槓子",
            "tiles": [tile.to_json() for tile in self._tiles],
        }


class Ming:
    def __init__(
        self,
        ming: Shunzi | Kezi | Minggangzi | Angangzi,
    ) -> None:
        self._ming = ming

    def to_json(self) -> object:
        return self._ming.to_json()


class Hupai:
    def __init__(self, *, title: str, fan: int) -> None:  # noqa: C901
        match title:
            case "門前清自摸和":
                if fan != 1:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "立直":
                if fan != 1:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "槍槓":
                if fan != 1:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "嶺上開花":
                if fan != 1:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "海底摸月":
                if fan != 1:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "河底撈魚":
                if fan != 1:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "役牌白":
                if fan != 1:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "役牌發":
                if fan != 1:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "役牌中":
                if fan != 1:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "役牌:自風牌":
                if fan != 1:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "役牌:場風牌":
                if fan != 1:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "断幺九":
                if fan != 1:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "一盃口":
                if fan != 1:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "平和":
                if fan != 1:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "混全帯幺九":
                if fan not in [2, 1]:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "一気通貫":
                if fan not in [2, 1]:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "三色同順":
                if fan not in [2, 1]:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "ダブル立直":
                if fan != 2:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "三色同刻":
                if fan != 2:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "三槓子":
                if fan != 2:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "対々和":
                if fan != 2:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "三暗刻":
                if fan != 2:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "小三元":
                if fan != 2:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "混老頭":
                if fan != 2:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "七対子":
                if fan != 2:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "純全帯幺九":
                if fan not in [3, 2]:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "混一色":
                if fan not in [3, 2]:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "二盃口":
                if fan != 3:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "清一色":
                if fan not in [6, 5]:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "一発":
                if fan != 1:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "ドラ":
                if fan < 1:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "赤ドラ":
                if fan < 1:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "裏ドラ":
                if fan < 1:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "流し満貫":
                msg = f"title == {title}, fan == {fan}"
                raise NotImplementedError(msg)
            case "天和":
                msg = f"title == {title}, fan == {fan}"
                raise NotImplementedError(msg)
            case "地和":
                msg = f"title == {title}, fan == {fan}"
                raise NotImplementedError(msg)
            case "大三元":
                msg = f"title == {title}, fan == {fan}"
                raise NotImplementedError(msg)
            case "四暗刻":
                if fan != 1:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "字一色":
                msg = f"title == {title}, fan == {fan}"
                raise NotImplementedError(msg)
            case "緑一色":
                msg = f"title == {title}, fan == {fan}"
                raise NotImplementedError(msg)
            case "清老頭":
                msg = f"title == {title}, fan == {fan}"
                raise NotImplementedError(msg)
            case "国士無双":
                msg = f"title == {title}, fan == {fan}"
                raise NotImplementedError(msg)
            case "小四喜":
                if fan != 1:
                    msg = (
                        f"title == {title}, fan == {fan}:"
                        " An invalid combination."
                    )
                    raise ValueError(msg)
            case "四槓子":
                msg = f"title == {title}, fan == {fan}"
                raise NotImplementedError(msg)
            case "九蓮宝燈":
                msg = f"title == {title}, fan == {fan}"
                raise NotImplementedError(msg)
            case "純正九蓮宝燈":
                msg = f"title == {title}, fan == {fan}"
                raise NotImplementedError(msg)
            case "四暗刻単騎":
                msg = f"title == {title}, fan == {fan}"
                raise NotImplementedError(msg)
            case "国士無双十三面待ち":
                msg = f"title == {title}, fan == {fan}"
                raise NotImplementedError(msg)
            case "大四喜":
                msg = f"title == {title}, fan == {fan}"
                raise NotImplementedError(msg)
            case _:
                msg = f"{title}: An invalid value for `title`."
                raise ValueError(msg)

        self._title = title
        self._fan = fan

    def to_json(self) -> object:
        return {
            "title": self._title,
            "fan": self._fan,
        }


class Hule:
    def __init__(  # noqa: C901
        self,
        *,
        seat: Seat,
        zhuangjia: bool,
        hand: list[Tile],
        ming_list: list[Ming],
        hupai: Tile,
        lizhi: bool,
        zimo: bool,
        doras: list[Tile],
        li_doras: list[Tile],
        fu: int,
        hupai_list: list[Hupai],
        fan: int,
        fan_title: str | None,
        damanguan: bool,
        point_rong: int | None,
        point_zimo_zhuangjia: int | None,
        point_zimo_sanjia: int | None,
    ) -> None:
        self._seat = seat
        self._zhuangjia = zhuangjia

        if len(hand) not in (13, 10, 7, 4, 1):
            msg = f"An invalid value for `hand`: {hand}"
            raise ValueError(msg)
        self._hand = hand

        if len(ming_list) not in (0, 1, 2, 3, 4):
            msg = f"An invalid value for `ming_list`: {ming_list})"
            raise ValueError(msg)
        if len(hand) + 3 * len(ming_list) != 13:
            msg = (
                "An invalid combination of `hand` and `ming_list`:"
                f" hand == {hand}, ming_list == {ming_list}"
            )
            raise ValueError(msg)
        self._ming_list = ming_list

        self._hupai = hupai
        self._lizhi = lizhi
        self._zimo = zimo
        self._doras = doras
        self._li_doras = li_doras

        if fu < 20:
            msg = f"{fu}: An invalid value for `fu`."
            raise ValueError(msg)
        self._fu = fu

        self._hupai_list = hupai_list

        if fan < 1:
            msg = f"{fan}: An invalid value for `fan`."
            raise ValueError(msg)
        self._fan = fan

        if fan_title is not None:
            if fan_title not in ("満貫", "跳満", "倍満", "三倍満", "役満"):
                msg = f"{fan_title}: An invalid value for `fan_title`."
                raise ValueError(msg)
        self._fan_title = fan_title

        self._damanguan = damanguan

        if zimo:
            if point_rong is not None:
                msg = f"{point_rong}: An invalid value."
                raise ValueError(msg)
            if point_zimo_sanjia is None:
                msg = f"{point_zimo_sanjia}: An invalid value."
                raise ValueError(msg)
            if zhuangjia and point_zimo_zhuangjia is not None:
                msg = f"{point_zimo_zhuangjia}: An invalid value."
                raise ValueError(msg)
        else:
            if point_zimo_zhuangjia is not None:
                msg = f"{point_zimo_zhuangjia}: An invalid value."
                raise ValueError(msg)
            if point_zimo_sanjia is not None:
                msg = f"{point_zimo_sanjia}: An invalid value."
                raise ValueError(msg)
            if point_rong is None:
                msg = f"{point_rong}: An invalid value."
                raise ValueError(msg)
        self._point_rong = point_rong
        self._point_zimo_zhuangjia = point_zimo_zhuangjia
        self._point_zimo_sanjia = point_zimo_sanjia

    def to_json(self) -> object:
        result = {
            "seat": self._seat.to_json(),
            "zhuangjia": self._zhuangjia,
            "hand": [tile.to_json() for tile in self._hand],
            "ming_list": [ming.to_json() for ming in self._ming_list],
            "hupai": self._hupai.to_json(),
            "lizhi": self._lizhi,
            "zimo": self._zimo,
            "doras": [dora.to_json() for dora in self._doras],
            "li_doras": [li_dora.to_json() for li_dora in self._li_doras],
            "fu": self._fu,
            "hupai_list": [hupai.to_json() for hupai in self._hupai_list],
            "fan": self._fan,
            "damanguan": self._damanguan,
        }

        if self._fan_title is not None:
            result["fan_title"] = self._fan_title
        if self._point_rong is not None:
            result["point_rong"] = self._point_rong
        if self._point_zimo_zhuangjia is not None:
            result["point_zimo_zhuangjia"] = self._point_zimo_zhuangjia
        if self._point_zimo_sanjia is not None:
            result["point_zimo_sanjia"] = self._point_zimo_sanjia

        return result


class RoundEndByHule:
    def __init__(
        self,
        *,
        hule_list: list[Hule],
        old_scores: list[int],
        delta_scores: list[int],
        new_scores: list[int],
    ) -> None:
        self._hule_list = hule_list

        if len(old_scores) != 4:
            msg = "The length of `old_scores` must be equal to 4."
            raise ValueError(msg)
        self._old_scores = old_scores

        if len(delta_scores) != 4:
            msg = "The length of `delta_scores` must be equal to 4."
            raise ValueError(msg)
        self._delta_scores = delta_scores

        if len(new_scores) != 4:
            msg = "The length of `new_socres` must be equal to 4."
            raise ValueError(msg)
        self._new_scores = new_scores

    def to_json(self) -> object:
        return {
            "type": "和了",
            "hule_list": [hule.to_json() for hule in self._hule_list],
            "old_scores": self._old_scores,
            "delta_scores": self._delta_scores,
            "new_scores": self._new_scores,
        }


class PlayerResultOnNoTile:
    def __init__(
        self,
        *,
        tingpai: bool,
        hand: list[Tile] | None,
        tingpai_list: list[TingpaiInfo],
        old_score: int,
        delta_score: int,
    ) -> None:
        self._tingpai = tingpai

        if tingpai != (hand is not None):
            msg = "Inconsistency between `tingpai` and `hand`."
            raise ValueError(msg)
        self._hand = hand

        if tingpai != (len(tingpai_list) >= 1):
            msg = "Inconsistency between `tingpai` and `tingpai_list`."
            raise ValueError(msg)
        self._tingpai_list = tingpai_list

        self._old_score = old_score
        self._delta_score = delta_score

    def to_json(self) -> object:
        tingpai_list = [tingpai.to_json() for tingpai in self._tingpai_list]
        result = {
            "tingpai": self._tingpai,
            "tingpai_list": tingpai_list,
            "old_score": self._old_score,
            "delta_score": self._delta_score,
        }

        if self._hand is not None:
            result["hand"] = [tile.to_json() for tile in self._hand]

        return result


class NoTile:
    def __init__(
        self,
        *,
        liujumanguan: bool,
        player_results: list[PlayerResultOnNoTile],
    ) -> None:
        self._liujumanguan = liujumanguan

        if len(player_results) != 4:
            msg = "The length of `player_results` must be equal to 4."
            raise ValueError(msg)
        self._player_results = player_results

    def to_json(self) -> object:
        return {
            "type": "荒牌平局",
            "liujumanguan": self._liujumanguan,
            "player_results": [
                player_result.to_json()
                for player_result in self._player_results
            ],
        }


class Kyushukyuhai:
    def __init__(self, *, seat: Seat, hand: list[Tile]) -> None:
        self._seat = seat

        if len(hand) != 14:
            msg = "The length of `hand` must be equal to 14."
            raise ValueError(msg)
        self._hand = hand

    def to_json(self) -> object:
        return {
            "type": "九種九牌",
            "hand": [tile.to_json() for tile in self._hand],
        }


class Sifengzilianda:
    def __init__(self) -> None:
        pass

    def to_json(self) -> object:
        return {
            "type": "四風子連打",
        }


class Turn:
    def __init__(
        self,
        turn: Zimo
        | Chi
        | Peng
        | Daminggang
        | Dapai
        | Angang
        | Jiagang
        | RoundEndByHule
        | NoTile
        | Kyushukyuhai
        | Sifengzilianda,
    ) -> None:
        self._turn = turn

    def to_json(self) -> object:
        return self._turn.to_json()


class GameRound:
    def __init__(  # noqa: C901
        self,
        *,
        chang: str,
        ju: int,
        ben: int,
        lizhibang: int,
        initial_scores: list[int],
        qipai_list: list[list[Tile]],
        paishan: list[Tile],
        paishan_code: str,
        dora: Tile,
        left_tile_count: int,
        tingpai_list: list[tuple[Seat, TingpaiInfo]],
        option_presence: ZimoOptionPresence,
    ) -> None:
        if chang not in ["東", "南", "西"]:
            msg = "`chang` must be equal to either `東`, `南`, or `西`."
            raise ValueError(msg)
        self._chang = chang

        if ju < 0 or ju >= 4:
            msg = "`ju` must be equal to either `0`, `1`, `2`, or `3`."
            raise ValueError(msg)
        self._ju = ju

        if ben < 0:
            msg = "`ben` must be a non-negative integer."
            raise ValueError(msg)
        self._ben = ben

        if lizhibang < 0:
            msg = "`lizhibang` must be a non-negative integer."
            raise ValueError(msg)
        self._lizhibang = lizhibang

        if len(initial_scores) != 4:
            msg = "The length of `initial_scores` must be equal to 4."
            raise ValueError(msg)
        for initial_score in initial_scores:
            if initial_score < 0:
                msg = (
                    "All the elements in `initial_scores` must be"
                    " a non-negative integer."
                )
                raise ValueError(msg)
        self._initial_scores = initial_scores

        if len(qipai_list) != 4:
            msg = "The length of `qipai_list` must be equal to 4."
            raise ValueError(msg)
        for i in range(len(qipai_list)):
            if i == self._ju and len(qipai_list[i]) != 14:
                msg = (
                    "The length of `qipai_list` for zhuangjia"
                    " must be equal to 14."
                )
                raise ValueError(msg)
            if i != self._ju and len(qipai_list[i]) != 13:
                msg = (
                    "The length of `qipai_list` for sanjia must"
                    " be equal to 13."
                )
                raise ValueError(msg)
        self._qipai_list = qipai_list

        self._paishan = paishan

        self._paishan_code = paishan_code

        self._dora = dora

        self._tingpai_list = tingpai_list

        self._option_presence = option_presence

        self._left_tile_count = left_tile_count

        self._turns = []

    @property
    def chang(self) -> str:
        return self._chang

    @property
    def ju(self) -> int:
        return self._ju

    @property
    def ben(self) -> int:
        return self._ben

    def append_turn(self, turn: Turn) -> None:
        self._turns.append(turn)

    def to_json(self) -> object:
        qipai_list = [
            [tile.to_json() for tile in qipai] for qipai in self._qipai_list
        ]

        tingpai_list = [
            {
                "seat": seat.to_json(),
                "tingpai": tingpai.to_json(),
            }
            for seat, tingpai in self._tingpai_list
        ]

        return {
            "chang": self._chang,
            "ju": self._ju,
            "ben": self._ben,
            "lizhibang": self._lizhibang,
            "initial_scores": self._initial_scores,
            "qipai_list": qipai_list,
            "paishan": [tile.to_json() for tile in self._paishan],
            "paishan_code": self._paishan_code,
            "dora": self._dora.to_json(),
            "tingpai_list": tingpai_list,
            "option_presence": self._option_presence.to_json(),
            "left_tile_count": self._left_tile_count,
            "turns": [t.to_json() for t in self._turns],
        }


class GameRecord:
    def __init__(
        self,
        *,
        placeholder: GameRecordPlaceholder,
        end_time: datetime.datetime,
        mode: str,
        account_list: list[Account],
    ) -> None:
        self._uuid = (placeholder.uuid,)

        self._start_time = placeholder.start_time

        self._end_time = end_time

        if mode not in [
            "段位戦・銅の間・四人東風戦",
            "段位戦・銅の間・四人半荘戦",
            "段位戦・銀の間・四人東風戦",
            "段位戦・銀の間・四人半荘戦",
            "段位戦・金の間・四人東風戦",
            "段位戦・金の間・四人半荘戦",
            "段位戦・玉の間・四人東風戦",
            "段位戦・玉の間・四人半荘戦",
            "段位戦・王座の間・四人東風戦",
            "段位戦・王座の間・四人半荘戦",
            "段位戦・銅の間・三人東風戦",
            "段位戦・銅の間・三人半荘戦",
            "段位戦・銀の間・三人東風戦",
            "段位戦・銀の間・三人半荘戦",
            "段位戦・金の間・三人東風戦",
            "段位戦・金の間・三人半荘戦",
            "段位戦・玉の間・三人東風戦",
            "段位戦・玉の間・三人半荘戦",
            "段位戦・王座の間・三人東風戦",
            "段位戦・王座の間・三人半荘戦",
        ]:
            msg = f"{mode}: An invalid value for `mode`."
            raise ValueError(msg)
        self._mode = mode

        if len(account_list) != 4:
            msg = "The length of `account_list` must be equal to 4."
            raise ValueError(msg)
        self._account_list = account_list

        self._round_list = []

    @property
    def uuid(self) -> str:
        return self._uuid

    @property
    def start_time(self) -> datetime.datetime:
        return self._start_time

    def append_game_round(self, new_round: GameRound) -> None:
        self._round_list.append(new_round)

    def to_json(self) -> object:
        return {
            "uuid": self._uuid,
            "mode": self._mode,
            "start_time": int(self._start_time.timestamp()),
            "end_time": int(self._end_time.timestamp()),
            "account_list": [
                account.to_json() for account in self._account_list
            ],
            "round_list": [r.to_json() for r in self._round_list],
        }
