import requests
import aiohttp
from concurrent.futures import as_completed

from pifx import util


class LIFXWebAPIClient:
    def __init__(self, api_key, http_endpoint=None, is_async=False):
        if http_endpoint == None:
            self.http_base = "https://api.lifx.com/v1/"
        else:
            self.http_base = http_endpoint

        self.api_key = api_key
        self.headers = util.generate_auth_header(self.api_key)
        self.is_async = is_async
        if self.is_async:
            # Configure event loop for up to 10 concurrent requests to avoid rate-limiting by Lifx.
            self._s = aiohttp.ClientSession()
        else:
            self._s = requests.Session()

    def _full_http_endpoint(self, suffix):
        return self.http_base + suffix

    async def perform_request(
        self,
        method,
        endpoint,
        endpoint_args=[],
        argument_tuples=None,
        json_body=False,
        parse_data=True
    ):
        http_endpoint = self._full_http_endpoint(
            endpoint.format(*endpoint_args)
        )

        data = None
        if argument_tuples is not None:
            data = util.arg_tup_to_dict(argument_tuples)

        request_parameters = {
            "method": method,
            "url": http_endpoint,
            "headers": self.headers
        }

        if json_body:
            request_parameters["json"] = json_body
        else:
            request_parameters["data"] = data

        if self.is_async:
            async with self._s.request(**request_parameters) as response:
                result = response
                result_text = await response.text()
                result_status = response.status
        else:
            # Call request routine
            result = self._s.request(**request_parameters)
            result_text = result.text()
            result_status = result.status_code

        parsed_response = util.parse_response(result_text)

        util.handle_error(result_status)

        if parse_data:
            return util.parse_data(parsed_response)

        return parsed_response

