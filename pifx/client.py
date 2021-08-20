import requests
from requests_futures.sessions import FuturesSession
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
            self._s = FuturesSession(max_workers=10)
        else:
            self._s = requests.Session()

    def _full_http_endpoint(self, suffix):
        return self.http_base + suffix

    def perform_request(
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
            # Attach correct hook for async parsing of response
            if parse_data:
                request_parameters["hooks"] = {"response": util.process_response_with_results}
            else:
                request_parameters["hooks"] = {"response": util.process_response}

        # Call request routine/coroutine
        result = self._s.request(**request_parameters)

        if self.is_async:
            return result

        parsed_response = util.parse_response(result)

        util.handle_error(result)

        if parse_data:
            return util.parse_data(parsed_response)

        return parsed_response

