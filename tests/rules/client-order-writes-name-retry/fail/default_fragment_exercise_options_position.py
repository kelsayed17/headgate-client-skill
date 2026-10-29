class Broker(AsyncBaseClient):
    async def exercise_options_position(self, body: Exercise) -> Order:
        return await self.post("options/exercise", body=EXERCISE(body), expect=ORDER)
