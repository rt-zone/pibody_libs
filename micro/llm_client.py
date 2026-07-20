import ujson
import urequests


class LLMClientError(Exception):
    pass


class LLMClient:
    def __init__(self, api_key, url, model, system_prompt="",
                fallback_no_choices="print('No choices')",
                fallback_error="print('LLM Error')"):
        if not api_key:
            raise ValueError("api_key is required")
        if not url:
            raise ValueError("url is required")
        self.api_key = api_key
        self.url = url
        self.model = model
        self.system_prompt = system_prompt
        self.fallback_no_choices = fallback_no_choices
        self.fallback_error = fallback_error

    def ask(self, prompt_text):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.api_key,
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt_text},
            ],
        }

        res = None
        try:
            res = urequests.post(
                self.url,
                data=ujson.dumps(payload).encode("utf-8"),
                headers=headers,
            )
            result = res.json()
            if "choices" in result:
                return result["choices"][0]["message"]["content"].strip().replace("`", "")
            return self.fallback_no_choices
        except Exception as e:
            print("LLM error:", e)
            return self.fallback_error
        finally:
            if res is not None:
                try:
                    res.close()
                except Exception:
                    pass