from typing import Dict, Any


class MemoryStorageLike:
    def __init__(self):
        self._states: Dict[int, str | None] = {}
        self._data: Dict[int, Dict[str, Any]] = {}

    async def get_state(self, user_id: int):
        return self._states.get(user_id)

    async def set_state(self, user_id: int, state: str | None):
        self._states[user_id] = state

    async def get_data(self, user_id: int):
        return self._data.get(user_id, {})

    async def set_data(self, user_id: int, data: Dict[str, Any]):
        self._data[user_id] = data


class FSMContextLike:
    def __init__(self, storage: "MemoryStorageLike", user_id: int):
        self._storage = storage
        self._user_id = user_id

    async def set_state(self, state: str | None):
        await self._storage.set_state(self._user_id, state)

    async def clear(self):
        await self._storage.set_state(self._user_id, None)
        await self._storage.set_data(self._user_id, {})

    async def get_state(self) -> str | None:
        return await self._storage.get_state(self._user_id)

    async def get_data(self) -> Dict[str, Any]:
        return await self._storage.get_data(self._user_id)

    async def update_data(self, **kwargs):
        data = await self._storage.get_data(self._user_id)
        data.update(kwargs)
        await self._storage.set_data(self._user_id, data)
