"""Just playing the Docker ReST API"""

import json
import requests


class DockerSandbox:
    def __init__(self, repo, tag) -> None:
        self._repo = repo
        self._tag = tag
        res = requests.get(
            "https://auth.docker.io/token",
            params={
                "service": "registry.docker.io",
                "scope": f"repository:{repo}:pull",
            },
            timeout=10,
        )
        if res.status_code != requests.codes.ok:
            raise RuntimeError(f"Could not get auth token: {res.reason}")
        self._auth_token = res.json()["token"]

    def _fetch_blob(self, digest):
        req_headers = {
            "Authorization": f"Bearer {self._auth_token}",
            "Accept": "application/vnd.oci.image.index.v1+json"
            }
        url = f"https://registry-1.docker.io/v2/{self._repo}/blobs/{digest}"
        print(f"\nGET {url}")
        res = requests.get(url, headers=req_headers, timeout=10)
        try:
            print(json.dumps(res.json(), indent=2))
        except json.JSONDecodeError:
            print(res)

    def fetch_annotations(self):
        req_headers = {
            "Authorization": f"Bearer {self._auth_token}",
            "Accept": "application/vnd.oci.image.manifest.v1+json"
        }
        url = f"https://registry-1.docker.io/v2/{self._repo}/manifests/{self._tag}"
        print(f"GET {url}\nHeaders:\n{json.dumps({k:v for k,v in req_headers.items() if k != 'Authorization'}, indent=2)}")
        res = requests.get(url, headers=req_headers, timeout=10)
        manifests = res.json()
        print(f"\nRESPONSE\nHeaders:{json.dumps(dict(res.headers), indent=2)}\nBody:\n{json.dumps(manifests, indent=2)}")
        if res.status_code != requests.codes.ok:
            raise RuntimeError(f"Could not fetch manifests: {res.reason}")
        self._fetch_blob(res.headers["docker-content-digest"])
        for manifest in manifests["manifests"]:
            self._fetch_blob(manifest["digest"])
            if "annotations" in manifest:
                self._fetch_blob(manifest["annotations"]["vnd.docker.reference.digest"])


if __name__ == "__main__":
    sandbox = DockerSandbox("mbulut/annotated", "latest")
    sandbox.fetch_annotations()
