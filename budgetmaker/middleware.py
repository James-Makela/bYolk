import re


class DemoObfuscationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not request.session.get("privacy_mode", False):
            return response

        if response.status_code == 200 and "text/html" in response.get(
            "Content-Type", ""
        ):

            content = response.content.decode("utf-8", errors="ignore")

            def mask_currency(match):
                amount = match.group(1)
                masked_amount = re.sub(r"\d", "x", amount)
                return f"${masked_amount}"

            obscured_content = re.sub(r"\$-*([\d,.]+)", mask_currency, content)

            response.content = obscured_content.encode("utf-8")

            if response.has_header("Content-Length"):
                response["Content-Length"] = str(len(response.content))

        return response
