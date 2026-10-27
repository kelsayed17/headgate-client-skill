# headgate-verify-config: {"write_name_fragments": ["redeem"]}
# A project's own fragment, from [tool.headgate-verify] write-name-fragments.
class Vault(AsyncBaseClient):
    async def redeem_voucher(self, code: str) -> Receipt:
        return await self.post(t"vouchers/{code}/redeem", expect=RECEIPT)
